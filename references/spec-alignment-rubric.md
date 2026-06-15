# Spec-Alignment Review Rubric

This rubric defines what `/check-rules` reviewers check and — equally important — what they do NOT check.

---

## Check Dimensions

### 1. Algorithm Consistency

Does the code implement the algorithms/formulas described in the spec?

- Formula correctness (operators, operands, order of operations)
- Algorithmic steps (correct sequence, correct branching)
- Mathematical relationships (inequalities, thresholds, multipliers)

### 2. Configuration Reference Consistency

Does the code reference the correct configuration sources?

- Config key names match spec description
- Config source files/systems match spec description
- Default values match spec description (if stated)
- Config field paths match spec description

### 3. Boundary Handling Coverage

Does the code handle the edge cases described in the spec?

- Stated boundary conditions have corresponding code guards
- Boundary handling behavior matches spec requirements
- Failure modes match spec (clamp, reject, default, etc.)

### 4. Known-Diff Timeliness

Are documented known-differences still being tracked?

- `pending-review` entries that haven't been addressed → STALE
- `confirmed` entries are acknowledged — not reported as findings

### 5. Undocumented Behavior Discovery

Does the code have significant behaviors not described in any spec?

- Public API surface without spec coverage
- Business logic branches without spec coverage
- Configuration-driven behavior without spec coverage

---

## NOT Checked (Out of Scope)

The following are explicitly NOT reported by `/check-rules` reviewers:

| Category | Reason | Handled By |
|----------|--------|------------|
| Bugs (null deref, race conditions) | Code quality issue, not spec alignment | `/check` bug-reviewer |
| Code style (naming, formatting) | Style issue | `/check` standards-reviewer |
| Architecture (coupling, patterns) | Design concern | `/check` quality-reviewer |
| Performance | Optimization concern | `/check` quality-reviewer |
| Security vulnerabilities | Security issue | `/check` bug-reviewer |
| Test coverage | Testing concern | Out of scope for all current commands |

**Rule**: If a finding is about "code is broken" rather than "code doesn't match what the document says", it belongs in `/check`, not `/check-rules`.

---

## Finding Quality Standards

A valid spec-alignment finding MUST have:

1. **Specific assertion reference**: Which exact spec-card entry is violated (by ID)
2. **Specific code location**: File path + line number where the discrepancy occurs
3. **Clear discrepancy description**: What the spec says vs what the code does
4. **SOURCE traceability**: Link back to the original rule document location

A finding WITHOUT all four elements should not be reported.

---

## Confidence Guidance

| Signal | Effect on Confidence |
|--------|---------------------|
| Spec uses precise numbers/formulas that code clearly violates | High confidence |
| Spec is ambiguous but code seems to contradict intent | Medium confidence |
| Spec uses vague language ("should handle edge cases") | Low confidence — likely not worth reporting |
| Code implements behavior spec doesn't mention | Depends on behavior significance |
