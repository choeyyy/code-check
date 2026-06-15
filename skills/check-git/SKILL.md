---
name: check-git
description: "Quick code review against git branch diff. Same 3 reviewers as /check but scoped to branch changes vs base."
disable-model-invocation: true
---

# /check-git — Quick Code Review (Git Branch Mode)

You are the orchestrator for a multi-agent code review in git branch mode. The scope is the diff between the current branch and its base branch. Launch 3 parallel reviewers, collect findings, assign consensus confidence, persist results, and report.

Follow the same 9-step flow as `/check`, with the git-mode overrides documented below. Do not skip steps. Do not modify files under review.

---

## Step 1: Determine Scope (Git Override)

This command reviews changes on the current branch relative to a base branch.

**1a. Verify git repo:**
Run `git rev-parse --is-inside-work-tree`. If this fails, stop immediately and tell the user: "Not a git repository. Use `/check` for local file review."

**1b. Determine base branch:**

Priority chain:
1. **User specified a base branch** in their message (e.g., "check against develop", "base: release/2.0") → use that branch name.
2. **Auto-detect** → try in order:
   - `git rev-parse --verify main 2>/dev/null` — if it exists, use `main`
   - `git rev-parse --verify master 2>/dev/null` — if it exists, use `master`
   - `git rev-parse --abbrev-ref @{upstream} 2>/dev/null` — if tracking branch exists, use it
3. **None found** → ask the user: "Could not auto-detect base branch. Which branch should I diff against?"

**1c. Compute changed files:**
Run `git diff --name-only <base>...HEAD` to get the list of changed files. Exclude deleted files (verify each path exists on disk).

If the diff is empty (no changes vs base), tell the user: "No changes detected between current branch and `<base>`. Nothing to review." and stop.

**1d. Compute diff hunks:**
Run `git diff <base>...HEAD` to get the full diff. Store this — reviewers receive both the diff and the full file contents.

> **Note:** In git mode, openspec is used only for change-context labeling (Step 1.5), not for scope determination. Check if an `openspec/` directory exists in the project root. If it does, run `openspec status --json` and note the active change name if one is found — you will use it in Step 1.5.

## Step 1.5: Identify Change Context

Determine a semantic label and a Source line for the current work. The **label** is used for file naming; the **source_line** is written into the change document.

**Priority chain (produces both outputs):**

1. **Openspec** → If an openspec active change was detected in Step 1, use its change name.
   - `label` = change name (e.g., `add-auth`)
   - `source_line` = `openspec: {change-name} (openspec/changes/{change-name}/proposal.md)`

2. **Git branch** → Run `git branch --show-current`. If the branch is not `main` or `master`, strip common prefixes (`feat/`, `fix/`, `bugfix/`, `feature/`, `hotfix/`) and use the remainder.
   - `label` = stripped branch name (e.g., `parser-refactor`)
   - `source_line` = `git: {full-branch-name} (branch)`

3. **User message** → Extract a short keyword or phrase from the user's message describing their work.
   - `label` = extracted keyword (e.g., `check-api-handler`)
   - `source_line` = `user: {short phrase from message}`

4. **Fallback** → No context detected.
   - `label` = `未分类`
   - `source_line` = `unclassified: (no context detected)`

**Sanitize the label for filenames:** replace spaces with hyphens, remove characters not matching `[a-zA-Z0-9\u4e00-\u9fff\-_]`, truncate to 30 characters.

Store both `label` (sanitized) and `source_line` — you will use them in the persistence step.

## Step 2: Collect Context

Read all of the following. Failures on optional files are fine — skip them silently.

**Required — files under review:**
Read every changed file in the scope list (full content). If a file is binary or unreadable, drop it from scope and note it in the final report.

**Required — diff hunks:**
You already have the diff from Step 1d. This goes to reviewers alongside the full files.

**Optional — project review config:**
Look for `REVIEW.md` in the project root. If it exists, read it.

**Required — plugin references (paths relative to this plugin's root):**
- `references/rubric.md`
- `references/false-positives.md`
- `references/output-format.md`

## Step 3: REVIEW.md Auto-Generation (First Run Only)

Identical to `/check`. If `REVIEW.md` does NOT exist in the project root AND the user did NOT say "不生成 REVIEW.md" or "no review.md":

**3a. Scan project files** (read whichever exist, skip missing ones silently):

| Source | What to extract |
|--------|-----------------|
| `README.md` | Project name (first heading), description (first paragraph), technology/framework mentions |
| `package.json` | `name`, `description`, notable frameworks from `dependencies` and `devDependencies` |
| `go.mod` | Module path, major dependencies from `require` block |
| `Cargo.toml` | `[package]` name, notable entries from `[dependencies]` |
| `pyproject.toml` | `[project]` name, description, major entries from `dependencies` |
| `ARCHITECTURE.md` (project root, then `docs/ARCHITECTURE.md`) | Read up to 200 lines — architecture summary |
| User-specified paths in message | If the user's message references doc files, read and incorporate |

**3b. Create `REVIEW.md`** in the project root with structured `## Project Context` (bullet format: Project, Language, Framework, Architecture, Key dependencies), plus Review Focus Areas, Custom Rules, Model Overrides, Configuration sections.

**3c.** Tell the user: "Generated `REVIEW.md` with project defaults. Edit it to customize review behavior."

## Step 4: Check for Previous Session

Identical to `/check`. If `.checks/session.md` exists:

1. Read it. Parse the issue tracker table.
2. For each issue with status `open`:
   - Read the referenced file.
   - Search for the recorded **snippet** (exact substring match).
   - Snippet not found → `fixed`. Snippet found → `open`. Inconclusive → `verify`.
3. Hold these status updates for Step 8.

## Step 5: Launch 3 Reviewers in Parallel

Read these three agent prompt files (paths relative to plugin root):
- `agents/bug-reviewer.md`
- `agents/standards-reviewer.md`
- `agents/quality-reviewer.md`

For each agent file, construct the sub-agent prompt by combining:
1. The agent file contents (the reviewer's role and instructions)
2. The **diff hunks** (so the reviewer knows exactly what changed)
3. The **full file contents** of changed files (so the reviewer has surrounding context)
4. The rubric (`references/rubric.md` contents)
5. The false-positives list (`references/false-positives.md` contents)
6. The output format spec (`references/output-format.md` contents)
7. The project `REVIEW.md` contents (if it exists)
8. **Known patterns** (conditional — see below)

**Known Patterns (conditional):**
Read `.checks/changes/{label}.md` (using the label from Step 1.5). If the file exists, extract the content under the `## Patterns` heading. If that content is non-empty (not just whitespace or blank), store it as `patterns_text`. If the file doesn't exist or `## Patterns` is empty, set `patterns_text` to empty (omit from prompt).

Assemble the prompt for each reviewer like this:

```
[Contents of the agent .md file]

---

## Review Context

### Mode
Git branch review. Base: `<base branch>`. Focus findings on the changed code.

### Diff
```diff
<full git diff output>
```

### Full File Contents (for surrounding context)

[For each changed file:]
#### `<file path>`
```
<full file content>
```

### Review Standards

<contents of rubric.md>

### False-Positive Patterns — Do NOT Report These

<contents of false-positives.md>

### Output Format — Follow Exactly

<contents of output-format.md>

### Project-Specific Configuration

<contents of REVIEW.md, or "No project REVIEW.md — use built-in rubric only.">

[IF patterns_text is non-empty, include this section:]
### Known Patterns (from prior reviews of this change)

<patterns_text>

Use these patterns to:
- Flag if a known pattern is still present (recurring issue)
- Note if a previously identified pattern has been resolved
- Identify new patterns not yet documented
[END conditional section — omit entirely if patterns_text is empty]
```

**Launch all three in a single message** using the Task tool. This is critical — they MUST be in the same response to run in parallel:

- **Bug Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Bug Reviewer (git)"`, `prompt: <constructed prompt>`
- **Standards Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Standards Reviewer (git)"`, `prompt: <constructed prompt>`
- **Quality Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Quality Reviewer (git)"`, `prompt: <constructed prompt>`

After launching, tell the user: "Launched Bug Reviewer, Standards Reviewer, Quality Reviewer (reviewing `<base>`...HEAD) — waiting for results..."

## Step 6: Collect and Deduplicate

Identical to `/check`:

As each sub-agent completes, report: "[Reviewer Name] complete (N findings)".

After all three return:

1. **Parse findings** from each reviewer's output.

2. **Deduplicate**: same file + overlapping lines + similar description → merge, noting all source reviewers.

3. **Assign consensus confidence**:
   - **high** — 2+ reviewers flagged the same issue
   - **medium** — 1 reviewer, severity is `critical` or `warning`
   - **low** — 1 reviewer, severity is `nit`

4. **Annotate**: all findings get `source_mode: git`.

## Step 7: Handle Failures

Identical to `/check`:

- "No findings." = valid zero-findings result.
- Empty output, error, or unparseable output → skip that reviewer's findings, add warning: "[Reviewer Name] did not return results — coverage incomplete."
- Never block on a failed reviewer.

## Step 8: Persist to .checks/ (Unless Skipped)

Check if the user said "不收录", "不记录", "skip", or "once". If so, skip this step.

Otherwise:

**8a–8b. Initialize and determine run number**: identical to `/check` (including `.checks/changes/` directory and both old/new filename pattern scanning).

**8c. Write history file** (`.checks/history/check{NNN}-{label}.md`, e.g. `check001-重构解析器.md`):

```markdown
# Check Run NNN

**Date**: <current date/time>
**Scope**: git diff <base>...HEAD
**Mode**: git
**Base Branch**: <base branch name>
**Changed Files**: <comma-separated file list>
**Reviewers**: Bug (N), Standards (N), Quality (N)

## Findings

[All deduplicated findings in output-format.md format, with added Confidence, Source, and source_mode: git fields]
```

**8d. Update session.md**:

If `.checks/session.md` does not exist, create it with the standard template (see `/check` Step 8d).

Assign issue IDs: `C`-prefixed, zero-padded, continuing from last ID.

For each new finding: add a row with status `open`, source `git`, and the current run number.

Update previously open issues from Step 4 (same logic as `/check`).

**8e. Stage auto-progression** (git-mode specific):
If the current stage in `session.md` is `developing`, update it to `pre-commit`. This reflects that the user has moved from local development to reviewing branch-level changes.

**8f. Update change aggregate** (`.checks/changes/{label}.md`):

Create `.checks/changes/` directory if it doesn't exist.

Compute the `resolved_count`: count issues from Step 4 whose status changed from `open` to `fixed` AND whose file is in the current scope. If no session existed (first run), `resolved_count` = 0.

If `.checks/changes/{label}.md` already exists:
- Read it
- Append a new row to the `## Review History` table: `| check{NNN} | {date} | {finding_count} | {critical_count} | {resolved_count} |`
- Merge any new file paths into the `## Files` list (deduplicate, preserve order)
- Do NOT modify `## Source` or `## Patterns`

If it does not exist, create it with this template:

```markdown
# Change: {label}

## Source
{source_line}

## Files
- {list of files from this run's scope, one per line}

## Review History

| Run | Date | Findings | Critical | Resolved |
|-----|------|----------|----------|----------|
| check{NNN} | {date} | {count} | {critical_count} | 0 |

## Patterns
```

## Step 9: Format Final Report

```
## Code Check Results (Git Mode)

**Base**: `<base branch>` → HEAD
**Changed Files**: <file list>
**Change**: {label}
**Reviewers**: Bug (N findings), Standards (N findings), Quality (N findings)
[If any reviewer failed: "⚠ [Reviewer Name] did not return results — coverage incomplete."]

### Critical
[Findings with severity: critical, ordered by confidence (high → low). If none: "None."]

### Warning
[Findings with severity: warning, ordered by confidence. If none: "None."]

### Nit
[Findings with severity: nit, ordered by confidence. If none: "None."]
```

Each finding displays:
- **File**: path — **Line**: number/range
- **Snippet**: `<code>`
- Description
- **Confidence**: high/medium/low — **Source**: [reviewer names]

Then:

```
### Session Update
[If persisted: "Run NNN saved. N new issues added, N issues resolved, N issues pending verification. Stage: <stage>."]
[If stage changed: "Stage progressed: developing → pre-commit."]
[If skipped: "Results not persisted (one-time run)."]

### Next Steps
[Actionable recommendations. Examples:]
[- "Fix the N critical issues above, then re-run `/check-git` to verify."]
[- "No critical issues — consider `/check-full-git` for a thorough pre-merge review."]
[- "Clean branch. Ready to merge."]
```

If there are zero total findings: output "**No findings.** Branch changes look good." and skip the severity sections.
