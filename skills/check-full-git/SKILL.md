---
name: check-full-git
description: "Thorough git branch review with 5 parallel reviewers, confidence scoring, and threshold filtering. Use for check-full-git, full git review, full branch review, or thorough branch check."
disable-model-invocation: true
---

# /check-full-git — Thorough Code Review (Git Branch Mode)

You are the orchestrator for a thorough multi-agent code review in git branch mode. The scope is the diff between the current branch and its base branch. Launch 5 parallel reviewers, score each finding's confidence, filter by threshold, persist results, and report.

Follow the same 11-step flow as `/check-full`, with the git-mode overrides documented below. Do not skip steps. Do not modify files under review.

---

## Step 1: Determine Scope (Git Override)

This command reviews changes on the current branch relative to a base branch.

**1a. Verify git repo:**
Run `git rev-parse --is-inside-work-tree`. If this fails, stop immediately and tell the user: "Not a git repository. Use `/check-full` for local file review."

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

Note: In git mode, openspec is used only for change-context labeling (Step 1.5), not for scope determination.

## Step 1.5: Identify Change Context

Determine a semantic label and a Source line for the current work. The **label** is used for file naming; the **source_line** is written into the change document.

**Priority chain (produces both outputs):**

1. **Openspec** → Check if an `openspec/` directory exists in the project root. If it does, run `openspec status --json`. If the output shows an active change, use its change name. If `openspec/` doesn't exist or the command fails, fall through silently.
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

Read all of the following. Missing optional items are not errors — skip and continue.

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

**Required — git context (for History Reviewer):**
For each changed file, collect:
- `git blame <file>` — line-by-line authorship and recency
- `git log --oneline -20 -- <file>` — recent commit history for the file
- `git log --oneline <base>...HEAD -- <file>` — commits on this branch that touched the file

If any git command fails for a specific file, skip that file's git context and note it.

## Step 3: REVIEW.md Auto-Generation (First Run Only)

Identical to `/check-full`. If `REVIEW.md` does NOT exist in the project root AND the user did NOT say "不生成 REVIEW.md" or "no REVIEW.md":

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

## Step 4: Check Previous Session

Identical to `/check-full`. If `.checks/session.md` exists:

1. Read it. Parse the issue tracker table.
2. For each issue with status `open` or `verify`:
   - Read the referenced file.
   - Search for the recorded **snippet** (exact substring match).
   - Snippet not found → `fixed`. Snippet found → keep current status. Inconclusive → `verify`.
3. Hold these status updates for Step 10.

## Step 5: Launch 5 Reviewers in Parallel

Read the agent prompt files and construct each reviewer's full prompt by combining the agent instructions with the collected context. Then launch ALL FIVE reviewers in a single message using the Task tool.

### Prompt Construction

For each reviewer, build the prompt by combining:
1. The agent file contents (the reviewer's role and instructions)
2. The **diff hunks** (so the reviewer knows exactly what changed)
3. The **full file contents** of changed files (so the reviewer has surrounding context)
4. The rubric (`references/rubric.md` contents)
5. The false-positives list (`references/false-positives.md` contents)
6. The output format spec (`references/output-format.md` contents)
7. The project `REVIEW.md` contents (if it exists)
8. Additional context per reviewer (see specifications below)
9. **Known patterns** (conditional — see below)

**Known Patterns (conditional):**
Read `.checks/changes/{label}.md` (using the label from Step 1.5). If the file exists, extract the content under the `## Patterns` heading. If that content is non-empty (not just whitespace or blank), store it as `patterns_text`. If the file doesn't exist or `## Patterns` is empty, set `patterns_text` to empty (omit from prompt).

Assemble the prompt like this:

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

[Additional context sections per reviewer — see below]

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

### Reviewer Specifications

**1. Bug Reviewer** — `agents/bug-reviewer.md`
No additional context sections beyond the base template.

**2. Standards Reviewer** — `agents/standards-reviewer.md`
No additional context sections beyond the base template.

**3. Quality Reviewer** — `agents/quality-reviewer.md`
No additional context sections beyond the base template.

**4. History Reviewer** — `agents/history-reviewer.md`
Add these sections to the prompt before "### Review Standards":
```
### Git Blame

[For each file:]
#### `<file path>`
<git blame output>

### Recent Commit History

[For each file:]
#### `<file path>`
<git log --oneline -20 output>

### Branch Commits

[For each file:]
#### `<file path>`
<git log --oneline <base>...HEAD output>
```
The History Reviewer in git mode gets richer context than in local mode — it sees branch-specific commits in addition to overall file history.

**5. Comments Reviewer** — `agents/comments-reviewer.md`
No additional context sections beyond the base template.

**Launch all five in a single message** using the Task tool. This is critical — they MUST be in the same response to run in parallel:

- **Bug Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Bug Reviewer (git)"`, `prompt: <constructed prompt>`
- **Standards Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Standards Reviewer (git)"`, `prompt: <constructed prompt>`
- **Quality Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Quality Reviewer (git)"`, `prompt: <constructed prompt>`
- **History Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "History Reviewer (git)"`, `prompt: <constructed prompt>`
- **Comments Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `model: "claude-4.5-haiku-thinking"`, `description: "Comments Reviewer (git)"`, `prompt: <constructed prompt>`

After launching, tell the user: "Launched Bug Reviewer, Standards Reviewer, Quality Reviewer, History Reviewer, Comments Reviewer (reviewing `<base>`...HEAD) — waiting for results..."

## Step 6: Collect Findings

Track reviewer completion order (1st, 2nd, 3rd...). As each reviewer completes, report progress including its position:

"[Reviewer Name] complete (N findings) — finished #X. Still waiting for: [remaining reviewer names]..."

When the last reviewer completes, mark it as the bottleneck:

"[Reviewer Name] complete (N findings) — finished last (bottleneck). All reviewers done."

After all reviewers finish:
1. Parse each reviewer's output for findings matching the output-format template.
2. Deduplicate: if two or more reviewers flag the same file + overlapping line range + substantially similar description, merge into one finding and note all source reviewers.
3. Preserve all unique findings across reviewers.
4. Annotate every finding with `source_mode: git` to distinguish from local-mode findings in the session history.

## Step 7: Handle Failures

If any reviewer fails, times out, or returns unparseable output:
- Skip its findings.
- Add a warning to the final report: "[Reviewer Name] did not return results — this review has incomplete coverage in that dimension."
- Do NOT block the pipeline. Continue with the findings you have.
- Suggest the user re-run if the failed reviewer covers a critical dimension.

## Step 8: Confidence Scoring

After all reviewers complete and findings are collected, determine the scoring strategy.

### Strategy Selection

Check the user's message for explicit overrides first:
- "逐条评分" or "per-issue scoring" → force **per-issue** mode
- "批量评分" or "batch scoring" → force **batch** mode

If no explicit override, use adaptive strategy:
- ≤5 findings AND at least one has severity `critical` → **per-issue** mode
- \>5 findings OR no findings have severity `critical` → **batch** mode

### Scoring Rubric

Include this rubric verbatim in every confidence-judge prompt:

```
Score each finding from 0-100 using this scale:

- 0: Not confident at all. False positive, pre-existing issue.
- 25: Somewhat confident. Might be real. Stylistic without explicit REVIEW.md backing.
- 50: Moderately confident. Verified real but low-impact or nitpick.
- 75: Highly confident. Double-checked, very likely real, will be hit in practice. Directly impacts functionality.
- 100: Absolutely certain. Definitely real, frequent in practice. Evidence directly confirms.

Return your score as an integer 0-100. You may use any value, not just the anchors above.
```

### Per-Issue Mode

For each finding, launch a separate confidence-judge sub-agent:
- Agent file: `agents/confidence-judge.md`
- Task tool config: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`
- `model: "claude-4.5-haiku-thinking"`
- Prompt includes: the single finding (full details), the file content where the finding was identified, the branch diff for that file, REVIEW.md contents, false-positives list, and the scoring rubric above

Launch all judge sub-agents in a single message for parallelism.

### Batch Mode

Launch ONE confidence-judge sub-agent:
- Agent file: `agents/confidence-judge.md`
- Task tool config: `subagent_type: "generalPurpose"`, `readonly: true`
- `model: "claude-4.5-haiku-thinking"`
- Prompt includes: all findings together, all file contents, branch diff, REVIEW.md, false-positives list, and the scoring rubric above

Report: "Scoring N findings ([per-issue/batch] mode)..."

### Parse Scores

Extract the integer score (0-100) for each finding from the judge output. If a score cannot be parsed for a finding, default to 50.

## Step 9: Threshold Filtering

Determine the confidence threshold:
1. Check REVIEW.md for a `threshold:` line (e.g. `threshold: 60`). Use that value if present.
2. Check the user's message for a threshold override (e.g. "threshold 70", "阈值 90").
3. Default: **80**.

Partition findings:
- **Above threshold**: score ≥ threshold → included in the main report sections
- **Below threshold**: score < threshold → listed in the "Below Threshold" section

## Step 10: Persist to .checks/ (Unless Skipped)

Check if the user said "不收录", "不记录", "skip", or "once". If so, skip this entire step.

Otherwise:

**10a–10b. Initialize and determine run number**: identical to `/check-full`.

**10c. Write history file** (`.checks/history/check{NNN}-{label}.md`):

```markdown
# Check Run NNN

**Date**: <current date/time>
**Change**: {label}
**Scope**: git diff <base>...HEAD
**Mode**: git (full)
**Base Branch**: <base branch name>
**Changed Files**: <comma-separated file list>
**Reviewers**: Bug (N), Standards (N), Quality (N), History (N), Comments (N)
**Scoring**: <per-issue/batch>, threshold: <value>

## Findings

[All deduplicated findings in output-format.md format, with added Score, Source, and source_mode: git fields]
```

**10d. Update session.md**:

If `.checks/session.md` does not exist, create it with the standard template (see `/check` Step 8d).

Assign issue IDs: `C`-prefixed, zero-padded, continuing from last ID.

For each new finding: add a row with status `open`, source `git`, score column, and the current run number.

Update previously open issues from Step 4 (same logic as `/check-full`).

**10e. Stage auto-progression** (git-mode specific):
Set the stage to **"final-review"** (最终审查). `/check-full-git` always progresses the session to the final review stage, regardless of prior stage.

**10f. Update change aggregate** (`.checks/changes/{label}.md`):

Create `.checks/changes/` directory if it doesn't exist.

Compute the `resolved_count`: count issues from Step 4 whose status changed to `fixed` (from `open` or `verify`) AND whose file is in the current scope. If no session existed (first run), `resolved_count` = 0.

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

## Step 11: Format Final Report

Present the results in this structure:

```
## Code Check (Full Git) Results

**Change**: {label}
**Branch**: [current] vs [base]
**Scope**: [N files changed]
**Reviewers**: Bug (N), Standards (N), Quality (N), History (N), Comments (N)
**Scoring**: [per-issue/batch], threshold: [value]
[Any failure warnings for reviewers that didn't return results]

### Critical (score ≥ threshold)
[Findings with severity critical, sorted by score descending.
Each shows: File:Line | Snippet | Description | Score | Source reviewer(s)]

### Warning (score ≥ threshold)
[Findings with severity warning, same format]

### Nit (score ≥ threshold)
[Findings with severity nit, same format]

### Below Threshold
[Findings that scored below the threshold, in brief format:
File:Line | Severity | Score | One-line description | Source reviewer(s)]

### Performance
[Table showing each reviewer's completion order and finding count:

| Reviewer | Completion | Findings |
|----------|-----------|----------|
| {name}   | #1        | N        |
| {name}   | #2        | N        |
| ...      | ...       | ...      |
| {name}   | #X (bottleneck) | N  |

If a reviewer was skipped, show: | {name} | skipped ({reason}) | — |
]

### Session Update
[New issues added, issues resolved since last check, current stage: 最终审查]

### Next Steps
[Recommendations: address critical findings before merge, consider warnings, etc.]
```

If there are zero findings above threshold, report "No findings above threshold (N findings scored below threshold and are listed in Below Threshold)." or "No findings." if there are none at all.
