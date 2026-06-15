---
name: check-session
description: "View review session status or archive and restart"
disable-model-invocation: true
---

# /check-session

Manage the current code review session. Supports two subcommands: `status` (default) and `end`.

Parse the user's message to determine the subcommand. If no subcommand is specified, default to `status`.

---

## Subcommand: status

### 1. Check for active session

Read `.checks/session.md`.

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
