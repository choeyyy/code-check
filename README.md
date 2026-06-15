# Code Check

多代理代码审查工具，支持置信度评分、会话追踪和可定制审查规则。

## 快速安装

### 方式一：脚本安装（推荐）

将本目录放到任意位置，然后运行安装脚本。脚本会自动检测路径并创建 Skill 指针文件。

**Windows (PowerShell)**：

```powershell
cd <code-check 所在目录>
.\install.ps1
```

**Linux / macOS**：

```bash
cd <code-check 所在目录>
bash install.sh
```

安装完成后重启 Cursor，即可在任意工作区使用 `/check` 系列命令。

**卸载**：

```powershell
.\install.ps1 -Uninstall        # Windows
bash install.sh --uninstall     # Linux/macOS
```

### 方式二：Cursor 内安装

在 Cursor 对话中输入 `/check-setup`，Agent 会引导你完成安装（需要先将本目录中的 `setup/SKILL.md` 复制到 `~/.cursor/skills/check-setup/SKILL.md`）。

### 方式三：手动安装

1. 将本目录放到一个固定位置（安装后不要移动）

2. 为每个命令在 `~/.cursor/skills/` 下创建 Skill 指针文件，格式如下：

**`~/.cursor/skills/check/SKILL.md`**（其他命令同理，替换 name 和路径）：

```markdown
---
name: check
description: "Quick code review — 3 parallel reviewers, consensus confidence, session tracking."
---

Read and follow the complete orchestrator instructions at `<你的路径>/code-check/skills/check/SKILL.md`.

The plugin root for relative path resolution (agents/, references/) is `<你的路径>/code-check/`.
```

需要创建的 7 个 Skill 指针：

| 目录名 | 对应 Skill |
|--------|-----------|
| `check/` | 日常轻量审查 |
| `check-git/` | 分支变更审查 |
| `check-full/` | 深度审查 |
| `check-full-git/` | 分支深度审查 |
| `check-rules/` | 规格对齐检查 |
| `check-session/` | 会话管理 |
| `check-summarize/` | 经验总结 |

3. 重启 Cursor 或新开窗口

## 插件结构

```
code-check/
├── .cursor-plugin/plugin.json   ← 插件元数据
├── skills/                      ← 编排器（实际逻辑）
│   ├── check/SKILL.md
│   ├── check-git/SKILL.md
│   ├── check-full/SKILL.md
│   ├── check-full-git/SKILL.md
│   ├── check-rules/SKILL.md
│   ├── check-session/SKILL.md
│   └── check-summarize/SKILL.md
├── agents/                      ← 子代理角色 prompt
├── references/                  ← 审查标准（rubric, 误报清单, 输出格式）
├── setup/SKILL.md               ← Cursor 内安装引导 Skill
├── install.ps1                  ← Windows 安装脚本
├── install.sh                   ← Linux/macOS 安装脚本
└── README.md
```

### 运行时产物

首次在某个项目中运行 `/check` 时，会在**该项目根目录**自动创建：

```
<项目根>/
├── REVIEW.md            ← 项目审查配置（首次自动生成，可编辑）
└── .checks/
    ├── .gitignore       ← 默认排除 git 追踪
    ├── session.md       ← 当前会话 Issue 追踪
    ├── history/         ← 每次 check 的完整记录
    ├── changes/         ← 按变更维度聚合（跨 session 保留）
    └── lessons.md       ← check-summarize 生成的经验总结
```

---

## 命令一览

| 命令 | 用途 |
|------|------|
| `/check` | 快速本地审查 |
| `/check-git` | 快速分支审查 |
| `/check-full` | 深度本地审查 |
| `/check-full-git` | 深度分支审查 |
| `/check-rules` | 规格对齐检查（代码 vs 规则文档） |
| `/check-session status` | 查看会话状态 |
| `/check-session end` | 归档当前会话并重开 |
| `/check-summarize` | 从历史中提取 Bug 经验 |

---

## /check-rules — 规格对齐检查

验证代码实现是否与项目规则文档一致。与 `/check` 系列（通用代码质量）独立互补。

### 前置条件

- 项目根目录存在 `spec-index.md`（规则文档→代码文件映射表）
- 首次运行时如不存在，会自动生成草稿供确认

### 参数

| 参数 | 说明 |
|------|------|
| `--refresh` | 强制重新提炼指定 spec-card |
| `--refresh-all` | 强制重新提炼全部 spec-card |
| `--all` | 检查所有规则文档（忽略 dirty file 匹配） |
| `--threshold N` | 覆盖置信度阈值（默认 80） |

### 运行时产物

```
<项目根>/
├── spec-index.md          ← 规则文档→代码映射（用户维护）
├── spec-card/             ← AI 提炼的断言缓存（自动生成）
│   ├── feature-a.yaml
│   └── feature-b.yaml
├── CheckRulesTasks.md     ← 批次进度追踪（>3 对时生成，运行后可删）
└── .checks/
    └── history/rules{NNN}-{label}.md  ← 每次运行记录
```

### Finding 类型

| 类型 | 含义 |
|------|------|
| DRIFT | 代码实现与文档断言不一致 |
| MISSING | 文档描述了但代码未实现 |
| UNDOCUMENTED | 代码有行为但文档未描述 |
| STALE | 已知差异标注"待评估"长期未更新 |

详细用法见 `D:\SOFT\TOOLS\NOTE\USAGE\code-check.md`。
