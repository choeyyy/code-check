# Output Format

All reviewer agents MUST produce findings in this exact format. No exceptions.

---

## Rules

1. Return findings as a structured markdown list using the template below.
2. If there are zero findings, respond with exactly: **No findings.**
3. An empty review is valid. Do NOT pad reviews with low-value nits to justify your existence.
4. If there are larger structural issues, do NOT dilute them with minor nits. Focus on what matters.
5. Order findings by severity: `critical` first, then `warning`, then `nit`.

---

## Finding Template

Each finding MUST include all six fields in this order:

```
### Finding: <short title>

- **File**: <path relative to project root>
- **Line**: <line number or range, e.g. `42` or `42-48`>
- **Snippet**: `<the actual problematic code, verbatim from the diff>`
- **Severity**: <`critical` | `warning` | `nit`>
- **Description**: <what is wrong and why, referencing specific code>
- **Evidence**: <the reasoning chain showing WHY this is a problem>
```

---

## Severity Definitions

- **critical**: Bugs, data loss, security vulnerabilities, fundamentally broken behavior. The code will produce wrong results or cause harm in production.
- **warning**: Design concern, maintainability risk, correctness issue that isn't immediately broken but will cause problems under realistic conditions or during future changes.
- **nit**: Style, naming, minor improvement. Only include if genuinely useful to the author — not to demonstrate thoroughness.

---

## Field Requirements

**File**: Relative path from the project root. Use forward slashes. Example: `src/api/handlers/user.go`

**Line**: The line number (or range) in the file as it appears in the diff. Use the post-change line numbers. A range like `42-48` means the issue spans those lines.

**Snippet**: The actual line(s) of code that contain the problem, copied verbatim from the diff. This field is used for automated fix-detection — it must match the source exactly. Keep it to the minimal relevant lines (1-5 lines typically).

**Severity**: One of the three values above. Nothing else.

**Description**: Concrete, specific, referencing the actual code. **MUST be written in Chinese (中文).** Bad: "This could cause issues." Good: "第 44 行的 `fetchUser` 调用未检查 404 响应，导致第 46 行 `user.name` 在用户不存在时抛出 TypeError。"

**Evidence**: The reasoning chain that proves this is a real issue, not a hypothetical. **MUST be written in Chinese (中文).** For bugs, trace the execution path. For security issues, trace the input flow. For design issues, explain the concrete consequence. Bad: "这可能是 null。" Good: "当 `getConfig()` 返回 `undefined`（`CONFIG_PATH` 环境变量未设置时发生，见 `config.ts:12`），第 30 行的解构赋值会抛异常。该环境变量按 README 说明是可选的。"

---

## Example Output

### Finding: API 响应未检查即访问属性

- **File**: src/api/handlers/user.go
- **Line**: 44-46
- **Snippet**: `resp, _ := client.GetUser(ctx, userID)`
- **Severity**: critical
- **Description**: `GetUser` 的 error 返回值被丢弃。当用户不存在时 `resp` 为 nil，第 46 行 `resp.Name` 会触发 nil pointer panic。
- **Evidence**: `GetUser` 在用户 ID 不存在时返回 `(nil, ErrNotFound)`（见 `client.go:112`）。该 handler 由公开 API 路由 `/users/:id` 调用，`userID` 来自 URL 路径——任何无效或已删除的用户 ID 都会触发此路径。

### Finding: 可并行的 API 调用被串行执行

- **File**: src/services/dashboard.go
- **Line**: 88-95
- **Severity**: warning
- **Snippet**: `metrics := fetchMetrics(ctx); alerts := fetchAlerts(ctx)`
- **Description**: `fetchMetrics` 和 `fetchAlerts` 是两个独立调用但被串行执行。每个约 200ms（据 tracing 数据），给每次 dashboard 加载增加了不必要的延迟。
- **Evidence**: 两个调用互不依赖，都只接受 context 和 dashboard ID。使用 `errgroup` 或等价方案可将此函数延迟减半。

---

## Zero-Findings Output

When you find no issues:

```
**No findings.**
```

---
---

# Spec-Alignment Finding Format

The following format applies to `/check-rules` findings (Type = `spec`). These represent discrepancies between rule documents and code implementation — not bugs or style issues.

---

## Spec-Alignment Finding Template

Each spec-alignment finding MUST include all fields in this order:

```
### Finding: <short title>

- **ID**: R{NNN}
- **Type**: <`DRIFT` | `MISSING` | `UNDOCUMENTED` | `STALE`>
- **Rule Document**: <SOURCE link to the rule document section>
- **File**: <code file path relative to project root>
- **Line**: <line number or range>
- **Snippet**: `<the actual code, verbatim>`
- **Description**: <what is inconsistent and why, in Chinese>
- **Evidence**: <reasoning chain showing the discrepancy, in Chinese>
- **Source Agent**: <`Spec→Code` | `Code→Spec`>
```

---

## Spec-Alignment Type Definitions

| Type | Meaning | Source Agent |
|------|---------|--------------|
| **DRIFT** | Code implementation does not match spec assertion | Spec→Code |
| **MISSING** | Spec describes behavior but code has no corresponding implementation | Spec→Code |
| **UNDOCUMENTED** | Code has behavior that spec does not describe | Code→Spec |
| **STALE** | Known-diff marked "pending review" with no recent update | Spec→Code |

---

## ID Format

Spec-alignment findings use the `R{NNN}` prefix (e.g. `R001`, `R002`) to distinguish from code-quality findings which have no prefix. The sequence resets per `/check-rules` run.

---

## Rule Document SOURCE Link

The Rule Document field uses the SOURCE format defined in `spec-card-format.md`:

```
{relative-doc-path} §{section}, line {N}
```

This allows the user to navigate directly to the relevant section of the original rule document.

---

## Cross-Document Annotation

When a finding affects multiple rule documents (identified during Phase 3 merge):

```
- **Rule Document**: {primary SOURCE link}
- **Also affects**: {doc-a}, {doc-b}
- **Root Cause Note**: 可能共享根因
```
