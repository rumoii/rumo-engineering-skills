# 更新记录

每个版本的完整说明见 [GitHub Releases](https://github.com/rumoii/rumo-engineering-skills/releases)。插件用户只在 `.claude-plugin/plugin.json` 的 `version` 提升后才会收到更新，所以每次发版都要提升版本号，并在这里补一节。

## 未发布

## 0.8.0 - 2026-10-24

- `rumo-review` 新增 Panel 模式（`references/panel.md`，取代 `references/other-cli.md`）：请 `rumo-setup` 配置的 review 线同时独立评审同一份改动。评审前先写一段改动意图；所有线共用一份 brief，不含自己的结论；当前 agent 自己先评完并存下结论，再读各线结果。失败、超时或空结果记为掉线，不换模型顶上。每条发现都对照代码核实，标出由哪几条线提出，报告附线路表、驳回清单和一致与分歧。只请一个模型给第二意见，就是只有一条线的面板。你点名时开；高风险改动由 agent 提议，按 `auto_panel` 先问、直接开或不提。
- `rumo-test`：高保障流程最终检查通过后，提议多模型评审面板。
- `rumo-agent-collaboration`：`agent_run.py start` / `resume` 默认不再弹进度窗口，后台运行，用 `watch` 查看进度；需要窗口时加 `--window`。`open` 的交互窗口不变。
- `agent_run.py`：去掉默认的 30 分钟超时；不带 `--timeout` 时一轮不设时间限制，只有用户或真实期限给出时才传。面板不为慢的线设时限：主审先出报告，后跑完的线再补进来，用户要求时才停掉某条线。面板 brief 要求评审者以 diff 为准，只在核实具体疑点时才读其他文件。
- `rumo-agent-collaboration`：description 改为只续接本技能记录的运行，并写明不用于自己接手另一个 agent 的会话；`rumo-coding-guidelines` 的接续工作流程写明来源可以是另一个 CLI 的会话（如 `codex resume <id>`），读它的会话记录后自己继续做。新增不应触发的用例 `collab-skip-takeover`。
- `agent_config.py`：某个角色里有一条线失效（例如适配器更新后不再支持某个强度）时，`set-role`、`set-auto-panel` 不再被整份配置的校验挡住，只校验正在改的那一项，失效的线由 `check` 逐条报告；`check` 在没配置任何线时返回 3（未配置）；`--executable` 对已保存的线也生效；预检失败时报出版本和 help 的真实原因；用途不同但 CLI、模型、强度相同的线只探测一次；文件读写和超时错误按退出码 2 报告，不再抛出 Python 报错；非字符串的用途标签给出拒绝原因而不是崩溃。这些问题由多模型评审面板实测时发现。
- 新增触发用例 `review-panel-request`。

## 0.7.0 - 2026-10-23

- 新增默认技能 `rumo-setup`：为多模型评审、多方案设计和默认委派选择 CLI、模型与思考强度，保存前对每条线跑一次只读探测；之后可随时重跑，只改点名的项。配置存放在 `~/.rumo-engineering-skills/agents.json`，只由脚本读取，不占会话上下文。安装器最后一行改为提示运行 `rumo-setup`。新增触发用例 `setup-first-run`、`setup-change-role`。
- `rumo-agent-collaboration`：新增 `scripts/agent_config.py`（`show`、`lanes`、`check --probe`、`set-role`、`set-auto-panel`）。适配器新增 `effort` / `efforts` 字段，`start`、`open`、`show` 支持 `--effort`，续接时沿用记录的强度；codex、claude、grok、pi 已声明。codex、claude、grok、pi 实际跑通一轮带强度的只读调用，`verified.live_run` 改为 true。用户没点名 CLI 时使用配置的 `delegate` 线。
- 适配器新增 `models` 字段，`agent_config.py models <cli>` 列出 CLI 可用的模型：codex 读 `codex debug models`（含每个模型支持的强度和默认强度），grok 读 `grok models`，pi 读 `pi --list-models`（列出 pi 里配置的所有提供方，ID 为 `provider/model`），claude 给出 `fable`、`opus`、`sonnet` 别名；qwen 不能列出，需手填。`rumo-setup` 改为先列出模型供选择，不再要求用户自己填 ID。CLI 列不出模型时，请用户照该 CLI 自己的模型选择界面原样提供 ID，不从它的模型总目录或配置文件里找。
- 默认委派可以按用途配多条线，写成 `用途=cli[:model][@effort]`，例如 `测试=pi:xiaomi-token-plan-cn/mimo-v2.6-pro@medium`、`实现=pi:deepseek/deepseek-v4-pro@high`；agent 按任务挑用途匹配的线，都不匹配用第一条。多条线时每条都要有不重复的用途；评审和设计的线不带用途。
- 插件清单：description 改为概括说明，不再逐个列技能名；原列表漏了 `rumo-agent-collaboration` 和 `rumo-reflect`。
- 安装器：`install.sh` 中需要带值的参数缺值时，明确提示缺哪个参数的值，并且不做任何改动。
- 评测：Codex 触发运行器的样本 `AGENTS.md` 不再禁止使用其他 agent，避免压低协作类用例的通过率。

## 0.6.1 - 2026-10-23

- `rumo-coding-guidelines`：任务流程从 6 条扩充到 14 条，新增性能问题、指标优化、运行时诊断、原型、视觉对齐、改技能或提示词、跟进 PR、暂停。正文保留一张速查表，每条的步骤和必须停下的情况放进 `references/task-flows.md`；常驻基线的 Flow 行同步更新，已安装基线的项目重跑安装器后生效。
- `rumo-reflect` 由可选扩展改为默认技能，Claude Code 插件用户也能使用了。description 中的修正位置补上“改结构”。之前用 `-Extras rumo-reflect` / `--extras rumo-reflect` 装过的，直接重跑安装器即可，链接会改指新位置；不要再带这个参数，否则会报 Unknown optional skill。新增触发用例 `reflect-request`，以及不该触发的 `reflect-skip-summary`。

## 0.6.0 - 2026-10-23

- 文档：重写中英文 README，新增“亮点”和“一个任务怎么走”，用修 500 报错讲完整流程并附 6 条任务流程速览；页头加入帕拉珂 / PARALCOR 标识，本项目纳入帕拉珂品牌展示；安装、更新卸载等内容保留，次要部分折叠。
- `rumo-verify`：新增“项目验证配方”模式。按项目整理一份 `verify-<app>` 技能，写明启动、就绪判断、只读健康检查、真实操作、取证和清理，并附功能地图；必须照着完整跑通一次才算完成，之后可以检查是否已经过时。能提交的仓库放在项目级技能目录，并在 `AGENTS.md` 写明路径；fork 等不能提交的仓库放在用户级技能目录。默认模式会先查找配方并按它取证。新增触发用例 `verify-recipe`。
- `rumo-coding-guidelines`：新增 6 条任务流程：小改动、修缺陷、新功能、只调查、接续工作、重构。常驻基线的 Flow 行改为指向这些流程。已安装基线的项目，需要重新运行 `baseline_block.py --install` 才会更新。
- `rumo-plan`：按计划执行跨会话或多步骤的任务时，在计划文件末尾追加“决策与弃案”，已写的行不再修改。`rumo-handoff` 的交接文档新增 “Tried And Dropped” 一节。
- `rumo-reflect`：修正位置最优先考虑“改结构，让错误无法发生”。每条候选都要说明更高的级别为什么做不到；新加的检查必须拿本次的真实错误跑一遍，确认会失败。
- 贡献规则：改动技能的 description 或行为规则后，推送前要在至少一个真实客户端上跑受影响的用例，并记录提交号、客户端、模型、用例和结果。
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
