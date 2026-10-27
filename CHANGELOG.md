# 更新记录

每个版本的完整说明见 [GitHub Releases](https://github.com/rumoii/rumo-engineering-skills/releases)。插件用户只在 `.claude-plugin/plugin.json` 的 `version` 提升后才会收到更新，所以每次发版都要提升版本号，并在这里补一节。

## Unreleased

- 外部 agent 的 `start`、`resume` 默认重新打开进度窗口（`rumo-agents` 里的一个标签页），`--no-window` 可以关掉。之前关掉它的理由是“客户端自己会通知后台任务结束”，但 Codex、qwen、pi 一轮结束后不会被叫醒：一次委派中，Codex 等了 8 分钟，在对方刚跑完时结束了这一轮，说“完成后我会核对”，用户只能自己去问。在终端里，`watch` 的输出改为上面滚动显示进度、下面固定几行状态（状态、用时、事件数、当前在做什么），结尾用中英文写明跑完、失败或超时，以及用时、结果文件，并提醒用户去告诉发起它的 agent；输出被重定向时仍是纯文本，不带控制字符。`external-cli.md` 的启动后一节改为：收不到后台退出通知的客户端直接结束这一轮，请用户在窗口显示跑完后告诉它，不承诺自己去核对，也不反复 `wait`；多模型评审的每条线各占一个标签页。

- 新增默认技能 `rumo-explain`：问“本仓库某块代码怎么工作、为什么这么设计”时，只读地讲清楚。先用一两句大白话给出最短的完整答案，再按需往深讲（怎么运行、代码在哪、为什么是这个形状、改它会踩的坑）；“为什么”从 `git log`、`git blame`、提交说明、PR 和决策记录里找证据，找不到就如实说，不编历史。不开子 agent。通用概念问题仍然不加载技能，出了故障交给 `rumo-debug`。常驻基线的路由表和任务路线里的“调查”一行都指向它；新增选用用例 `explain-how`。
- `rumo-handoff` 的接续支持按主题回忆：几天没碰一个项目，或者同时开着几条线时，先用 `session_digest.py list --since 14 --limit 30` 列出这段时间的会话，有主题再加 `--grep`（只匹配你说过的话、压缩摘要和会话标题，不匹配 agent 的回复），按线归类后每条线只读最新的会话。汇报时每条线一行，开头标明与 git 核对过的状态（已推送、已提交未推送、未提交已验证、在分支上进行中、已回滚、计划未开始等），再列反复出现的问题和下一步。带筛选时脚本不再凑够 `--limit` 个会话就停止扫描。新增选用用例 `handoff-recall`。
- 常驻基线和 `rumo-coding-guidelines` 新增一条：回答、讲解和报告里的事实性结论，写明来自实际运行、读到的代码（`file:line`）还是推断，不把推断说成事实。
- `rumo-coding-guidelines` 新增参考 `measurement.md`：报告性能数字之前要过的几问，包括瓶颈在哪、两边配置是否一致、结果是否超出硬件上限、错误是否被计入、交替多跑几次后差距是否大于波动、端到端占比多少、被计时的工作是否真的执行了。报告先给结论，再给数字、次数、范围和瓶颈。性能问题和指标改进两条路线在报告数字前会读它。

- 删除行为评测、回归集和 pi 运行器（`run_codex_behavior.py`、`codex_behavior_cases.py`、`run_pi_behavior.py`、`run_regression.py`、`run_pi_trigger.py`、`pi_workspace_guard.mjs` 及其测试）：规则好不好用改看实际开发反馈，不再做有无技能的对照。`run_codex_trigger.py` 原来借用的辅助函数和对应测试并入它自己；推送前验收、`evals/` 用例和 Claude 行为用例保留。PR 模板、CONTRIBUTING 和 README 同步去掉对照组与回归集的要求。
- README 去掉三处与别处重复的内容：任务路线表改为链接到 `task-flows.md`，“第一次配置 agent”缩成几行（细节由 `rumo-setup` 运行时讲解），项目 Profile 的用法只留在新手指南。
- `rumo-agent-collaboration` 第 3、4 步只留判断规则，各路线的操作细节移到对应参考：`--detach`、`watch`、`survives_caller` 和 Claude Code 跨会话订阅放进 `external-cli.md` 新增的 “After Launch” 一节，原生子 agent 的完成通知放进 `native.md`；路线不可用和不确定是否送达两条改为停止条件。只是挪位置，没有删改规则。
- `rumo-verify` 的验证配方按首次真实使用（为一个静态导出博客生成并跑通配方）补齐：调查阶段先看仓库的 e2e 或部署实际怎么启动，不再默认指向 dev server；新增“本地没有的依赖、仓库测试怎么替身”一问，替身只限应用之外的依赖、没有现成替身先问用户，并在功能文件里写明替身范围和线上未验证的部分；隔离考虑构建产物；新增前提条件一节；启动时记下真实进程 ID 和占用端口的证据，健康检查和清理以此为准；没有版本标记时每次重新构建并比对产物；证据放在项目构建、测试和清理删不到的地方，且不进版本库；命令要在项目用到的每种 shell 里都能跑；仓库内的配方先过项目的格式和 lint 检查；配方或辅助脚本改动后要重新跑通。
- `rumo-prose` 的写作指南不再要求精简技能前后跑行为评测，改为跑仓库贡献指南规定的检查，并确认钉住的规则仍在。
- 风险关卡改由 `rumo-coding-guidelines` 直接承载，不再要求另外加载 `rumo-test`。原来的写法是 guidelines 只说一句“去加载 rumo-test”，Claude 改权限时常常不去加载。关卡分两档：钱、登录权限与密钥、数据库迁移、不可撤销操作直接按高风险处理；持久数据、并发、别的程序会读的接口和格式、外部不可信输入、个人隐私数据、部署与依赖先判断。后三类参照 Google 代码评审指南、OWASP 和业界对 AI agent 的管控做法补齐。高风险时要先写改前会失败的测试，说出这次改动安全所依赖的那一个事实并用运行代码证明，改完再跑一遍。`high-assurance.md` 随之移到 guidelines 的 references；`rumo-test` 只保留证据规划和测试先行。
- 常驻基线块改写成路由表：核心规则加风险关卡摘要，再用一张表写明“什么情况用哪个技能”，不靠模型自己挑选也能接上各个技能。仍然不用 SessionStart hook，写进用户自己的 `CLAUDE.md` 或 `AGENTS.md` 之前照旧先征得同意。
- 删除多方案设计面板：`rumo-plan` 的 `design-panel.md`、配置里的 `design` 用途和 `plan-design-panel` 用例都已移除。想让别的模型出方案时，通过 `rumo-agent-collaboration` 交给它一个只读的设计任务。旧配置里的 `design` 读取时忽略，下次写入时去掉。
- 委派分两条路：当前客户端自己那家的模型线（例如 Claude Code 里的 `claude` 线）直接用客户端自带的子 agent 运行，传入线上配置的模型和思考强度，不再另起一个 CLI；子 agent 不支持该模型时改走 `agent_run.py`，模型不变。别家的模型照旧走 `agent_run.py`。派活按活的难度选线；简报必须写明“怎样算做完”的检查，主 agent 拿回结果后自己重跑；不合格时开新的一轮返工，换线要用户同意。`rumo-setup` 为委派增加“常规活交给当前客户端的便宜模型”这一推荐。
- 推送前验收只针对选用：增删、合并、改名技能或改描述时，跑受影响的选用用例。技能正文的规则好不好用，看实际开发中的反馈和 `rumo-reflect`；行为用例和对照实验改为按需。

- `rumo-handoff` 写交接文档时会同时接入工作区已有的任务索引、现状文档或交接登记入口，让接收方不依赖原对话即可发现；没有现成入口时明确给出需要传递的路径，不另建平行文档体系。会话接续新增 Kimi Code：通过官方会话索引只读取当前项目的主会话，保留真实用户消息、每轮最终回复和最近压缩摘要，并排除工具输出、思考及注入内容。新增交接发现行为用例和 Kimi 单元测试。
- `rumo-setup` 改为讲人话：第一次运行先说明它是做什么的、不配也能用、什么时候才花额度；每个配置项用大白话解释，展示给你时不再出现 `codex:...@high` 这类写法；推荐配置整理成一张表，每行写明理由，可以整体接受或只改几项；本机只有当前这一个 AI 工具时直接说明不用配；探测失败时说明原因和你下一步能做什么；常驻基线改为配置写入后单独问。重跑时的选项也按同一套说法写，不再自造“评审团”之类的名字；自动多模型那项说清是“你没开口、agent 觉得有风险时要不要请其他 agent 一起看”。全部选项和重跑行为不变。README 的“第一次配置 agent”补充用途、推荐配置示例和术语对照。
- 多模型什么时候主动提议，按研究和业界做法写实：评审要同时满足“出错代价高”和“正确性靠测试钉不住的假设、做法本身可能错，或自己没把握、修了两次没修好”之一，测试已能判定就不提；设计要同时满足难以回退、确实拿不准、没有快速原型能判定。提议时用一句话说明理由、请谁和花额度，同一目标只问一次。普通评审遇到权限、金额、持久数据、并发、公共接口或部署脚本的改动时，也会对照这些条件，满足就在报告末尾提议；之前这些条件只写在面板的说明里，普通评审根本读不到。`rumo-test` 高保障流程跑完也按这套条件判断，不再一律提议。`rumo-setup` 为评审和设计推荐该厂商的最强模型，不推荐轻量档。
- `rumo-handoff` 只在工作区自己的说明文件点名了任务索引或交接登记处时才往那里加链接，不为指向未提交的交接文档去改产品 README 等其他受跟踪文件。Kimi 会话接续改为按 `<skill-loaded>` 标签识别技能注入，不再依赖一句英文提示，并保留用户在一轮进行中补发的消息。`handoff-discoverable` 用例不再需要 Bash，Windows 上也能跑 Claude 验收，评分改为同时检查测试命令和未完成的文档。

## 1.0.0 - 2026-10-25

- 看外部 agent 的进度只需一步：`agent_run.py start` 和 `resume` 一启动，就先在 stderr 打印一行现成的 `watch` 命令（含 run ID），stdout 仍然只输出最后的摘要，agent 能直接把这条命令交给你，不必再让你先查 `runs --active`。`agent_run.py watch` 不带 run ID 时，会在同一屏跟踪所有正在运行的任务，每行标明是哪个 CLI、哪个任务；多模型面板的几条线可以一起看。
- `rumo-handoff` 支持新会话接续：在新会话里问“汇报一下当前进度、下一步做什么”或“接着上次做”时，会用新增的只读脚本 `scripts/session_digest.py` 列出本项目最近的 Claude Code 和 Codex 会话，并压缩成时间线。时间线只保留你的消息、每轮的最终回复和最近一次压缩摘要，不读别的项目的会话。之后对照仓库状态，汇报做到哪了、验证过什么、下一步建议，汇报完就停，等你说继续。会话结束时不需要再写交接文档；交接文档仍然只在你要求时写。它改为可以自动调用，`rumo-coding-guidelines` 的接续流程也指向它。新增触发用例 `handoff-pickup`、`handoff-write`。
- `rumo-lifecycle-safety`、`rumo-frontend` 的 description 写明不该用的情况：在主机上安装或运维服务交给 `rumo-remote-ops`，没有后台任务的同步代码不用它；只查原因、不要修的页面问题交给 `rumo-debug`。新增不应触发的用例 `lifecycle-skip-service`、`frontend-skip-diagnosis`。
- `agent_config.py` 读到更新版本的 rumo 写入的配置时，提示先更新技能，不再只报 “version must be 1”；配置文件照旧不被改写。代码里写明以后改结构时的约定：提升版本，同时在读取处补上旧版本的内存升级，下次写入才落盘。
- 一台机器只有一份 agent 配置，不支持按仓库覆盖：`rumo-setup` 和 README 写明两条退路，某次任务在请求里点名线路；某个仓库长期用另一套时，把 `RUMO_AGENTS_CONFIG` 指向另一份配置。
- README 把 CLI 分三组写：codex、claude、grok、pi、qwen 实际跑通过，属于支持；aider、cline、copilot、cursor、goose 属于实验性，并写明升为支持的条件；gemini、opencode 已停用，要先解决权限问题才能启用。补充安装器方式固定在某个版本的方法；写明安全护栏是写给 agent 的规则，不是拦截机制。
- 外部模型评审只归 `rumo-review`：它的面板自己调用协作技能的脚本。`rumo-agent-collaboration` 的 description 和正文不再要求同时加载两个技能，示例里不再用已停用的 Gemini。用例 `collab-external-review` 改为只加载 `rumo-review`，提示词点名 qwen，在 Claude 和 Codex 里意思相同。
- `rumo-interface` 的 HTTP 评审报告分别说明幂等键对调用主体、租户、操作和 endpoint 的隔离，以及请求指纹，不再用一个合并的“幂等失败”标记掩盖未检查的维度。
- `rumo-review` 的修复循环保留独立评审，线路由用户点名或 review 配置决定，不再硬编码 Codex 优先；首次外发前确认一次，后续循环沿用同一线路，不默认启动多模型面板。
- `rumo-handoff` 按 ID 读取旧 Codex 会话时不再受最近 500 条全局记录限制；列表达到扫描预算仍未找全本项目记录时明确报告截断。部署计划脚本现在校验唯一的 Profile deployment 和必要命令，空 Profile 或缺字段会拒绝生成计划。
- 离线包静态审查不再默认执行安装器，构建和隔离安装分别授权；Mermaid 缺依赖时先取得安装同意；Linux 硬件巡检默认保留旧报告。内存巡检补齐有界线程、FD 和声明式 JVM 证据，缺失时明确标记未收集。
- 外部 agent 的新运行记录在 POSIX 上默认目录 0700、文件 0600，Windows 保留现有 ACL；README 写明 start/resume 当前仅支持 Windows 和 Linux/WSL。
- `rumo-setup` 首次运行时问要不要写入常驻基线，推荐写入；写入当前客户端的用户级说明文件，Claude Code 和 Codex 以外的客户端先问文件路径。插件用户因此不需要 clone 仓库。
- `rumo-coding-guidelines`：小改动和只调查两条流程不再要求先读 `task-flows.md`，表格里的步骤已经写全。
- 扩展：`rumo-daily-report` 的 description 补上中英文之间的空格；`rumo-imagegen` 去掉无法判断的 “more appropriate” 条件。
- 安装器在 pull 成功、后续校验或安装失败时，明确警告现有技能链接可能已经提供新内容，不再让用户误以为整个更新没有生效。
- `rumo-filesystem-safety` 明确覆盖以后执行、本次不运行的清理脚本；编写或评审脚本不等于授权执行删除。
- 自动触发的 extras 纳入触发用例覆盖检查，新增 Mermaid、Word 文档和离线交付包场景；`database-stop` 改为禁止未确认目标前的任何 shell 执行。

## 0.9.0 - 2026-10-24

- `rumo-plan` 新增多方案设计面板（`references/design-panel.md`）：你让几个模型各出一个方案，或者设计确实拿不准、会影响接口、存储数据或模块边界时，请 `rumo-setup` 配置的 design 线各自独立出一版方案：先写调用方怎么用，再写数据形状、模块划分和放弃过的方案。当前 agent 也出一版，存档后再读各线结果。比较时看坏味道清单和接口深度，选一个做底、最多移植一两处，交给你选定后才拆任务。启动、授权、掉线和运行记录整篇沿用 `rumo-review` 的面板，只替换 brief、自评和比较报告三处。设计坏味道从 3 条扩到 6 条，新增：同一份状态有多个写入者、同一件事有两种做法、同一份清单要多处手动同步。新增触发用例 `plan-design-panel`。
- `rumo-coding-guidelines` 新增 `references/principles.md`，收录还没覆盖的 8 条原则：先删再加、质疑前提、重新设计而不是硬塞、先定数据形状、边界校验内部信任、降低读者负担、造工具、解释数字。每条写明什么时候读、改变什么决定、一个反例；这些原则只改变做法、不扩大范围，本次改动以外的清理照旧只报告。正文写明在哪些时刻去读，修缺陷、重构、性能问题这几条流程各链到相应条目。
- `rumo-review` 面板：客户端在本轮结束后收不到后台退出时，先出报告，并请用户在待返回的线跑完时告知，再核实这些线。

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
