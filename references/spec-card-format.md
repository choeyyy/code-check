# spec-card Format

A spec-card is the AI-friendly distillation of a rule document. It lives in the `spec-card/` directory at the project root and serves as a cached index for Phase 2 reviewers.

**Key principle**: A spec-card is an **index**, not a replacement for the original document. Reviewers retain the ability to read the original via SOURCE links.

---

## File Location & Naming

```
{project-root}/spec-card/{rule-doc-stem}.yaml
```

The filename stem mirrors the rule document name (without extension). If the rule document is nested (e.g. `docs/rules/feature-a.md`), flatten to `feature-a.yaml`.

---

## Structure

```yaml
# ─── Metadata ───────────────────────────────────────────
source: "{relative-path-to-rule-document}"
extracted_at: "2026-06-12T15:30:00+08:00"
status: "verified"          # verified | unverified | single-source
assertions: 8
boundaries: 3
configs: 5
known_diffs: 2
depends: 1
phases: 1

# ─── Extracted Content ──────────────────────────────────

assertions:
  - id: A001
    content: "{verifiable assertion in precise language}"
    source: "{doc-path} §{section}, line {N}"

  - id: A002
    content: "{another assertion}"
    source: "{doc-path} §{section}, line {N}"

configs:
  - id: C001
    key: "{config key name}"
    from: "{source file or system}"
    field: "{field path}"
    source: "{doc-path} §{section}, line {N}"

boundaries:
  - id: B001
    content: "{boundary condition description}"
    source: "{doc-path} §{section}, line {N}"

known_diffs:
  - id: K001
    content: "{description of known difference}"
    status: "confirmed"     # confirmed | pending-review
    impact: "{impact description}"
    source: "{doc-path} §{section}, line {N}"

depends:
  - id: D001
    concept: "{referenced concept name}"
    defined_in: "{other-doc-path} §{section}"
    source: "{doc-path} §{section}, line {N}"

phases:
  - id: P001
    stage: "{execution stage/phase name}"
    defined_in: "{state-machine-doc-path} §{section}"
    source: "{doc-path} §{section}, line {N}"
```

---

## Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Relative path to the source rule document |
| `extracted_at` | ISO 8601 | When this spec-card was generated |
| `status` | enum | `verified` (dual-summarizer + human reviewed), `unverified` (not yet reviewed), `single-source` (one summarizer failed) |
| `assertions` | int | Count of ASSERT entries |
| `boundaries` | int | Count of BOUNDARY entries |
| `configs` | int | Count of CONFIG entries |
| `known_diffs` | int | Count of KNOWN-DIFF entries |
| `depends` | int | Count of DEPENDS entries |
| `phases` | int | Count of PHASE entries |

---

## SOURCE Field Format

Every extracted item MUST include a `source` field linking back to the original document:

```
{relative-doc-path} §{section-number-or-name}, line {line-number}
```

- Path: project-root relative, forward slashes
- Section: `§` followed by section number or heading name
- Line: single line number or range (`line 12` or `line 12-15`)

For documents without clear section structure, omit the section: `{path}, line {N}` or `{path}, line {N}-{M}`.

---

## ID Generation

Each extracted item gets a prefixed sequential ID within its category:

| Category | Prefix | Example |
|----------|--------|---------|
| Assertion | A | A001, A002 |
| Config | C | C001, C002 |
| Boundary | B | B001, B002 |
| Known Diff | K | K001, K002 |
| Depends | D | D001, D002 |
| Phase | P | P001, P002 |
