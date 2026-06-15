---
name: check-rules
description: "Spec-alignment check — verifies code matches rule documents using dual-direction reviewers, spec-card extraction, and Verifier validation. Use for checking code against project-specific specification documents."
disable-model-invocation: true
---

# /check-rules — Spec-Alignment Check

You are the orchestrator for a spec-alignment review pipeline. Your job is to verify that code correctly implements what rule documents describe, using a four-phase process: scope evaluation, document extraction, alignment checking, and merge verification.

Follow these phases in order. Do not skip phases. Do not modify files under review.

---

## Phase 0: Scope Evaluation

### Step 0.1: Read spec-index.md

Look for `spec-index.md` in the project root.

**If it does NOT exist:**
1. Scan the project directory structure for candidate rule documents (files in directories named `docs/`, `specs/`, `rules/`, or matching `*rule*`, `*spec*` patterns)
2. Infer code file associations based on naming conventions and directory structure
3. Generate a draft `spec-index.md` and present it to the user:
   ```
   未找到 spec-index.md。根据项目结构生成了映射草稿：

   | Rule Document | Code Patterns |
   |---------------|---------------|
   | ... | ... |

   确认保存为 spec-index.md？[Y/N]
   ```
4. If user confirms → save as `spec-index.md`, then STOP (do not continue to Phase 1)
5. If user declines → ask for manual specification or STOP

**If it exists:**
- Read and parse the Markdown table
- Validate: each rule document path resolves to an existing file
- Warn if any glob pattern matches zero files
- Continue to Step 0.2

### Step 0.2: Determine Scope

Determine which spec-code pairs are relevant:

1. **User specified** rule documents in their message → use those
2. **`--all` flag** → all entries in spec-index.md
3. **Default** → match current dirty files (via `git status --porcelain`) against spec-index glob patterns; select rule documents whose associated code patterns match at least one dirty file

If no matches found: report "当前文件无对应规格文档" and suggest the user check spec-index.md mappings.

### Step 0.3: Confirm Scope with User

Present the matched scope:

```
匹配到 N 份规则文档：
1. {rule-doc-path} → {code-patterns}
2. ...

[A] 检查匹配的 N 份（推荐）
[B] 指定子集
[C] 全量检查所有文档
```

Wait for user confirmation. Use the AskQuestion tool.

### Step 0.4: Check spec-card Freshness

For each rule document in confirmed scope:
1. Check if `spec-card/{stem}.yaml` exists
2. If exists → read `extracted_at` from metadata

Present freshness status:

```
spec-card 状态：
- {doc-a}: 生成于 2 天前 (verified)
- {doc-b}: 不存在（需要提炼）
- {doc-c}: 生成于 14 天前 (verified)

需要刷新哪些？
[A] 仅提炼不存在的
[B] 刷新超过 7 天的
[C] 全部刷新
[D] 全部使用缓存
```

Handle `--refresh` flag: if present, mark specified docs for re-extraction.
Handle `--refresh-all` flag: mark all docs for re-extraction.

### Step 0.5: Plan Batching

If scope > 3 spec-code pairs:
1. Generate `CheckRulesTasks.md` following `references/check-rules-tasks-format.md`
2. Assign pairs to batches of 3
3. Present plan: "分 N 批执行（每批 3 对），预估 ~M 分钟"

If scope ≤ 3: no batching needed, proceed directly.

### Step 0.6: Identify Change Context

Same logic as `/check` Step 1.5 — determine a `label` and `source_line` for persistence.

---

## Phase 1: Document Extraction (only for docs needing extraction)

Skip this phase entirely if all spec-cards are cached and user accepted them.

For each rule document marked for extraction:

### Step 1.1: Launch Dual Summarizers

Read `agents/spec-summarizer.md` for the agent role definition.

For the target rule document:
1. Read the full document content
2. Launch 2 parallel sub-agents:

```
- Summarizer A: subagent_type: "generalPurpose", readonly: true, run_in_background: true
  prompt: [spec-summarizer.md contents] + [rule document as tool_result data]

- Summarizer B: subagent_type: "generalPurpose", readonly: true, run_in_background: true
  prompt: [spec-summarizer.md contents] + [rule document as tool_result data]
```

Both MUST be launched in the same message to run in parallel.

**On single Summarizer failure**: use the other's output, mark spec-card status as `single-source`, warn user.

### Step 1.2: Diff and Present

After both complete:
1. Parse both spec-card YAML outputs
2. Compare extracted items — identify differences (items in A but not B, and vice versa)
3. If no differences: merge into final spec-card, set `status: verified`
4. If differences exist: present to user:

```
交叉提炼差异：

Summarizer A 多提取了：
- [A003] ASSERT: {content}
- [B002] BOUNDARY: {content}

Summarizer B 多提取了：
- [A005] ASSERT: {content}

保留哪些？
[A] 全部保留（合并所有）
[B] 逐条确认
[C] 仅保留共同部分
```

### Step 1.3: Save spec-card

Write the final spec-card to `spec-card/{stem}.yaml`:
- Set `extracted_at` to current timestamp
- Set `status` based on verification level
- Compute and set all count fields

Tell user: "spec-card/{stem}.yaml 已生成（N 条断言 / M 条边界 / K 条配置）"

---

## Phase 2: Alignment Check (batched parallel)

### Step 2.1: Read References

Read these files (paths relative to plugin root):
- `agents/spec-code-reviewer.md`
- `agents/code-spec-reviewer.md`
- `references/spec-alignment-rubric.md`
- `references/output-format.md` (Spec-Alignment section)

### Step 2.2: Execute Pairs (per batch)

For each spec-code pair in the current batch:

1. Read the spec-card YAML
2. Read the associated code file(s) (resolve globs from spec-index)
3. Read the original rule document (for SOURCE link fallback)

Launch 2 sub-agents per pair in a single message:

```
- Spec→Code Agent: subagent_type: "generalPurpose", readonly: true, run_in_background: true
  description: "Spec→Code: {doc-name}"
  prompt: [spec-code-reviewer.md] + [spec-card content] + [code files] + [rubric] + [output-format] + [original doc path for fallback]

- Code→Spec Agent: subagent_type: "generalPurpose", readonly: true, run_in_background: true
  description: "Code→Spec: {doc-name}"
  prompt: [code-spec-reviewer.md] + [code files] + [spec-card content] + [output-format]
```

For Code→Spec Agent, prefer a lighter/faster model if available.

**Attention limit**: If a code file associates with > 2 spec-cards, split into multiple reviewer tasks (max 2 spec-cards per reviewer).

### Step 2.3: Batch Progress

After each batch completes:
1. Report intermediate results to user (marked as "未去重"):
   ```
   Batch 1/3 完成：
   - {doc-a}: 2 DRIFT, 1 MISSING
   - {doc-b}: 0 findings
   - {doc-c}: 1 UNDOCUMENTED
   ```
2. Update `CheckRulesTasks.md` status → `done` for completed pairs
3. Proceed to next batch (or allow user to interrupt)

**On user interrupt**: mark remaining batches as `skipped`, proceed to Phase 3 with available findings.

**On single Agent failure**: note in report, continue with other Agent's results.

---

## Phase 3: Merge & Verify

### Step 3.1: Merge & Deduplicate (Orchestrator does this directly)

1. **Same-pair merge**: If both Spec→Code and Code→Spec flagged the same code location with the same issue → merge into 1 finding (keep richer evidence)
2. **Cross-document merge**: If findings from different rule docs point to the same code location or same config/function → merge, annotate "影响 N 份规格文档", tag "可能共享根因"
3. **Different types don't merge**: DRIFT + UNDOCUMENTED on same location → keep both

### Step 3.2: Assign Type Labels

Each finding gets exactly one type: DRIFT / MISSING / UNDOCUMENTED / STALE

### Step 3.3: Format Standardization

Ensure every finding has all required fields per `references/output-format.md` (Spec-Alignment section):
- ID: `R{NNN}` sequential
- Type, Rule Document, File, Line, Snippet, Description, Evidence, Source Agent

### Step 3.4: Launch Verifier

Read `agents/spec-verifier.md`.

If there are findings to verify, launch 1 Verifier sub-agent:

```
- Verifier: subagent_type: "generalPurpose", readonly: true, run_in_background: true
  description: "Spec Verifier"
  prompt: [spec-verifier.md] + [all findings] + [original rule document contents for each cited SOURCE]
```

**On Verifier failure**: skip verification, output all findings without confidence scores, note "未经 Verifier 校验" in report.

### Step 3.5: Apply Threshold

Default threshold: 80 (configurable in REVIEW.md `Configuration` section as `rules_confidence_threshold`).

- Findings with confidence ≥ threshold → include in final report
- Findings with confidence < threshold → record in history but exclude from main report
- Rejected findings → exclude entirely, note count in report

### Step 3.6: Persist to .checks/

**Initialize directories** (if they don't exist): `.checks/`, `.checks/history/`, `.checks/changes/`

**Determine run number:**
- Scan `.checks/history/` for files matching `rules\d{3}-.*\.md`
- Next number = highest found + 1 (or 1 if none). Zero-pad to 3 digits.

**Write history file** (`.checks/history/rules{NNN}-{label}.md`):

```markdown
# Check-Rules Run {NNN}

**Date**: {timestamp}
**Scope**: {spec-code pairs checked}
**Mode**: rules
**Reviewers**: Spec→Code ({N}), Code→Spec ({N}), Verifier ({passed}/{rejected})

## Findings (Above Threshold)

[All findings passing threshold, in spec-alignment output format]

## Below Threshold

[Findings below threshold, for reference]

## Rejected by Verifier

[Count and brief summary of rejected findings]
```

**Update session.md:**

If `.checks/session.md` doesn't exist, create with standard header (same as `/check` but including Type column).

Add new findings with `Type=spec`, `Status=open`, source `rules`.

**Update changes/{label}.md:**

Append to Review History table: `| rules{NNN} | {date} | {finding_count} | {drift_count} | 0 |`
Set Mode to `rules` in the row.

---

## Phase 4: Final Report

Output:

```
## Check-Rules Results

**Scope**: {N} 份规则文档 × 代码
**Change**: {label}
**Agents**: Spec→Code ({N} findings), Code→Spec ({N} findings)
**Verifier**: {N} passed, {N} rejected, threshold={T}
[If any agent failed: "⚠ {Agent} 未返回结果 — 覆盖不完整"]
[If CheckRulesTasks.md exists: "进度: {done}/{total} 对完成"]

### DRIFT (代码与文档不一致)
[Findings of type DRIFT, if any. Otherwise "None."]

### MISSING (文档描述了但代码未实现)
[Findings of type MISSING, if any. Otherwise "None."]

### UNDOCUMENTED (代码行为未被文档描述)
[Findings of type UNDOCUMENTED, if any. Otherwise "None."]

### STALE (已知差异待评估)
[Findings of type STALE, if any. Otherwise "None."]

### Session Update
[Run NNN saved. N new issues, N below threshold, N rejected.]

### Next Steps
[Actionable recommendations]
```

Each finding displays:
- **ID**: R{NNN} — **Type**: {type}
- **Rule Document**: {SOURCE link}
- **File**: {path} — **Line**: {range}
- **Snippet**: `{code}`
- Description
- **Confidence**: {score} — **Source**: {agent}

If zero total findings: "**No findings.** 代码与规格文档一致。"

---

## Parameters

| Parameter | Effect |
|-----------|--------|
| `--refresh` | Force re-extraction of specified spec-cards |
| `--refresh-all` | Force re-extraction of ALL spec-cards |
| `--all` | Check all rule documents in spec-index (ignore dirty file matching) |
| `--threshold N` | Override confidence threshold (default 80) |

---

## Error Handling

- Single sub-agent failure: continue with remaining agents, note in report
- All agents in a pair fail: mark pair as `skipped`, continue to next pair
- Verifier failure: output findings without confidence scores
- spec-index.md invalid: report specific validation errors, stop
- No matching rule documents: report and suggest checking spec-index.md
