---
name: /check-rules
id: check-rules
category: Code Review
description: Spec-alignment check — verify code matches rule documents
---

Run a spec-alignment check to verify code matches project rule documents.

**Prerequisites**: `spec-index.md` in project root (auto-generated on first run).

**Parameters**:
- `--refresh`: re-extract specified spec-cards
- `--refresh-all`: re-extract all spec-cards
- `--all`: check all rule documents (ignore dirty file matching)
- `--threshold N`: override confidence threshold (default 80)

Read and follow the skill at `D:\SOFT\TOOLS\cursor-plugins\code-check\skills\check-rules\SKILL.md`.
The plugin root for relative path resolution is `D:\SOFT\TOOLS\cursor-plugins\code-check\`.
