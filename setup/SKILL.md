---
name: check-setup
description: "Install or uninstall code-check plugin — auto-detect paths, create skill pointers, verify installation."
---

# /check-setup — Code Check 安装引导

You are the installer for the code-check plugin. Guide the user through installation or uninstallation.

Follow these steps in order.

---

## Step 1: Detect Environment

1. Determine the OS: run `echo $env:OS` (PowerShell) or `uname -s` (bash). This tells you whether to use PowerShell or bash syntax.

2. Find the plugin directory. Search for `code-check/.cursor-plugin/plugin.json` in likely locations:
   - The current workspace root and its subdirectories (check `cursor-plugins/code-check/`, `code-check/`)
   - Common tool directories

   If not found, ask the user: "Where is the code-check plugin directory? (the folder containing `.cursor-plugin/plugin.json`)"

3. Set `PLUGIN_DIR` to the absolute path of the code-check directory.

4. Set `SKILLS_DIR`:
   - Windows: `$env:USERPROFILE\.cursor\skills`
   - Linux/macOS: `$HOME/.cursor/skills`

5. Tell the user what was detected:
   ```
   Detected:
   - OS: <os>
   - Plugin: <PLUGIN_DIR>
   - Skills: <SKILLS_DIR>
   ```

## Step 2: Check Existing Installation

List the contents of `SKILLS_DIR`. Check if any of these directories already exist:
`check`, `check-git`, `check-full`, `check-full-git`, `check-rules`, `check-session`, `check-summarize`

If some exist, read their `SKILL.md` files and check if the paths inside match `PLUGIN_DIR`.

Report status:
- "Already installed (current path)" — skip
- "Installed but pointing to different path" — will update
- "Not installed" — will create

Ask the user to confirm: "Proceed with installation?" (or "Update paths?" if already installed with different path)

If the user wants to uninstall, jump to Step 5.

## Step 3: Create Skill Pointer Files

For each of the 7 skills, create `SKILLS_DIR/<name>/SKILL.md` with this exact content (replace `<name>`, `<description>`, and paths):

```markdown
---
name: <name>
description: "<description>"
---

Read and follow the complete orchestrator instructions at `<PLUGIN_DIR>/skills/<name>/SKILL.md`.

The plugin root for relative path resolution (agents/, references/) is `<PLUGIN_DIR>/`.
```

Use forward slashes in paths (even on Windows) for markdown compatibility.

Skill definitions:

| name | description |
|------|------------|
| check | Quick code review -- 3 parallel reviewers, consensus confidence, session tracking. |
| check-git | Quick git branch review -- 3 parallel reviewers scoped to branch diff. |
| check-full | Thorough code review -- 5 parallel reviewers, 0-100 confidence scoring, threshold filtering. |
| check-full-git | Thorough git branch review -- 5 parallel reviewers, confidence scoring, threshold filtering. |
| check-rules | Spec-alignment check -- verify code matches rule documents using dual-direction reviewers. |
| check-session | View review session status or archive and restart. |
| check-summarize | Analyze review history to extract bug patterns, hotspots, and recommended rules. |

Create directories and write files using shell commands.

## Step 4: Verify Installation

1. List `SKILLS_DIR` and confirm all 7 directories exist.
2. Read one of the created files to verify content is correct.
3. Report results:

```
Installation complete:

  [ok] check
  [ok] check-git
  [ok] check-full
  [ok] check-full-git
  [ok] check-rules
  [ok] check-session
  [ok] check-summarize

Restart Cursor (or open a new window) to activate.

Available commands:
  /check            — 日常轻量审查（3 reviewer）
  /check-git        — 分支变更审查
  /check-full       — 深度审查（5 reviewer + Judge）
  /check-full-git   — 分支深度审查
  /check-rules      — 规格对齐检查（代码 vs 规则文档）
  /check-session    — 会话管理（status / end）
  /check-summarize  — 从历史中提取经验
```

## Step 5: Uninstall (Only if Requested)

Remove all 7 skill directories from `SKILLS_DIR`:

```
check, check-git, check-full, check-full-git, check-rules, check-session, check-summarize
```

Confirm each removal. Report: "Uninstall complete. Restart Cursor to take effect."
