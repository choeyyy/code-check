# Host capabilities: Cursor, Codex, Claude Code

This document adapts tool invocation, not task scope, approval, evidence, or quality rules.

| Capability | Cursor | Codex | Claude Code |
|---|---|---|---|
| Load a skill | Installed SKILL.md | Installed SKILL.md, explicit $name | Installed SKILL.md, explicit /name |
| Ask a question | Available question tool | Available question tool, or plain chat when unavailable | Available question tool, or plain chat |
| Delegate | Available Task/agent tool | Available subagent tool | Available Agent/Task tool |
| Read/edit/run | Current host's file and shell tools | Current host's file and shell tools | Current host's file and shell tools |

Before invoking any tool, inspect the current host's exposed schema. Task, AskQuestion,
subagent_type, readonly, run_in_background, resume and model literals in legacy examples
are capability descriptions, not portable API arguments. Map only supported arguments.
Never invent a tool, model id or model alias. Inherit the host model unless the user has
selected an available override; explain an unavailable explicit choice and ask for a replacement.
Preserve a requested read-only boundary through instructions and available restrictions.
Use the actual returned agent id for retries; do not assume another host's id format.

Independent reviews may run concurrently up to the host limit; queue remaining reviews.
If delegation is unavailable, say so and execute the same review roles sequentially,
recording that they were not independent agents. For evals requiring independent agents,
mark that measurement unperformed; do not report a simulated multi-agent pass.
Do not create a new user-visible task or use an external model service as an implicit fallback.
A question tool missing does not waive approval: ask in chat and wait when approval is required.

Use the current skill root and actual installed dependencies, never assume ~/.cursor/skills.
Resolve project instructions for the current host (AGENTS.md / CLAUDE.md / applicable rules).
Cursor plugin manifests and bootstrap/setup commands describe Cursor installation only.
For all three hosts use scripts/install_hosts.py with an explicit --host; legacy setup
skills must route to that installer on Codex/Claude, not create Cursor registrations.
Tool-specific log readers/settings remain labelled by their data source; running from Codex
or Claude does not turn Cursor logs into the current host's logs. Choose the provider explicitly.
