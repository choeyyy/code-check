# Fix Report Format

All Fix Agents MUST produce results in this exact format. No exceptions.

---

## Rules

1. Return one entry per issue using the template below.
2. Every issue assigned to the agent MUST appear in the report — either as `FIXED` or `SKIPPED`.
3. Do NOT combine multiple issues into a single entry.
4. Order entries by the original issue ID.

---

## Entry Template — FIXED

When the agent successfully fixes an issue:

```
### {ID} — FIXED

- **File**: <path relative to project root>
- **Lines Modified**: <line number or range, e.g. `42` or `42-48`>
- **Change Description**: <what was changed and why, in Chinese>
- **Snippet Before**: `<original code, verbatim>`
- **Snippet After**: `<modified code, verbatim>`
```

## Entry Template — SKIPPED

When the agent cannot fix an issue:

```
### {ID} — SKIPPED

- **File**: <path relative to project root>
- **Reason**: <why the fix was not applied, in Chinese>
```

---

## Status Definitions

- **FIXED**: The issue was resolved. The code has been modified and the original problem no longer exists.
- **SKIPPED**: The agent determined it cannot safely fix this issue. Common reasons: ambiguous intent, fix would change public API, requires human judgment, fix scope exceeds single-issue boundary.

---

## Field Requirements

**{ID}**: The original finding ID as assigned by the review session (e.g. `C001`, `C003`, `R005`). Must match exactly so the Orchestrator can correlate fix results back to the session.md row.

**File**: Relative path from the project root. Use forward slashes. Example: `src/api/handlers/user.go`

**Lines Modified**: The line numbers in the file that were changed by the fix. Use post-fix line numbers. A range like `42-48` means lines 42 through 48 were modified. For multi-site fixes within one file, use comma-separated ranges: `42-48, 103`.

**Change Description**: Concrete explanation of what was modified and why. **MUST be written in Chinese (中文).** Bad: "修复了问题。" Good: "为 `fetchUser` 返回值添加了 nil 检查，当 `resp` 为 nil 时返回 404 错误而非继续执行。"

**Snippet Before**: The original code before the fix, copied verbatim. Keep to the minimal relevant lines (1-5 lines typically). Used by the Orchestrator to verify the fix target is correct.

**Snippet After**: The code after the fix, copied verbatim. Same line scope as Snippet Before. Used by Verify Agents to validate the fix.

**Reason** (SKIPPED only): Why the fix was not applied. **MUST be written in Chinese (中文).** Must be specific enough for the user to understand what manual action is needed. Bad: "太复杂了。" Good: "该修复需要改变 `UserService.GetUser` 的公开返回类型签名，影响 12 个调用方，超出单 issue 修复范围。"

---

## Example Output

### C003 — FIXED

- **File**: src/api/handlers/user.go
- **Lines Modified**: 44-46
- **Change Description**: 为 `GetUser` 返回值增加了 error 检查。当 error 为 `ErrNotFound` 时返回 404 响应，其他 error 返回 500。移除了对 `resp` 的直接解引用。
- **Snippet Before**: `resp, _ := client.GetUser(ctx, userID)`
- **Snippet After**: `resp, err := client.GetUser(ctx, userID); if err != nil { return handleErr(w, err) }`

### C007 — SKIPPED

- **File**: src/services/dashboard.go
- **Reason**: 将串行调用改为并行需要引入 `errgroup` 依赖并重构错误处理逻辑，属于架构级变更，超出单 issue 自动修复的安全边界。建议人工评估后重构。

---

## Parsing Notes

The Orchestrator extracts per-issue results by matching section headers:

- `### {ID} — FIXED` → issue was resolved, extract modification details
- `### {ID} — SKIPPED` → issue was not resolved, extract reason

The `—` (em-dash) is the delimiter between the issue ID and the status keyword. Both `FIXED` and `SKIPPED` are uppercase constants.
