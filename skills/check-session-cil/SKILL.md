---
name: check-session-cil
description: "View review session status, archive/restart, or query Cursor, Codex or Claude Code transcripts"
disable-model-invocation: true
---

## Host compatibility

Read [host capability mapping](../../references/host-compatibility.md) before using tools. It governs host-specific tool names, model arguments, installation paths and unavailable capabilities throughout this workflow. Keep all task approval and evidence requirements.


# /check-session-cil

Manage code review sessions **or** query Cursor agent conversation logs (CIL).

Parse the user's message to determine the subcommand:

| Subcommand | Trigger | Action |
|------------|---------|--------|
| `status` | default when no path/date given and `.checks/session.md` exists | Review session summary |
| `end` | user says `end` | Archive review session |
| `cil` | user gives a workspace path and/or asks for 对话/会话/transcript/today | Query agent transcripts |

If the user gives an absolute workspace path (e.g. `D:\REQUIREMENTS\gx-server\game-platform-new-qxc`) or asks for “今天的对话”, run **Subcommand: cil** even without the literal word `cil`.

---

## Transcript provider selection

The `cil` name is retained for compatibility. For conversation queries, first select the data provider
from the explicit request or current host. If unclear, ask; never read Cursor logs as a Codex/Claude session.
For Codex/Claude, obtain the selected path using host history tools or a user-supplied transcript path,
then run `python scripts/portable_sessions.py resolve --provider <codex|claude> --input <selected.jsonl>`
from this skill directory. Read the selected file for detailed content with original line references.
Use the host history tool to list sessions when available; if unavailable ask for the input path, not a made-up UUID.
For an explicit Cursor file the same command supports `--provider cursor`.
Only Cursor discovery follows the legacy CIL folder steps below. Review `status` / `end` operations remain unchanged.

## Subcommand: cil

Query today's (or specified date's) Cursor agent conversations for a workspace.

### 1. Resolve workspace path

- Use the path from the user message if provided.
- Otherwise use the current workspace root.

### 2. Map to Cursor projects folder

Agent transcripts live under:

```
%USERPROFILE%\.cursor\projects\<slug>\agent-transcripts\
```

**Slug rule:** `{driveLetter}-{path-with-slashes-as-dashes}` (no colon). Example:

- `D:\REQUIREMENTS\gx-server\game-platform-new-qxc` → `D-REQUIREMENTS-gx-server-game-platform-new-qxc`

If the exact slug folder is missing, try the lowercase-drive variant (e.g. `d-REQUIREMENTS-...`) or scan `%USERPROFILE%\.cursor\projects\` for a directory whose name ends with the last path segment.

### 3. Collect transcripts

For each `agent-transcripts/<uuid>/<uuid>.jsonl`:

- Filter by file `mtime` date (default: **today**, local timezone).
- If user specifies a date (`YYYY-MM-DD`), filter to that date instead.

### 4. Parse each jsonl

For each line (JSON):

- **user** messages: extract `<user_query>...</user_query>`; also extract `<timestamp>` when present.
- **assistant** messages: take first ~200 chars of text content as a one-line summary (skip tool-only turns).

Group by transcript UUID. Sort sessions by earliest timestamp in each file.

### 5. Present summary

```markdown
## Cursor Interaction Log (CIL)

**Workspace**: <absolute path>
**Date**: <YYYY-MM-DD>
**Sessions**: <N>

### Session 1 — <uuid short> (<start time> ~ <end time>)
**Topic**: <one-line inferred topic from first user query>

| Time | Role | Summary |
|------|------|---------|
| HH:MM | user | <query excerpt ≤120 chars> |
| HH:MM | asst | <summary ≤120 chars> |
...

### Session 2 — ...
...

### Day Overview
- **Main threads**: <bullet list of 3–6 themes across all sessions>
- **Commands used**: <e.g. /bf-rd-sop, /speckit-specify, …>
- **Outcomes**: <what was completed, blocked, or left open>
```

Omit empty sessions. If no transcripts found:

> No Cursor agent transcripts found for `<path>` on `<date>`. Confirm the workspace was opened in Cursor today.

---

## Subcommand: status

### 1. Check for active session

Read `.checks/session.md` in the **current workspace** (or path given by user).

- If the file does not exist, respond with:
  > No review session exists. Run `/check` to start reviewing.
- If the file exists but cannot be parsed (missing required sections, malformed tables), respond with:
  > Session file is corrupted or incomplete. Run `/check` to reinitialize.

Stop here in either case.

- If `.checks/changes/` exists but `.checks/session.md` does not exist: show the Active Changes table and note "No active session — run `/check` to start one. Historical change data is available."

### 2. Parse session.md

Extract from the file:

- **Stage**: one of `developing`, `pre-commit`, `final-review`
- **Issue tracker table**: each row contains an issue ID, file, severity, description, and status (`open` | `fixed` | `verify`)

Count issues by status:
- `open`: issues not yet addressed
- `fixed`: issues resolved by the developer
- `verify`: issues marked as fixed but awaiting confirmation

Also count issues by Type (if a Type column exists):
- `code`: findings from `/check` series (default if no Type column)
- `spec`: findings from `/check-rules`

### 3. Count review runs

List files in `.checks/history/`. Each file represents one review run.

- Files matching `check{NNN}-*.md` are code-quality runs
- Files matching `rules{NNN}-*.md` are spec-alignment runs
- If `.checks/history/` does not exist or is empty, set total runs to 0.

### 4. Present the summary

```
## Review Session Status

**Stage**: <stage>
**Total Runs**: <N> (code: <C>, rules: <R>)
**Issues**: <X> open, <Y> fixed, <Z> to verify
**By Type**: code: <A> open, spec: <B> open

### Open Issues
| ID | File | Severity | Description |
|----|------|----------|-------------|
<rows for all open issues, ordered by severity: critical > warning > nit>

### Recently Fixed
| ID | File | Severity | Description |
|----|------|----------|-------------|
<rows for fixed issues — omit this section entirely if none>

### Needs Verification
| ID | File | Severity | Description |
|----|------|----------|-------------|
<rows for verify issues — omit this section entirely if none>

### Active Changes

| Change | Runs | Latest | Total Findings |
|--------|------|--------|----------------|
<one row per change file, sorted by most recent run>

### Next Steps
<see recommendation logic below>
```

**Active Changes logic:**

If `.checks/changes/` exists, read all `.md` files in it. For each change file:
- Parse the change label (from the `# Change: {label}` title)
- Count rows in the Review History table (= run count)
- Count findings across runs

Present the Active Changes table (shown in the template above) sorted by most recent run. If `.checks/changes/` does not exist, omit the Active Changes section entirely.

### Recommendation logic for Next Steps

Evaluate conditions in order and include all that apply:

1. If any open issue has severity `critical`:
   > Fix critical issues and run `/check` again.
2. If open issues exist (non-critical only):
   > Address open warnings and run `/check` to verify.
3. If `verify` issues exist:
   > Run `/check` to verify fixed issues.
4. If stage is `pre-commit` and open issues remain:
   > Address remaining issues before merging.
5. If all issues are `fixed` and none are `verify`:
   > Consider running `/check-full` before committing.
6. If zero issues across all statuses:
   > No open issues. Ready to commit!

---

## Subcommand: end

### 1. Check for active session

Read `.checks/session.md`.

- If the file does not exist, respond with:
  > No active session to archive.
- Stop here.

### 2. Create archive

Generate a timestamp in `YYYY-MM-DD-HHmmss` format using the current date and time.

Create the directory: `.checks/archive/<timestamp>/`

### 3. Move session data to archive

- Move `.checks/session.md` → `.checks/archive/<timestamp>/session.md`
- Move all files from `.checks/history/` → `.checks/archive/<timestamp>/history/`

**Do NOT archive `.checks/changes/`** — this directory contains cross-session knowledge that persists across session boundaries. Only `session.md` and `history/` are archived.

### 4. Initialize fresh session

Create a new `.checks/session.md` with:

```markdown
# Review Session

## Metadata
- **Stage**: developing
- **Scope**: (none)
- **Started**: <current date and time>

## Issue Tracker

| ID | File | Line | Severity | Snippet | Description | Status |
|----|------|------|----------|---------|-------------|--------|
```

Create an empty `.checks/history/` directory.

### 5. Confirm

Respond with:

> Session archived to `.checks/archive/<timestamp>/`. Changes directory preserved. New session started.
