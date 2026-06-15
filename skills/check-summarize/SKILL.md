---
name: check-summarize
description: "Analyze review history to extract bug patterns, hotspots, and recommended REVIEW.md rules. Use for check-summarize, summarize checks, review summary, or lessons learned."
disable-model-invocation: true
---

# /check-summarize — Experience Extraction

You are an analyst reviewing the history of code check sessions to extract actionable patterns. Analyze all historical findings, identify recurring issues, and produce a structured experience summary.

## Step 1: Validate Data Source

Check for data sources in this order:

**Primary: `.checks/changes/` directory**
- If `.checks/changes/` exists and contains ≥2 `.md` files → use **changes-based analysis** (Steps 2a-3a below).
- If `.checks/changes/` has 0-1 files → fall through.

**Fallback: `.checks/history/` directory**
- If `.checks/history/` exists and contains ≥3 run files → use **history-based analysis** (original Steps 2-3 below).
- If neither source has enough data → inform the user: "Not enough review history for meaningful pattern extraction. Run more `/check` cycles."

Announce which mode you're using: "Analyzing N change records (changes-based mode)" or "Analyzing N run files (history-based mode)."

## Step 2a: Load Change Records (Changes-Based Mode)

Read every `.md` file in `.checks/changes/`.

For each change file, extract:
- Change label (from `# Change: {label}`)
- Source (openspec / git branch / user description / unclassified)
- Files involved
- Review history table (run IDs, dates, finding counts)
- Issue patterns (if populated)

## Step 3a: Change-Type Classification and Analysis

**Classify each change by type** using label keywords and source metadata:
- **refactor**: label contains "refactor", "重构", "restructure", "reorganize"
- **new-feature**: label contains "feat", "add", "新增", "implement", "create"
- **optimization**: label contains "perf", "optim", "优化", "speed", "cache"
- **bugfix**: label contains "fix", "修复", "bug", "patch", "hotfix"
- **other**: none of the above match

**Aggregate by change type:**
For each type, across all changes of that type:
- Total changes in this category
- Total findings across all runs of these changes
- Most common file patterns
- Recurring issue descriptions

**Produce change-type insights:**
For each type with ≥2 changes: "When doing {type} changes, these bug patterns commonly appear: {patterns}."

## Step 2: Load All History

If using history-based mode (fallback), follow Steps 2-9 as they currently exist — do not use Steps 2a/3a.

Read every file in `.checks/history/` (001.md, 002.md, ...) and `.checks/session.md`.

For each run file, extract:
- Run number
- Files reviewed
- Each finding: file, line, snippet, severity, confidence, description, source reviewer

From `session.md`, extract:
- All issues with their current status (open / fixed / verify)
- The session stage

## Step 3: Bug Pattern Analysis

Categorize all findings by type. Common type categories:
- Null/undefined handling
- Error handling gaps
- Race conditions / concurrency
- Type safety issues
- Boundary validation
- Security (injection, auth, secrets)
- API contract violations
- Code structure / spaghetti
- Dead code / complexity
- Naming / convention violations

For each category:
- Count total occurrences across all runs
- Count unique files affected
- Note which reviewers most frequently flag this category
- Identify if the pattern is increasing, stable, or decreasing over time

Flag as **high-frequency** any category appearing in 3+ different runs.

## Step 4: Hotspot Identification

Aggregate findings by file path.

For each file:
- Count total findings across all runs
- List severity distribution (critical / warning / nit)
- List which types of issues appear

Flag as **hotspot** any file appearing in findings across 3+ different runs.

Sort hotspots by total finding count (descending).

## Step 5: Fix Pattern Extraction

From `session.md`, identify all issues with status `fixed`.

For each fixed issue, examine:
- What the original issue was (description, severity, type)
- When it was introduced (run number)
- When it was resolved (run number or "current")

Group fixed issues by type and look for common resolution patterns:
- "Added null checks at boundary functions"
- "Centralized error handling in middleware"
- "Extracted shared logic into helper"
- "Added input validation at API layer"

List the top fix patterns with occurrence counts.

## Step 6: REVIEW.md Recommendations

Based on the patterns found, generate concrete rules for the project's `REVIEW.md`.

For each high-frequency bug pattern NOT already covered by an existing REVIEW.md rule:
- Draft a specific, actionable rule
- Include the evidence (occurrence count, affected files)
- Format as ready-to-paste text

Example output:

```markdown
## Suggested REVIEW.md Additions

### Null Safety at API Boundaries
**Evidence**: 7 null-handling issues across 4 runs, primarily in `src/api/` handlers.
**Rule**: All API handler functions MUST validate input parameters for null/undefined before processing. Use the existing `validateInput()` helper.

### Error Propagation in Async Chains
**Evidence**: 5 swallowed-error findings across 3 runs in `src/services/`.
**Rule**: Async functions MUST propagate errors to the caller. Do not catch errors silently — either handle them with user-facing feedback or re-throw.
```

## Step 7: Optional REVIEW.md Update

Check the user's message:
- If it contains "update REVIEW.md", "写入 REVIEW.md", or "append to REVIEW.md":
  - Read the current `REVIEW.md`
  - Append the suggested rules under a `## Auto-generated Rules` section
  - If the section already exists, append below existing auto-generated rules
  - Confirm: "Added N rules to REVIEW.md under '## Auto-generated Rules'."
- Otherwise: just include the suggestions in the output for manual review.

## Step 8: Write lessons.md

Write the full analysis to `.checks/lessons.md` with this structure:

```markdown
# Code Check — Experience Summary

Generated: [date]
Based on: [N] review runs

## By Change Type

### Refactor Changes
- N changes analyzed
- Common patterns: [list]
- Insight: "When refactoring, watch for: [patterns]"

### New Feature Changes
[same structure]

### Bugfix Changes
[same structure]

[Only include types that have ≥2 changes]

## High-Frequency Bug Patterns

| Pattern | Occurrences | Runs | Top Files | Trend |
|---------|-------------|------|-----------|-------|
| ...     | ...         | ...  | ...       | ...   |

## File Hotspots

| File | Total Findings | Criticals | Warnings | Nits |
|------|----------------|-----------|----------|------|
| ...  | ...            | ...       | ...      | ...  |

## Fix Patterns

| Resolution Pattern | Count | Example Issue |
|-------------------|-------|---------------|
| ...               | ...   | ...           |

## Suggested REVIEW.md Additions

[Ready-to-paste rules with evidence]
```

## Step 8.5: Spec-Alignment Drift Analysis (if applicable)

If any history files match `rules{NNN}-*.md` OR any changes/ files contain Mode=rules rows:

1. Identify all spec-alignment findings (Type=spec in session.md, or from rules-prefixed history files)
2. Group by rule document (from the Rule Document / SOURCE field)
3. Count recurring drift per rule document across runs

Produce a "规格漂移热区" section in lessons.md:

```markdown
## 规格漂移热区

| Rule Document | DRIFT Count | MISSING Count | Runs Affected | Trend |
|---------------|-------------|---------------|---------------|-------|
| ...           | ...         | ...           | ...           | ...   |
```

This identifies which rule documents repeatedly have findings — indicating either the spec needs updating or a persistent implementation gap.

If no spec-alignment data exists, skip this step silently.

## Step 9: Report

Output a summary to the user:
- Number of runs analyzed
- Top 3 bug patterns with counts
- Top 3 file hotspots
- Number of fix patterns identified
- Number of REVIEW.md rules suggested
- Whether lessons.md was written
- Whether REVIEW.md was updated (if requested)
- If spec-alignment data exists: top 3 spec drift hotspots
