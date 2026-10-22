# 更新记录

每个版本的完整说明见 [GitHub Releases](https://github.com/rumoii/rumo-engineering-skills/releases)。插件用户只在 `.claude-plugin/plugin.json` 的 `version` 提升后才会收到更新，所以每次发版都要提升版本号，并在这里补一节。

## 未发布

- `rumo-agent-collaboration`：判断子 agent 能否使用时，依据当前会话实际加载的工具、扩展、启动参数和权限，区分可用、已安装未加载、本次调用禁用、确认不存在和未确认；不再凭 CLI 名称、版本或已安装的包下结论，父会话只读也不能证明子 agent 只读。pi 适配器的 `--no-extensions` 会让已安装的子 agent 扩展在本次调用中不可用，这是启动限制，不是 pi 没有子 agent。
- `rumo-agent-collaboration`：委派后优先等客户端的完成通知；通知不到时（客户端不能通知，或对方在 Orca 终端、后台会话、用户自开的终端里运行），可以启动后结束本轮、仍作负责人，并告诉用户对方在哪里运行、结果在哪里读、做完后说什么。用户说完成后，先读结果、核对工作区再采纳。
- 评测：pi 运行器（行为与触发）加载新扩展 `scripts/pi_workspace_guard.mjs`。pi 没有沙箱，只读工具也能访问任意路径；该扩展在执行前拦截样本工作区以外的路径，以及只读四个工具以外的工具。如果仍有越界调用执行成功，这次运行判为无效。
- 校验：每条 description 不超过 100 词；技能文档中反引号里的 `scripts/...` 路径必须在该技能目录内存在；每个允许模型自动选用的默认技能至少要有一个触发用例，并为 `rumo-project-profile` 补了用例。`rumo-prose` 的 agent 文档规范不再引用本仓库的测试路径。
- `rumo-agent-collaboration`：description 从 132 词精简到约 90 词，只保留触发场景、示例说法和与邻近技能的分界；外部 CLI 评审时明确要求同时加载 rumo-review，正文也要求写评审 brief 前先读它。新增 3 个触发用例：委派给点名的 CLI、客户端自带子 agent 不触发、外部 CLI 评审同时加载 rumo-review。
- 评测：新增 `scripts/run_pi_trigger.py`，用 pi 和任意可用模型跑 evals/ 的触发用例，作为改 description 前的低成本筛查；只加载样本里的技能，关闭 context files 和 MCP。结果不能代替 Claude 或 Codex 的结论。

## 0.5.0 - 2026-10-21

- `rumo-review`：新增评审结论取舍规则，适用于独立评审、评审机器人和他人意见；经用户同意后，可以调用本机另一个 CLI 做跨模型只读复审。
- `rumo-git-commit`：用户明确要求时，可跟进已开 PR 的 CI 检查。等待期间不轮询；修复前先给失败分类；修好后提交、推送仍需用户明确要求；不合并 PR，也不标记 ready。
- `rumo-plan`：出方案时，各选项须在结构上真正不同，并对照三类设计问题自查。
- 新增扩展 `rumo-reflect`：复盘当前会话中反复出现的错误和用户的纠正，逐条与用户讨论该在哪里修正，用户批准后才改；用户要求复盘时自动加载，被反复纠正时 agent 会在交付时提议复盘，但不会自动开始。
- 新增默认技能 `rumo-agent-collaboration`：通过另一个 CLI、模型或 Orca 委派、转交和接力；客户端自带的子 agent 不归它管，每个任务一个负责人。点名 CLI 和任务即视为同意，发出前说明内容；额外内容或权限另行同意，提交、推送等授权不随启动授予。附带 `agent_run.py` 和 JSON 适配器：内置 codex、claude、pi、qwen、grok（本机帮助核对，qwen 有历史单轮证据），以及按官方文档编写、未核实的 cursor、gemini、opencode、GitHub Copilot CLI、Aider、Cline CLI、Goose。新增四个支持只读和 native-write 开发档位；文档可确认写模式，但不等于实跑，native-write 不承诺目录隔离。Copilot、Aider 的检查由调用方执行，Cline Act 默认自动批准，Goose approve 可能需要交互；Aider、Cline、Goose 当前仅单轮。记录加锁，取消与启动登记互斥，终态不被进度回写覆盖，超时覆盖不读 stdin 的子进程；pi 禁用 MCP 和扩展发现。绕过参数及无只读模式的适配器拒绝使用；Kimi、Crush 暂无确认的只读调用组合，未纳入。随默认安装提供；未安装协作技能的客户端仍可使用原交接和评审流程。
- `rumo-agent-collaboration`：新增声明式 `disabled_reason`，脚本拒绝停用适配器的检查、启动及旧记录恢复，仍可查看、记结论和安全取消。Gemini CLI 的无交互 Plan 模式可进入不受限执行，OpenCode 管理配置可覆盖内联权限，两者暂时停用。Linux/WSL 改用启动周期与内核进程启动计数识别归属；身份不明时拒绝停止或标为遗弃，旧秒级标识不自动迁移，其他未支持平台在启动前拒绝。点名且范围明确即构成授权，未核实状态不重复确认；外部 CLI 评审由 review 管标准、collaboration 管执行和记录。`check` 和模拟测试不能证明真实权限边界。
- 评测：被测 agent 能看到的提示、git 元数据和工作路径中，不再出现评测相关字样；运行器拒绝名称里含这类字样的输出目录。
- 插件清单新增 `version` 字段，并新增本文件。
- 安装器：新增 `-Uninstall` / `--uninstall` 和卸载预览，只移除指向本仓库的技能链接及常驻基线，保留其他来源的技能、仓库和 Profile；成功时按客户端汇总安装数量，缺少依赖时提示安装方法。
- 文档：重写中文 README 并提供独立英文版，补充新手指南、更新与卸载、遇到问题的处理方法，以及贡献和问题反馈入口。
- 修复：批量回归测试按解析后的绝对路径比较输出目录，避免 Windows 临时目录使用 8.3 短路径时测试失败。

## 0.4.0 - 2026-10-18

- 原来的 30 个技能合并为 17 个默认技能和 6 个可选扩展，扩展通过 `-Extras` / `--extras` 安装。
- 新增 `rumo-clarify`、`rumo-filesystem-safety`、`rumo-frontend`、`rumo-handoff`。
- 安装器自动检测 Codex、Claude Code 和共享的 `~/.agents` 目录；新增可选的常驻基线（`-Baseline` / `--baseline`）。
- 新增 Claude Code 插件，只包含默认技能。

## 0.3.1 - 2026-08-31

- Project Profile 的标识和解析路径受到限制，防止目录穿越和越界链接。
- 安装器可以持久化私有 Profiles 仓库路径；日报的去重状态按输出目录隔离。
- 仓库校验只检查 Git 跟踪且未被忽略的文件；CI 增加差异空白检查。

## 0.3.0 - 2026-08-31

- 新增跨会话日报、HTTP API 与高可靠开发技能，完善通用编码约束。

## 0.2.0 - 2026-08-27

- 安装器遇到同名外部技能时整体停止；新增 `-ReplaceForeignLinks` / `--replace-foreign-links`。
- 校验器增加 JSON 语法检查；CI 覆盖 Windows 和 Ubuntu。

## 0.1.0 - 2026-08-26

- 首次公开发布：27 个工程技能、跨平台安装器、Profile 模板、仓库校验与 CI。
