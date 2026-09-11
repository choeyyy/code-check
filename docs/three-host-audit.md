# 三端兼容审计 — 2026-09-11

范围由用户确认：TOOL-SKILLS main/other、GitHub choeyyy/skill-creator、choeyyy/code-check。

| 范围 | 发现 | 处理 |
|---|---|---|
| BF-TOOLS CursorSessions | Cursor 专用且用户要求废弃 | 删除主分支及 other 分支源；删除本地源和 Claude 安装副本；其余宿主无该目录 |
| BF-TOOLS recall | Cursor 模型表、Task 参数、最新日志误认当前会话 | 显式 --host；Codex/Claude inherit；不再由 Cursor 最新日志推断当前会话；无代理记录 manual 来源 |
| BF-TOOLS ProblemReport | Cursor 日志格式和可选旧技能依赖 | 明确 provider/input 的三端解析归档；移除旧调用；main 保留完整台账，other 保留较早的问题报告范围 |
| BF-TOOLS pipeline prompt (main only) | AskQuestion 必须存在与固定 .cursor/skills 路径 | 使用可用提问能力和实际安装路径；保留发布前确认 |
| skill-creator / SKILL-RELATED | Cursor 安装和派发示例 | 三端自包含安装、宿主工具映射、保持原有审批和证据标准；兼容原 Codex lint 安装器 |
| code-check / CODE-CHECK | Task 并行、模型 id 与 Cursor 安装绑定 | 三端安装；只传宿主支持的参数；并发不足排队，无独立代理时不伪称独立评测通过 |
| GitHub code-check session-cil | 会话查询默认 Cursor 日志 | 保留兼容名称，增加 Codex/Claude 明确文件路线；Cursor 目录扫描只用于 Cursor 数据 |

Cursor 的 plugin.json、bootstrap 和既有 setup 安装逻辑保留为 Cursor 适配。
另提供 Python install_hosts.py；不把三端运行支持误写成三端插件市场格式相同。

验证覆盖合成的三类真实格式记录、缺失子日志阻断、非法记录拒绝、输出目录保护、安装资源完整和覆盖冲突。
没有读取真实私有会话，没有声称完成三款宿主的实际模型端到端运行。
Windows 不允许测试进程创建符号链接，该项测试标记 skipped；其余测试执行结果见测试输出。
