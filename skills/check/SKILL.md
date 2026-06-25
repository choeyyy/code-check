---
name: check
description: "Quick code review with 3 parallel reviewers and consensus-based confidence scoring. Use for daily development checks on local files."
disable-model-invocation: true
---

# /check — Quick Code Review

You are the orchestrator for a multi-agent code review. Launch 3 parallel reviewers, collect findings, assign consensus confidence, persist results, and report.

Follow these steps in order. Do not skip steps. Do not modify files under review.

---

## Step 0: Check for `-update fixed`

Check whether the user's message contains `-update fixed` (case-insensitive).

If **not found** → skip to Step 1.

If **found** → execute the lightweight sync flow below, then **STOP** (do not continue to Step 1):

1. **Read session** — Read `.checks/session.md` in the project root.
   - If the file does not exist → output "没有审查会话。" → **STOP**.

2. **Extract open issues** — Parse the `## Issue Tracker` table. Collect every row whose Status column is `open`.
   - If no open issues → output "没有待同步的 issue。" → **STOP**.

3. **Snippet-check each open issue** — For each open issue:
   - Read the file referenced in the **File** column.
   - Search for the **Snippet** value as an exact substring in the file content.
   - Snippet **not found** (or file does not exist / is unreadable) → set new status to `verify`.
   - Snippet **found** → keep status as `open`.

4. **Write back** — Update the Status column of each affected row in `.checks/session.md` with the new status.

5. **Output summary** — For each open issue processed, print one line:
   - Status changed: `{ID}: open → verify (snippet 已不存在)`
   - Status unchanged: `{ID}: 仍 open`

   End with: "运行 /check 确认修复。"

6. **STOP** — Do not proceed to Step 1 or any subsequent steps.

---

## Step 1: Determine Scope

Determine which files to review using this priority chain:

1. **User specified files/directories** in their message → use those. Resolve globs/directories to individual files.
2. **Openspec active change** → Check if an `openspec/` directory exists in the project root. If it does, run `openspec status --json`. If the output shows an active change with in-progress tasks, read the tasks file and extract any file paths mentioned in the current in-progress task description. If file paths are found, use them as the review scope. If `openspec/` doesn't exist, the command fails, or no file paths are extractable, fall through silently to the next priority.
3. **Git dirty files** → run `git status --porcelain` in the project root. If it succeeds and returns output, extract the file paths (both staged and unstaged changes — lines starting with `M`, `A`, `MM`, `AM`, `??`, etc.). Exclude deleted files (lines starting with `D` or ` D`).
4. **Neither** → ask the user: "No files specified and no uncommitted changes detected. Which files or directories should I review?"

Stop and wait for user input only in case 4.

Store the resolved file list — you will pass it to every reviewer.

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
Read every file in the scope list (full content). If a file is binary or unreadable, drop it from scope and note it in the final report.

**Optional — project review config:**
Look for `REVIEW.md` in the project root. If it exists, read it. Its contents override or supplement the built-in rubric.

**Required — plugin references (paths relative to this plugin's root):**
- `references/rubric.md`
- `references/false-positives.md`
- `references/output-format.md`

## Step 3: REVIEW.md Auto-Generation (First Run Only)

If `REVIEW.md` does NOT exist in the project root AND the user did NOT say "不生成 REVIEW.md" or "no review.md":

**3a. Scan project files** (read whichever exist, skip missing ones silently):

| Source | What to extract |
|--------|-----------------|
| `README.md` | Project name (first heading), description (first paragraph), technology/framework mentions |
| `package.json` | `name`, `description`, notable frameworks from `dependencies` and `devDependencies` |
| `go.mod` | Module path, major dependencies from `require` block |
| `Cargo.toml` | `[package]` name, notable entries from `[dependencies]` |
| `pyproject.toml` | `[project]` name, description, major entries from `dependencies` |
| `ARCHITECTURE.md` (project root, then `docs/ARCHITECTURE.md`) | Read up to 200 lines — architecture summary |
| User-specified paths in message | If the user's message references doc files (paths containing `/` or `\` with doc extensions), read and incorporate |

**3b. Create `REVIEW.md`** in the project root with these sections:

```markdown
# Review Configuration

## Project Context
- **Project**: {name from README or manifest}
- **Language**: {primary language(s) inferred from manifests/file extensions}
- **Framework**: {major frameworks from dependencies}
- **Architecture**: {brief summary from ARCHITECTURE.md, or "Not documented"}
- **Key dependencies**: {top 5-10 notable dependencies}

## Review Focus Areas
[Project-specific concerns derived from the codebase scan]

## Custom Rules
[Empty — user fills in project-specific rules]

## Model Overrides
[Empty — user can override reviewer models here]

## Configuration
confidence_threshold: medium
```

**3c.** Tell the user: "Generated `REVIEW.md` with project defaults. Edit it to customize review behavior."

If the user explicitly opted out, skip this step entirely.

## Step 4: Check for Previous Session

If `.checks/session.md` exists in the project root:

1. Read it. Parse the issue tracker table.
2. For each issue with status `open` or `verify`:
   - Read the file referenced by the issue.
   - Search for the **snippet** recorded in the issue (exact substring match).
   - Snippet **not found** in the file → mark as `fixed`.
   - Snippet **found** → keep current status (`open` stays `open`, `verify` stays `verify`).
   - File deleted, heavily restructured, or match inconclusive → mark as `verify`.
3. Hold these status updates — you will write them in Step 8.

If `.checks/session.md` does not exist, skip this step.

## Step 5: Launch 3 Reviewers in Parallel

Read these three agent prompt files (paths relative to plugin root):
- `agents/bug-reviewer.md`
- `agents/standards-reviewer.md`
- `agents/quality-reviewer.md`

For each agent file, construct the sub-agent prompt by combining:
1. The agent file contents (the reviewer's role and instructions)
2. The file contents under review (full source of each file, with file path headers)
3. The rubric (`references/rubric.md` contents)
4. The false-positives list (`references/false-positives.md` contents)
5. The output format spec (`references/output-format.md` contents)
6. The project `REVIEW.md` contents (if it exists)
7. **Known patterns** (conditional — see below)

**Known Patterns (conditional):**
Read `.checks/changes/{label}.md` (using the label from Step 1.5). If the file exists, extract the content under the `## Patterns` heading. If that content is non-empty (not just whitespace or blank), store it as `patterns_text`. If the file doesn't exist or `## Patterns` is empty, set `patterns_text` to empty (omit from prompt).

Assemble the prompt for each reviewer like this:

```
[Contents of the agent .md file]

---

## Review Context

### Files Under Review

[For each file:]
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

- **Bug Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Bug Reviewer"`, `prompt: <constructed prompt>`
- **Standards Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Standards Reviewer"`, `prompt: <constructed prompt>`
- **Quality Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Quality Reviewer"`, `prompt: <constructed prompt>`

After launching, tell the user: "Launched Bug Reviewer, Standards Reviewer, Quality Reviewer — waiting for results..."

## Step 6: Collect and Deduplicate

As each sub-agent completes, report to the user: "[Reviewer Name] complete (N findings)".

After ALL three have returned:

1. **Parse findings** from each reviewer's output. Each finding has: File, Line, Snippet, Severity, Description, Evidence.

2. **Deduplicate**: two findings are duplicates if they reference the same file AND overlapping line ranges AND describe the same underlying issue (use judgment on description similarity). Merge duplicates into a single finding, noting all source reviewers.

3. **Assign consensus confidence**:
   - **high** — 2 or more reviewers independently flagged the same issue
   - **medium** — 1 reviewer flagged it, severity is `critical` or `warning`
   - **low** — 1 reviewer flagged it, severity is `nit`

## Step 7: Handle Failures

For each reviewer:
- If it returned "No findings." → zero findings from that reviewer (this is valid, not a failure).
- If it returned empty output, errored, or produced unparseable output → skip its findings and add a warning to the final report: "[Reviewer Name] did not return results — coverage incomplete."
- Never block the pipeline waiting for a failed reviewer. If two reviewers returned and the third failed, proceed with what you have.

## Step 8: Persist to .checks/ (Unless Skipped)

Check if the user said "不收录", "不记录", "skip", or "once" in their message. If so, skip this entire step.

Otherwise:

**8a. Initialize directories** (if they don't exist):
- Create `.checks/` directory
- Create `.checks/history/` directory
- Create `.checks/changes/` directory
- Create `.checks/.gitignore` containing a single line: `*`

**8b. Determine run number**:
- List files in `.checks/history/`. They may be named in the old format (`001.md`, `002.md`, etc.) or the new format (`check001-label.md`, `check002-label.md`, etc.).
- Scan for both patterns: files matching `\d{3}\.md` and files matching `check\d{3}-.*\.md`. Extract the numeric portion from each.
- Next run number = highest number found across both patterns + 1 (or 1 if empty). Zero-pad to 3 digits.

**8c. Write history file** (`.checks/history/check{NNN}-{label}.md`, e.g. `check001-重构解析器.md`):

```markdown
# Check Run NNN

**Date**: <current date/time>
**Scope**: <comma-separated file list>
**Mode**: local
**Reviewers**: Bug (N), Standards (N), Quality (N)

## Findings

[All deduplicated findings in output-format.md format, with added Confidence and Source fields]
```

**8d. Update session.md**:

If `.checks/session.md` does not exist, create it:

```markdown
# Review Session

## Stage
developing

## Scope
[files reviewed in this run]

## Issue Tracker

| ID | Source | Run | Status | File | Snippet | Severity | Confidence | Description |
|----|--------|-----|--------|------|---------|----------|------------|-------------|
```

Assign issue IDs: `C`-prefixed, zero-padded to 3 digits, continuing from the last ID in the existing table (e.g., if last is C005, next is C006). If table is empty, start at C001.

For each new finding: add a row with status `open`, source `local`, and the current run number.

For issues processed in Step 4 (both previously `open` and `verify`):
- Issues marked `fixed` → update status to `fixed`
- Issues marked `verify` → update status to `verify`
- Issues whose status is unchanged → leave as-is

**8e. Update change aggregate** (`.checks/changes/{label}.md`):

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

## Step 9: Format Final Report

Output the report in this structure:

```
## Code Check Results

**Scope**: <file list>
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
[If skipped: "Results not persisted (one-time run)."]

### Next Steps
[Actionable recommendations. Examples:]
[- "Fix the N critical issues above, then re-run `/check` to verify."]
[- "No critical issues — consider `/check-full` or `/check-git` before committing."]
[- "All previous issues resolved. Ready to commit."]
```

If there are zero total findings across all reviewers: output "**No findings.** Code looks good." and skip the severity sections.
