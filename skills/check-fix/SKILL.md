---
name: check-fix
description: "AI-assisted issue fixing with parallel Fix Agents, verification, and session tracking. Use for automated code repair of /check findings."
disable-model-invocation: true
---

# /check-fix — AI-Assisted Issue Fixing

You are the orchestrator for automated issue fixing. Parse open issues from the review session, classify them, launch parallel Fix Agents, verify results, and update the session.

Follow these steps in order. Do not skip steps. Do not run git commands. Do not modify `.checks/changes/` files.

---

## Step 1: Read Session and Parse Issues

Read `.checks/session.md` in the project root.

**If the file does not exist:** output "没有审查会话。先运行 /check 创建会话。" → stop immediately.

Parse the Issue Tracker markdown table. Extract all rows with available fields: ID, Source, Run, Type (if column exists), Status, File, Snippet, Severity, Confidence, Description.

**If the table has no Type column** (e.g., session created by `/check` only): treat all issues as `Type = code`. The Type column is only present when `/check-rules` has contributed findings.

**Filter to open issues only** (Status = `open`).

**If no open issues exist:** output "没有待修复的 issue。" → stop immediately.

**If the user specified IDs** (e.g., `/check-fix C001 R003`): filter to only those IDs. For any ID that does not exist or is not `open`, warn the user: "⚠ {ID}: 未找到或状态非 open，已跳过。"

Store the resulting issue list for the next steps.

## Step 2: Classify Issues

Split the open issues into two groups:

**auto_fix** — issues that can be fixed immediately without user input:
- Type = `code` (any severity)
- Type = `spec` AND Severity = `UNDOCUMENTED`

**ask_user** — issues that require user direction before fixing:
- Type = `spec` AND Severity = `DRIFT`
- Type = `spec` AND Severity = `MISSING`
- Type = `spec` AND Severity = `STALE`

## Step 3a: Launch auto_fix Fix Agents

Group auto_fix issues by File field — one group per unique file path.

For each file group, construct the Fix Agent prompt:

1. Read `agents/fix-agent.md` (path relative to plugin root) — include its full contents as role instructions
2. Read `references/fix-report-format.md` (path relative to plugin root) — include its full contents as output format specification
3. List all issues for that file with their complete fields (ID, Type, Severity, File, Snippet, Description, and any other available fields)
4. For issues where Type = `spec` AND Severity = `UNDOCUMENTED`: add `Direction: 补文档` to the issue
5. Include instruction: "If a `REVIEW.md` exists at the project root, read it first to understand project-specific context."

**Launch ALL file groups in a SINGLE message** using the Task tool. This is critical — they MUST be in the same response to run in parallel:

- `subagent_type`: "generalPurpose"
- `readonly`: false
- `run_in_background`: true
- `description`: "Fix Agent: {filename}"
- `prompt`: the constructed prompt
- Do NOT specify `model` (inherits the user's IDE model)

If auto_fix is empty, skip this step.

## Step 3b: Ask User About Spec Issues (SIMULTANEOUS with Step 3a)

**In the SAME response** as launching the Fix Agents in Step 3a, present the ask_user issues to the user with direction options.

For each ask_user issue, display the issue details (ID, File, Severity, Description) and offer these options based on Severity:

- **DRIFT**: "改代码" / "改文档" / "跳过"
- **MISSING**: "补实现" / "删文档描述" / "跳过"
- **STALE**: "接受差异" / "修代码" / "修文档" / "跳过"

Format example:
```
### 需要确认修复方向

| ID | File | Type | Description | Options |
|----|------|------|-------------|---------|
| R001 | src/game.py | DRIFT | Spec 写 38... | 改代码 / 改文档 / 跳过 |
| R003 | src/api.py | MISSING | 文档描述了... | 补实现 / 删文档描述 / 跳过 |

请回复每个 issue 的修复方向（如 "R001 改代码, R003 跳过"）。
```

If ask_user is empty, skip this part entirely. Only display auto_fix launch confirmation: "Launched Fix Agents — waiting for results..."

## Step 4: Launch ask_user Fix Agents

After the user responds with directions for the ask_user issues:

1. Parse the user's response to extract direction per issue ID
2. Issues marked "跳过" → record as SKIPPED with reason "用户选择跳过"
3. For remaining issues, group by File field

Construct Fix Agent prompts the same way as Step 3a, but include the user's specified direction for each issue (e.g., `Direction: 改代码` or `Direction: 补实现`).

Launch ALL file groups in a SINGLE message using the Task tool with the same parameters as Step 3a.

If all ask_user issues were skipped, proceed directly to Step 5.

## Step 5: Collect Fix Agent Results

As each Fix Agent completes, report to the user: "[Fix Agent: {filename}] complete"

After ALL Fix Agents have returned (both auto_fix and ask_user):

1. **Parse each agent's output** against the fix report format (`references/fix-report-format.md`):
   - Match section headers: `### {ID} — FIXED` or `### {ID} — SKIPPED`
   - Extract fields: File, Lines Modified, Change Description, Snippet Before/After (for FIXED) or Reason (for SKIPPED)

2. **Categorize results** for each issue:
   - **FIXED**: agent reported `FIXED` with valid details
   - **SKIPPED**: agent reported `SKIPPED` with reason
   - **failed**: agent returned unparseable output, errored, or did not include the issue ID in its report

## Step 6: Launch Verify Agents

For each file that has at least one FIXED issue, construct a Verify Agent prompt:

1. Read `agents/verify-agent.md` (path relative to plugin root) — include its full contents as role instructions
2. Include all FIXED issues for that file:
   - Original: ID, Description, File, Snippet (original)
   - Fix details: Lines Modified, Change Description, Snippet Before, Snippet After
3. Include instruction: "Read the file at `{file path}` to perform verification checks."

**Launch ALL verify tasks in a SINGLE message** using the Task tool:

- `subagent_type`: "generalPurpose"
- `readonly`: true
- `run_in_background`: true
- `model`: "claude-4.5-haiku-thinking"
- `description`: "Verify Agent: {filename}"
- `prompt`: the constructed prompt

If no issues were FIXED (all skipped or failed), skip to Step 7.

## Step 7: Update session.md

After ALL Verify Agents have returned:

1. **Parse Verify Agent outputs** — for each issue, extract the verdict:
   - `### {ID} — PASS` or `PASS_WITH_NOTE` → verified
   - `### {ID} — FAIL` → verification failed

2. **Update the Issue Tracker table in `.checks/session.md`**:

   | Fix Result | Verify Result | New Status | Description Update |
   |------------|---------------|------------|-------------------|
   | FIXED | PASS or PASS_WITH_NOTE | `verify` | unchanged |
   | FIXED | FAIL | `open` | append " (修复已尝试，验证失败: {reason})" |
   | SKIPPED | — | `open` | unchanged |
   | failed | — | `open` | append " (修复代理错误)" |

3. **Write the updated session.md** — preserve all other content, only modify the Status and Description columns for affected rows.

**Constraints:**
- Do NOT modify `.checks/changes/` files
- Do NOT run any git commands

## Step 8: Output Final Report

Output the report in this format:

```
## Check Fix Results

**Issues processed**: {total count}

### ✓ 已修复 (verify)
- {ID}: {Change Description} ({File}:{Lines Modified})
[Repeat for each verified issue. If none: "None."]

### ✗ 修复失败
- {ID}: {reason} ({File})
[Repeat for each failed verification or agent error. If none: "None."]

### ⊘ 跳过
- {ID}: {reason}
[Repeat for each skipped issue. If none: "None."]

运行 /check 确认修复。
```
