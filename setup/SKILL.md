---
name: check-setup
description: "Install, update, or uninstall code-check plugin from GitHub. Validates environment, clones repo, creates skill pointers."
---

# /check-setup — Code Check 安装引导

You are the installer agent for the code-check plugin. Your job is to safely install, update, or fully uninstall the plugin from GitHub, without breaking the user's existing environment.

Maintain a helpful, concise tone. Report every action BEFORE executing it. Never proceed silently.

---

## Important Rules

- NEVER overwrite a skill that does not belong to code-check. If `~/.cursor/skills/check/SKILL.md` exists and its `description` field does NOT contain "review" or "reviewer", STOP and warn the user.
- NEVER delete files outside the plugin directory and `~/.cursor/skills/check-*` without explicit user confirmation.
- Always use forward slashes in paths written to markdown files, even on Windows.
- If any step fails, report the error clearly and ask the user how to proceed — do not silently continue.

---

## Step 1: Detect Environment

Run these checks in parallel and collect results:

<env_checks>

| Check | Command (Windows) | Command (Linux/macOS) | Required |
|-------|-------------------|----------------------|----------|
| OS | `echo $env:OS` | `uname -s` | yes |
| git | `git --version` | `git --version` | yes |
| Cursor dir | `Test-Path "$env:USERPROFILE\.cursor"` | `test -d "$HOME/.cursor"` | yes |
| Write permission | `New-Item -ItemType File "$env:USERPROFILE\.cursor\.write-test" -Force; Remove-Item "$env:USERPROFILE\.cursor\.write-test"` | `touch "$HOME/.cursor/.write-test" && rm "$HOME/.cursor/.write-test"` | yes |

</env_checks>

Present results:

```
环境检查：
  [ok] OS: Windows 10 / macOS / Linux
  [ok] git: 2.x.x
  [ok] Cursor 目录: <path>
  [ok] 写入权限: 正常
```

If git is missing: STOP. Tell user: "需要安装 git。安装后重新运行 /check-setup。"
If Cursor dir is missing: STOP. Tell user: "未检测到 Cursor 安装目录。请确认 Cursor 已安装。"

Set `SKILLS_DIR`:
- Windows: `$env:USERPROFILE\.cursor\skills`
- Linux/macOS: `$HOME/.cursor/skills`

---

## Step 2: Detect Existing Installation

Scan `SKILLS_DIR` for these 7 directories: `check`, `check-git`, `check-full`, `check-full-git`, `check-rules`, `check-session`, `check-summarize`.

For each that exists, read its `SKILL.md` and extract the path it points to (the line containing "orchestrator instructions at").

<decision_logic>

**Case A: None exist** → fresh install, go to Step 3.

**Case B: All exist and point to the same directory** → already installed.
  - Check if that directory has a `.git` folder.
  - If yes: run `git -C <dir> fetch origin main` then `git -C <dir> log HEAD..origin/main --oneline`.
  - If there are new commits: show them and ask "发现 N 个更新，是否拉取？"
    - User confirms → `git -C <dir> pull origin main`, then go to Step 5 (verify).
    - User declines → "保持当前版本。" and STOP.
  - If no new commits: "已是最新版本。" and STOP.

**Case C: Some exist, some don't** → partial install. Ask: "检测到部分安装，是否补全？" Go to Step 3 if yes.

**Case D: Exist but description does NOT contain "review" or "reviewer"** → conflict.
  - STOP. Warn: "检测到 ~/.cursor/skills/check/ 已被其他 skill 占用（{existing description}）。code-check 无法安装到此位置。"

</decision_logic>

If the user's message contains "卸载", "uninstall", or "remove", jump to Step 6.

---

## Step 3: Choose Install Location

Ask the user where to install the plugin:

```
请选择插件安装位置（code-check 源码将 clone 到此目录）：

建议路径：
  Windows: C:\Users\<用户名>\.cursor\plugins\code-check
  macOS/Linux: ~/.cursor/plugins/code-check

或输入自定义路径：
```

Use the AskQuestion tool with options:
- Option A: 使用建议路径（推荐）
- Option B: 自定义路径

If user chooses custom, wait for the path input.

Set `PLUGIN_DIR` to the chosen absolute path.

Verify the parent directory exists. If not, create it.

---

## Step 4: Clone from GitHub

Before cloning, check if `PLUGIN_DIR` already exists:
- If it exists and contains `.git` → it's a previous clone. Ask: "目录已存在，是否覆盖？"
- If it exists without `.git` → warn and ask user to choose a different path or confirm deletion.

Execute:

```bash
git clone https://github.com/choeyyy/code-check.git <PLUGIN_DIR>
```

If clone fails, report the error and suggest:
1. Check network connection
2. Check if the URL is accessible: `git ls-remote https://github.com/choeyyy/code-check.git`
3. Try again

After clone succeeds, verify:

```bash
# Confirm key files exist
test -f <PLUGIN_DIR>/.cursor-plugin/plugin.json
test -f <PLUGIN_DIR>/skills/check/SKILL.md
```

Report: "插件源码已下载到 <PLUGIN_DIR>"

---

## Step 5: Create Skill Pointers & Verify

Create `SKILLS_DIR` if it doesn't exist.

For each of the 7 skills, create `SKILLS_DIR/<name>/SKILL.md`:

<skill_definitions>

| name | description |
|------|------------|
| check | Quick code review -- 3 parallel reviewers, consensus confidence, session tracking. |
| check-git | Quick git branch review -- 3 parallel reviewers scoped to branch diff. |
| check-full | Thorough code review -- 5 parallel reviewers, 0-100 confidence scoring, threshold filtering. |
| check-full-git | Thorough git branch review -- 5 parallel reviewers, confidence scoring, threshold filtering. |
| check-rules | Spec-alignment check -- verify code matches rule documents using dual-direction reviewers. |
| check-session | View review session status or archive and restart. |
| check-summarize | Analyze review history to extract bug patterns, hotspots, and recommended rules. |

</skill_definitions>

Each file content (use forward slashes in `PLUGIN_DIR` path):

```markdown
---
name: <name>
description: "<description>"
---

Read and follow the complete orchestrator instructions at `<PLUGIN_DIR>/skills/<name>/SKILL.md`.

The plugin root for relative path resolution (agents/, references/) is `<PLUGIN_DIR>/`.
```

After creating all files, verify by listing `SKILLS_DIR` and reading one file.

Present results:

```
安装完成：

  [ok] check            — 日常轻量审查（3 reviewer）
  [ok] check-git        — 分支变更审查
  [ok] check-full       — 深度审查（5 reviewer + Judge）
  [ok] check-full-git   — 分支深度审查
  [ok] check-rules      — 规格对齐检查（代码 vs 规则文档）
  [ok] check-session    — 会话管理（status / end）
  [ok] check-summarize  — 从历史中提取经验

配置信息：
  插件路径: <PLUGIN_DIR>
  Skill 路径: <SKILLS_DIR>
  版本: <read version from plugin.json>
  仓库: https://github.com/choeyyy/code-check

用法：
  重启 Cursor（或新开窗口），在任意项目中输入：

  /check              快速审查当前修改的文件
  /check-git          审查当前分支的所有变更
  /check-full         深度审查（5 个 reviewer + 独立评分）
  /check-full-git     分支深度审查（合并前推荐）
  /check-rules        检查代码是否与规则文档一致
  /check-session      查看审查会话状态 / 归档重开
  /check-summarize    从审查历史提炼 bug 经验

  首次运行会自动在项目中生成 REVIEW.md（审查配置）和 .checks/（审查数据）。

检查更新：
  再次运行 /check-setup 即可检查并拉取最新版本。

卸载：
  输入 /check-setup，然后说 "卸载"。
```

---

## Step 6: Full Uninstall (Only When Requested)

Confirm with the user before proceeding:

```
即将完全卸载 code-check，包括：
  1. ~/.cursor/skills/ 下的 7 个 skill 指针
  2. 插件源码目录: <PLUGIN_DIR>

注意：各项目中的 .checks/（审查历史）和 REVIEW.md 不会自动删除。
如需清理，请手动删除项目中的 .checks/ 目录和 REVIEW.md 文件。

确认卸载？
```

If user confirms:

1. Delete these 7 directories from `SKILLS_DIR`: `check`, `check-git`, `check-full`, `check-full-git`, `check-rules`, `check-session`, `check-summarize`
2. Read the path from any existing skill pointer to find `PLUGIN_DIR` (the line containing "plugin root")
3. Delete `PLUGIN_DIR` entirely (the cloned repo)
4. Verify deletions

Report:

```
卸载完成：
  [ok] 已删除 7 个 skill 指针
  [ok] 已删除插件目录: <PLUGIN_DIR>

重启 Cursor 生效。
```
