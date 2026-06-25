---
name: check-full
description: "Thorough code review with 5 parallel reviewers, confidence scoring, and threshold filtering. Use for check-full, full check, full review, thorough review, or deep check."
disable-model-invocation: true
---

# /check-full — Thorough Code Review

You are the orchestrator for a thorough multi-agent code review. Launch 5 parallel reviewers, score each finding's confidence, filter by threshold, persist results, and report.

Follow these steps in order. Do not skip steps. Do not modify files under review.

---

## Step 1: Determine Scope

Determine which files to review using this priority chain:

1. **User specified files/directories** in their message → use those. Resolve globs/directories to individual files.
2. **Openspec active change** → Check if an `openspec/` directory exists in the project root. If it does, run `openspec status --json`. If the output shows an active change with in-progress tasks, read the tasks file and extract any file paths mentioned in the current in-progress task description. If file paths are found, use them as the review scope. If `openspec/` doesn't exist, the command fails, or no file paths are extractable, fall through silently to the next priority.
3. **Git dirty files** → run `git status --porcelain` in the project root. If it succeeds and returns output, extract file paths (both staged and unstaged changes). Exclude deleted files (lines starting with `D` or ` D`).
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

Read all of the following. Missing optional items are not errors — skip and continue.

**Required — file contents:**
For each file in scope, read its full content. These are the primary review targets.

**Required — plugin references:**
Read these three files from the plugin's `references/` directory:
- `references/rubric.md` — review criteria for all reviewers
- `references/false-positives.md` — patterns reviewers must not report
- `references/output-format.md` — structured finding format all reviewers must follow

**Optional — project REVIEW.md:**
Look for `REVIEW.md` in the workspace root. If it exists, read it — it contains project-specific review rules that supplement the built-in rubric.

**Required — git context (for History Reviewer):**
For each file in scope, collect:
- `git blame <file>` — line-by-line authorship and recency
- `git log --oneline -20 -- <file>` — recent commit history for the file

If any git command fails (not a git repo, file untracked, etc.), skip that file's git context and note it. The History Reviewer will work with whatever context is available.

## Step 3: REVIEW.md Auto-Generation

If the workspace has no `REVIEW.md` and the user did not say "不生成 REVIEW.md" or "no REVIEW.md":

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

**3b. Create `REVIEW.md`** in the workspace root with structured `## Project Context` (bullet format: Project, Language, Framework, Architecture, Key dependencies), plus Review Focus Areas, Custom Rules, Model Overrides, Configuration sections. Tailor content based on the built-in rubric and project characteristics discovered above.

**3c.** Tell the user: "Generated `REVIEW.md` with project defaults. Edit it to customize review behavior."

If the user opts out, proceed without it.

## Step 4: Check Previous Session

Look for `.checks/session.md` in the workspace root. If it exists:

1. Read it and extract the issue tracking table.
2. For each issue with status `open` or `verify`, check whether the problematic code snippet still exists in the current file contents. Use exact substring match on the snippet field, not line numbers (lines shift).
   - Snippet no longer present → mark as `fixed`
   - Snippet still present → keep current status
   - Cannot determine → mark as `verify` (reviewers will re-evaluate)
3. Report to the user: "Session update: N issues resolved, M still open, K need verification."

If `.checks/session.md` does not exist, skip this step.

## Step 5: Launch 5 Reviewers in Parallel

Read the agent prompt files and construct each reviewer's full prompt by combining the agent instructions with the collected context. Then launch ALL FIVE reviewers in a single message using the Task tool.

### Prompt Construction

For each reviewer, build the prompt by combining:
1. The agent file contents (the reviewer's role and instructions)
2. The file contents under review (full source of each file, with file path headers)
3. The rubric (`references/rubric.md` contents)
4. The false-positives list (`references/false-positives.md` contents)
5. The output format spec (`references/output-format.md` contents)
6. The project `REVIEW.md` contents (if it exists)
7. Additional context per reviewer (see specifications below)
8. **Known patterns** (conditional — see below)

**Known Patterns (conditional):**
Read `.checks/changes/{label}.md` (using the label from Step 1.5). If the file exists, extract the content under the `## Patterns` heading. If that content is non-empty (not just whitespace or blank), store it as `patterns_text`. If the file doesn't exist or `## Patterns` is empty, set `patterns_text` to empty (omit from prompt).

Assemble the prompt like this:

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
```

**5. Comments Reviewer** — `agents/comments-reviewer.md`
No additional context sections beyond the base template.

**Launch all five in a single message** using the Task tool. This is critical — they MUST be in the same response to run in parallel:

- **Bug Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Bug Reviewer"`, `prompt: <constructed prompt>`
- **Standards Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Standards Reviewer"`, `prompt: <constructed prompt>`
- **Quality Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "Quality Reviewer"`, `prompt: <constructed prompt>`
- **History Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `description: "History Reviewer"`, `prompt: <constructed prompt>`
- **Comments Reviewer**: `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`, `model: "claude-4.5-haiku-thinking"`, `description: "Comments Reviewer"`, `prompt: <constructed prompt>`

After launching, tell the user: "Launched Bug Reviewer, Standards Reviewer, Quality Reviewer, History Reviewer, Comments Reviewer — waiting for results..."

## Step 6: Collect Findings

Track reviewer completion order (1st, 2nd, 3rd...). As each reviewer completes, report progress including its position:

"[Reviewer Name] complete (N findings) — finished #X. Still waiting for: [remaining reviewer names]..."

When the last reviewer completes, mark it as the bottleneck:

"[Reviewer Name] complete (N findings) — finished last (bottleneck). All reviewers done."

After all reviewers finish:
1. Parse each reviewer's output for findings matching the output-format template.
2. Deduplicate: if two or more reviewers flag the same file + overlapping line range + substantially similar description, merge into one finding and note all source reviewers.
3. Preserve all unique findings across reviewers.

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
- Prompt includes: the single finding (full details), the file content where the finding was identified, REVIEW.md contents, false-positives list, and the scoring rubric above

Launch all judge sub-agents in a single message for parallelism.

### Batch Mode

Launch ONE confidence-judge sub-agent:
- Agent file: `agents/confidence-judge.md`
- Task tool config: `subagent_type: "generalPurpose"`, `readonly: true`
- `model: "claude-4.5-haiku-thinking"`
- Prompt includes: all findings together, all file contents, REVIEW.md, false-positives list, and the scoring rubric above

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

**10a. Initialize directories** (if they don't exist):
- Create `.checks/` directory
- Create `.checks/history/` directory
- Create `.checks/changes/` directory
- Create `.checks/.gitignore` containing a single line: `*`

**10b. Determine run number**:
- List files in `.checks/history/`. They match either old format (`\d{3}\.md`) or new format (`check\d{3}-.*\.md`).
- Take the max number from BOTH patterns, increment by 1 (or 1 if empty). Zero-pad to 3 digits.

**10c. Write history file** (`.checks/history/check{NNN}-{label}.md`):

```markdown
# Check Run NNN

**Date**: <current date/time>
**Change**: {label}
**Scope**: <comma-separated file list>
**Mode**: local (full)
**Reviewers**: Bug (N), Standards (N), Quality (N), History (N), Comments (N)
**Scoring**: <per-issue/batch>, threshold: <value>

## Findings

[All deduplicated findings in output-format.md format, with added Score and Source fields]
```

**10d. Update session.md**:

If `.checks/session.md` does not exist, create it with the standard template (see `/check` Step 8d).

Assign issue IDs: `C`-prefixed, zero-padded to 3 digits, continuing from the last ID in the existing table.

For each new finding: add a row with status `open`, source `local`, score column, and the current run number.

For issues processed in Step 4 (both previously `open` and `verify`):
- Issues marked `fixed` → update status to `fixed`
- Issues marked `verify` → update status to `verify`
- Issues whose status is unchanged → leave as-is

Stage stays at current value for local mode (does not auto-progress).

**10e. Update change aggregate** (`.checks/changes/{label}.md`):

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
## Code Check (Full) Results

**Change**: {label}
**Scope**: [files reviewed]
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
[New issues added, issues resolved since last check, current stage]

### Next Steps
[Recommendations: fix critical issues and re-run, consider warnings, etc.]
```

If there are zero findings above threshold, report "No findings above threshold (N findings scored below threshold and are listed in Below Threshold)." or "No findings." if there are none at all.
