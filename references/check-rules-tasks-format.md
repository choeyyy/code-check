# CheckRulesTasks.md Format

When `/check-rules` scope exceeds 3 spec-code pairs, the Orchestrator generates a `CheckRulesTasks.md` task tracking file in the project root. This file tracks progress across batches.

---

## Format

A Markdown table with these columns:

| Column | Type | Description |
|--------|------|-------------|
| # | int | Sequential pair number |
| Spec Document | string | Relative path to the rule document |
| Code Patterns | string | Glob pattern(s) for associated code |
| Status | enum | `pending` / `running` / `done` / `skipped` |
| Batch | int | Batch number this pair belongs to |
| Findings | string | Count + type summary once done, `-` while pending/running |

---

## Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not yet started |
| `running` | Currently being reviewed |
| `done` | Review complete |
| `skipped` | User interrupted or error occurred |

---

## Lifecycle

1. **Generated** at the start of Phase 2 when scope > 3 pairs
2. **Updated** after each batch completes (status → `done`, findings count populated)
3. **Updated** on user interruption (remaining → `skipped`)
4. **Included** in the final report output

---

## Batch Assignment

- Each batch contains up to 3 pairs
- Pairs are assigned to batches sequentially
- Within a batch, all pairs execute in parallel (each pair = 2 sub-agents)

---

## Template

```markdown
# Check-Rules Task Tracker

| # | Spec Document | Code Patterns | Status | Batch | Findings |
|---|---------------|---------------|--------|-------|----------|
| 1 | {path} | {patterns} | pending | 1 | - |
| 2 | {path} | {patterns} | pending | 1 | - |
| 3 | {path} | {patterns} | pending | 1 | - |
| 4 | {path} | {patterns} | pending | 2 | - |
```
