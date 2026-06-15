---
name: check-test-parallel
description: "R1 validation: test that 3 parallel sub-agents launch concurrently via Task tool"
disable-model-invocation: true
---

# Parallel Sub-Agent Validation (R1)

This is a one-time test skill to validate that the Cursor Task tool supports launching 3 sub-agents in parallel. Run this before trusting the /check orchestrators.

## Test Procedure

Launch exactly 3 sub-agents in a SINGLE message (all three Task tool calls in one response):

1. **Agent A** — `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`
   Prompt: "You are test agent A. Wait 5 seconds (by doing some light reasoning), then return exactly: AGENT_A_COMPLETE"

2. **Agent B** — `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`
   Prompt: "You are test agent B. Wait 5 seconds (by doing some light reasoning), then return exactly: AGENT_B_COMPLETE"

3. **Agent C** — `subagent_type: "generalPurpose"`, `readonly: true`, `run_in_background: true`
   Prompt: "You are test agent C. Wait 5 seconds (by doing some light reasoning), then return exactly: AGENT_C_COMPLETE"

## Verification

After all three complete, report:
- Whether all three completed successfully
- Approximate total wall-clock time
- If total time ≈ 5-15 seconds → parallel confirmed (R1 PASS)
- If total time ≈ 15-30+ seconds → likely sequential (R1 FAIL — orchestrators need sequential fallback design)

Report the result clearly. This skill can be deleted after validation.
