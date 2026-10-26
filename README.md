<div align="center">

# Rumo Engineering Skills

让 AI 编程 agent 先问清、再动手、用证据交付的工程技能

[![版本](https://img.shields.io/github/v/release/rumoii/rumo-engineering-skills?label=%E7%89%88%E6%9C%AC&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/releases/latest)
[![Stars](https://img.shields.io/github/stars/rumoii/rumo-engineering-skills?label=Stars&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/stargazers)
[![许可证](https://img.shields.io/github/license/rumoii/rumo-engineering-skills?label=%E8%AE%B8%E5%8F%AF%E8%AF%81)](LICENSE)
![客户端](https://img.shields.io/badge/%E5%AE%A2%E6%88%B7%E7%AB%AF-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20SKILL.md-4b6b8a)

**[快速开始](#快速开始)** · [亮点](#亮点) · [新手指南](GETTING_STARTED.md) · [遇到问题](GETTING_STARTED.md#6-遇到问题) · [English](README.en.md)

<p align="center">
  <a href="https://github.com/paralcor">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/images/brand/paralcor-horizontal-dark.png">
      <img alt="PARALCOR" src="docs/images/brand/paralcor-horizontal-light.png" width="120">
    </picture>
  </a>
  <br>
  <sub>Rumo Engineering Skills 由 @rumoii 编写维护，纳入帕拉珂 / PARALCOR 品牌展示。</sub>
</p>

</div>

一套精简的工程技能，适用于 Claude Code、Codex 以及其他能加载 `SKILL.md` 目录的 agent。

不需要先学工程规范：装上之后，agent 会先问清需求，改完拿证据验证；遇到删库、删文件、改服务器这类操作，会先停下来确认。

## 亮点

- **团队实战出来的。** 我所在公司的研发部门自 2026 年 6 月起有数十人日常使用这套技能，他们用的是加入了具体业务内容的定制版；这里是去掉业务内容的通用版。技能里不含任何公司、产品、主机或部署信息，私有信息放在本地 [项目 Profile](#进阶) 里。文档中文优先，另有完整英文版。
- **用评测说话，不靠自述。** 在 Claude Code 和 Codex 上分别评测两件事：会不会根据一句普通的话选中技能，选中后做得对不对；并设有不装技能的对照组。增删技能或改了描述，推送前要在真实客户端上跑受影响的选用用例做[验收](CONTRIBUTING.md#acceptance-before-push)；技能正文的规则好不好用，看实际开发中的反馈。用例都在 [`evals/`](evals/)。
- **危险操作有刹车。** 删库、删文件、改服务器、碰生产环境之前，先只读确认目标和影响范围，备份和回滚准备好、你明确同意后才写。这些是写给 agent 的规则，不是拦截机制；要硬性限制，请用客户端自己的权限设置。
- **小事不折腾。** 改一行文案不写计划、不做评审，改完跑最相关的检查就交付。每条技能描述不超过 100 词，由校验器把关，常驻上下文的开销很小。
- **验证一次，以后照着做。** 项目验证配方把“怎么启动、点哪里、看到什么算成功”写下来，并实际跑通一次。下一个 agent 不用重新摸索，改完直接照着验证真实功能。
- **跨客户端，能协作。** 同一套技能可以装进 Claude Code、Codex 和其他读 `SKILL.md` 的客户端；还能把任务交给本机的另一个 CLI 或模型去执行，或者请你配置的几个模型同时独立评审同一份改动；agent 自己也评一遍，逐条对照代码核实后合并成一份报告，注明每条问题是哪几个模型提出的。

## 装上之后有什么不同

| 你说 | 没装时常见的做法 | 装上之后 |
| --- | --- | --- |
| “做个导出功能” | 猜一个方案直接开写 | 先把要确认的问题一次问完，每个问题附推荐选项（`rumo-clarify`） |
| “页面报 500，查一下” | 边猜边改代码 | 先复现、定位，用证据说明根因；没让修就不改代码（`rumo-debug`） |
| “把测试库的旧数据清掉” | 直接执行 `DELETE` | 先只读确认是哪个库、会影响多少行，备份和回滚准备好、你明确同意后才写（`rumo-database-change-safety`） |
| “做完了吗？” | 没跑测试就说“已完成” | 列出实际跑过的命令和结果，没跑的直接说明（`rumo-verify`） |
| “改完了，帮我确认真的能用” | 只跑单元测试就说没问题 | 照项目验证配方启动应用、操作真实功能并保留证据，配方过时会指出来（`rumo-verify`） |

## 一个任务怎么走

以“订单页报 500，修一下”为例：

1. `rumo-debug` 先复现报错，沿调用链找到原因，并用日志、请求或数据证明原因成立，不靠猜。
2. `rumo-test` 先写一个能复现这个缺陷的测试，确认它在修复前失败。
3. 修复代码，看着这个测试转绿，再跑周边的测试。
4. 项目有验证配方时，照着它启动应用、打开订单页，确认真实页面恢复正常，并保存证据。
5. `rumo-verify` 交付前列出实际跑过的命令和结果；没跑的检查直接说明，不说“应该没问题”。
6. 你说提交，`rumo-git-commit` 才会按仓库约定提交；推送同样要你明确要求。

其他任务各有默认路线，由 `rumo-coding-guidelines` 选择：

| 任务 | 路线 |
| --- | --- |
| 小改动 | 读代码 → 改 → 跑最相关的检查 → 验证；不写计划、不做评审 |
| 修缺陷 | 复现并证明原因 → 失败测试 → 修复 → 验证配方 → 验证 |
| 新功能 | 目标不清先澄清 → 多步骤先计划 → 风险判断 → 分小段实现 → 验证配方 → 验证 |
| 只调查 | 只读，回答问题并附证据 |
| 接续工作 | 读交接文档、决策与弃案记录 → 核对仓库实际状态 → 继续 |
| 重构 | 确认测试覆盖 → 改结构 → 同一批测试仍然通过 |
| 性能问题 | 同样条件测基线 → 定位 → 修复 → 同样条件再测，报告前后数字 |
| 指标优化 | 固定测量方法 → 每次尝试记一行前后数值 → 有效保留、无效回退；不放宽目标 |
| 运行时诊断 | 采集现场信号或 trace → 缩小到具体机制 → 确认 → 对应到源码；只诊断不修 |
| 原型 | 说清要定的决定 → 产品之外做一次性实现 → 多方案可切换 → 给推荐 |
| 视觉对齐 | 先截各状态基线 → 一次迁移一个组件 → 逐个图像对比 |
| 改技能或提示词 | 按写作规范改 → 跑仓库校验 → 行为有变化时跑评测用例 |
| 跟进 PR | 你要求时：冲突 → 评审意见 → CI；不合并 |
| 暂停 | 停在安全边界，不做不可逆操作，写续做说明；你不说就不提交 |

想指定技能时可以点名调用（用插件安装时，Claude Code 的技能名要带前缀，例如 `/rumo-engineering-skills:rumo-clarify`）：

| 想做的事 | Codex | Claude Code |
| --- | --- | --- |
| 对齐含糊的需求 | `$rumo-clarify` | `/rumo-clarify` |
| 把已确认的工作拆成可验证的任务，再逐个执行 | `$rumo-plan` | `/rumo-plan` |
| 测试先行地实现 | `$rumo-test` | `/rumo-test` |
| 只读排查缺陷根因 | `$rumo-debug` | `/rumo-debug` |
| 声称完成前检查改动，或建立项目验证配方 | `$rumo-verify` | `/rumo-verify` |
| 只读评审差异 | `$rumo-review` | `/rumo-review` |
| 提交、合入、推送或开 PR | `$rumo-git-commit` | `/rumo-git-commit` |

标注“仅手动调用”的技能不会被自动选用，使用时必须点名。[完整案例](GETTING_STARTED.md#完整案例)展示了三个请求从提出到交付的全过程。

## 快速开始

### Claude Code 插件

只用 Claude Code 时推荐这种方式，不需要 clone。在会话里执行，然后开一个新会话（需要 Claude Code 2.1.275 或更高版本）：

```text
/plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills
```

在终端里用 `claude plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills`（需要 2.1.292 或更高版本）。更早的版本先添加插件市场再安装：

```bash
claude plugin marketplace add rumoii/rumo-engineering-skills
claude plugin install rumo-engineering-skills@rumo-engineering-skills
```

插件里的技能名带前缀，例如 `/rumo-engineering-skills:rumo-clarify`。插件只对 Claude Code 生效，不含扩展；其他客户端用安装器。同一台机器只选一种方式：安装器已经把技能链接进 `~/.claude/skills` 时再装插件，每个技能都会出现两次。

### 让 AI 帮你安装

用 Codex 或其他客户端时，把下面这段提示词发给你的 agent，它会先预演、再安装，并告诉你改了什么：

```text
按 https://github.com/rumoii/rumo-engineering-skills 的 README 安装这套技能。
1. 本地没有就先 clone，然后用 --dry-run(Windows 用 -DryRun)运行安装器，把它会改动的内容告诉我。
2. 不带 --baseline 正式运行安装器，告诉我链接了哪些客户端。
3. 写入我的用户级 CLAUDE.md 或 AGENTS.md 之前先问我；我同意了，才带 --baseline(-Baseline)重跑，并把加进去的内容给我看。
4. 列出改动过的文件，并提醒我开新会话。
5. 提醒我在新会话里运行 rumo-setup，选择多模型评审和委派用的 agent、模型和思考强度。
```

AI 没收到这段提示词、只按 README 安装时，也遵守同一条规则：没有用户明确同意，绝不加 `--baseline` 或 `-Baseline`，因为它会改用户自己的说明文件。

### 用安装器安装

需要 Git 和 Python 3，不需要管理员权限。`-ExecutionPolicy Bypass` 只对这一次运行生效，不改系统设置。后文的 Windows 命令简写成 `.\install.ps1 ...`；系统禁止运行脚本时，照这里写成 `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 ...`。

```powershell
git clone https://github.com/rumoii/rumo-engineering-skills.git
cd rumo-engineering-skills
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -NoPull
```

```bash
git clone https://github.com/rumoii/rumo-engineering-skills.git
cd rumo-engineering-skills
./install.sh --no-pull
```

安装器先校验仓库，再把默认技能链接到检测到的每个客户端（Codex、Claude Code 和共享的 `~/.agents` 目录）。它只管理 `rumo-*` 链接，不动其他技能。成功时每个客户端会输出一行 `<数量> skills linked in <目录>`，最后一行以 `Next:` 开头。装完开一个新会话，让客户端重新加载技能列表。

### 第一次配置 agent（可选）

**这是做什么的。** agent 可以调用你本机装的其他 AI 编程工具（Codex、Claude Code、qwen、grok、pi 等），请它们独立复查改动，或者把活交给它们做。`rumo-setup` 用来告诉 agent：可以找谁、用哪个模型、想多深。

**要不要配。** 不配也完全能用，所有技能照常工作，只是少了“第二双眼睛”。本机只装了当前这一个 AI 工具时不用配。配了之后，别的工具只在真正被调用时才花它的额度。

**怎样配比较合理。** 大多数人这样配就够了，`rumo-setup` 第一次运行也会这样推荐：

| 用途 | 推荐 | 理由 |
| --- | --- | --- |
| 评审：复查改动 | 一个和当前 agent 不同厂商的工具，思考强度 high | 不同厂商的模型盲点不同；配一个就够，多加一个主要是多花额度 |
| 委派：把活交出去 | 同一个工具，思考强度 medium；常规活也可以交给当前客户端自己的便宜模型，例如 Claude Code 的 sonnet | 常规活不需要最深的思考，也更省额度；同一家的模型由客户端自带的子 agent 运行，不用再启动一个 CLI |
| 你没开口、agent 觉得改动有风险时 | 先问你要不要请其他 agent 一起看（`ask`） | 每次多花额度都由你决定 |

例如平时用 Claude Code、本机还装了 Codex：评审用 Codex（high），委派用 Codex（medium），常规活交给 Claude Code 的 sonnet（medium）。

**术语对照。** 配置文件和脚本输出里会出现这些词：

| 词 | 意思 |
| --- | --- |
| lane（线） | 一个“工具 + 模型 + 思考强度”的组合，写作 `codex:gpt-6.1-sol@high`；省略模型或强度就用该工具自己的默认值 |
| review / delegate | 评审、委派两个用途，各配一条或几条线 |
| effort（思考强度） | 模型想得多深：越高越仔细，也越慢、越费额度 |
| `auto_panel` | 你没开口、agent 判断某个改动有风险时，要不要再请配置的其他 agent 一起看：先问你（`ask`，默认）、说明请谁后直接开始（`allow`），还是不主动请、等你开口（`off`） |
| 探测 | 保存前给每条新线发一句固定的话，确认它能用；只花一点额度，不发仓库内容 |

**怎么运行。** 装好后开新会话，运行 `/rumo-setup`（Claude Code 插件里是 `/rumo-engineering-skills:rumo-setup`，Codex 里是 `$rumo-setup`）。它先说明用途，列出本机检测到的工具，给一张带理由的推荐表，你可以整体接受或只改其中几项；探测通过后才写入，最后单独问一次要不要写入[常驻基线](#常驻基线)。

- 以后随时重跑 `/rumo-setup`，或直接说“把评审换成 grok，思考强度 high”；只改你点名的项。
- 配置在 `~/.rumo-engineering-skills/agents.json`，只有脚本读它，不占会话上下文。没配置时，用到多模型功能的地方会提示你先运行 `rumo-setup`。
- 默认只用当前 agent 一条线；多模型只在你点名、改动被评为高风险，或 agent 判断值得时才开，后两种是否先问你由配置里的 `auto_panel` 决定。
- 一台机器只有这一份配置，不支持按仓库覆盖。某次想换线，直接在请求里点名，例如“用 codex 评审”；某个仓库要长期用另一套，在那个目录里把 `RUMO_AGENTS_CONFIG` 指向另一份配置（可以用 direnv 之类的工具自动切换），再运行 `rumo-setup`。
- 支持的 CLI 分三组：
  - **支持**：codex、claude、grok、pi、qwen，都实际跑通过。
  - **实验性**：aider、cline、copilot、cursor、goose，适配器是按各自文档写的，`rumo-setup` 会提示它还没在真实环境跑通过、可能用不了。装上其中某个后，按 [adapters.md](skills/rumo-agent-collaboration/references/adapters.md) 跑 `check`，再跑一轮真实的只读调用，把结果写进 `verified`，它就升为支持。
  - **已停用**：gemini、opencode。它们的只读设置可能被绕过（原因见 adapters.md），脚本拒绝启动。要启用，得先把权限问题解决；不能靠删掉 `disabled_reason` 来启用。

### 遇到问题

- 装不上、装完看不到技能、技能出现两次：先看新手指南的[遇到问题](GETTING_STARTED.md#6-遇到问题)，按看到的现象找对应小节。
- 安装器报错时，加 `-DryRun`（`--dry-run`）重跑，保存完整输出。
- 仍未解决：[提交问题](https://github.com/rumoii/rumo-engineering-skills/issues/new/choose)，附上 `-DryRun` 输出、`git rev-parse HEAD` 和客户端版本。issue 是公开的，贴出前删掉用户名、公司路径和代码。

## 支持范围

| 客户端 | 安装方式 | 验证程度 |
| --- | --- | --- |
| Claude Code | 插件或安装器 | 安装、加载、自动选用评测、行为评测（含跨技能用例） |
| Codex | 安装器 | 安装、加载、自动选用评测、行为评测（含实际运行测试的用例） |
| 其他读取 `~/.agents/skills` 的客户端 | 安装器 + 共享目录 | 只验证过安装和加载 |

点名调用成功只说明客户端加载了技能，不说明它会根据自然语言自动选中技能。其他客户端的接入方式见[新手指南](GETTING_STARTED.md#其他客户端)。外部 agent 的 `start` / `resume` 目前只支持 Windows 和 Linux/WSL；其他平台（包括 macOS）只能查看已有运行记录，安装技能不代表可以使用这些外部运行功能。

## 默认技能

默认安装。

| 技能 | 用途 |
| --- | --- |
| `rumo-clarify` | 合并当前可回答的问题并给出推荐，必要时补问新决策；关键事项不擅自取默认值 |
| `rumo-plan` | 短规格加可验证的任务拆分、按任务逐个执行已确认的计划，或持久化的工程决策记录 |
| `rumo-coding-guidelines` | 基线纪律：基于真实代码路径，只做请求和必要的工作，高风险改动过风险关卡，并以验证收尾 |
| `rumo-test` | 证据规划与测试先行实现 |
| `rumo-debug` | 复现、定位并用证据证明根因；除非请求包含修复，否则只读 |
| `rumo-verify` | 声称完成前确定真实改动范围并跑最小充分检查；建设仓库门禁；建立和维护项目验证配方 |
| `rumo-review` | 只读评审差异或审计指定范围的现存问题；明确要求时进入修复循环、做可删复杂度审计、处理评审意见，或经你同意后请配置的几个模型一起评审（多模型评审面板），合并结果并核实 |
| `rumo-git-commit` | 按仓库约定提交、合入分支、整理历史、发布、推送、开 PR，以及跟进已开 PR 的 CI 检查 |
| `rumo-interface` | API、消息、配置和持久化格式的兼容演进，含 HTTP 契约检查 |
| `rumo-lifecycle-safety` | 长期运行任务的归属、重试、取消、超时、关闭与资源清理 |
| `rumo-database-change-safety` | 经授权、有备份、影响有界且可回滚的数据库写入 |
| `rumo-filesystem-safety` | 按影响范围分级处理删除与批量清理 |
| `rumo-remote-ops` | 远程 Linux 查询与变更、服务部署、备份恢复和制品部署 |
| `rumo-prose` | 保留全部事实的注释、报错、日志、界面文案、文档与 agent 文件 |
| `rumo-frontend` | 前端页面开发与新界面设计、可访问性检查、本地开发服务排障、按需采集浏览器证据 |
| `rumo-handoff` | 新会话里问“汇报一下当前进度、下一步做什么”时，读取本项目最近的 Claude Code、Codex 和 Kimi Code 会话记录并对照仓库状态接续；你要求时生成自包含的交接文档，并接入现有导航让接收方能够发现 |
| `rumo-project-profile` | 为其他技能解析和校验私有项目 Profile |
| `rumo-reflect` | 复盘当前会话的反复错误与纠正，逐条讨论该固化到哪里，你批准后才改 |
| `rumo-setup` | 首次或随时配置多模型评审和默认委派用的 CLI、模型与思考强度，保存前逐条只读探测 |
| `rumo-agent-collaboration` | 把任务委派、整体转交或接力给另一个 CLI 或模型，也可以通过 Orca 协作；同一家的模型交给客户端自带的子 agent 运行，别家的模型走外部 CLI，并按活的难度选线。支持哪些 CLI 见[第一次配置 agent](#第一次配置-agent可选) |

## 可选扩展

默认不安装，只能通过安装器添加，插件不含扩展。

| 技能 | 用途 |
| --- | --- |
| `rumo-diagram` | Mermaid 业务流程图与经确认的工程拓扑图，含预览与导出 |
| `rumo-document-writing` | 正式的 Word 交付文档 |
| `rumo-offline-delivery-audit` | 离线交付包的完整性、溯源、安装、回滚与验收边界 |
| `rumo-daily-report` | 按日期文本文件增量生成中文日报（仅手动调用） |
| `rumo-linux-inspect` | 只读采集 Linux 硬件配置或巡检内存（仅手动调用） |
| `rumo-imagegen` | 通过用户自配的 OpenAI 兼容接口生成单张图片（仅手动调用） |

```powershell
.\install.ps1 -NoPull -ListExtras
.\install.ps1 -NoPull -Extras rumo-diagram,rumo-document-writing
.\install.ps1 -NoPull -RemoveExtras rumo-document-writing
```

```bash
./install.sh --no-pull --list-extras
./install.sh --no-pull --extras rumo-diagram,rumo-document-writing
./install.sh --no-pull --remove-extras rumo-document-writing
```

装过的扩展在不带参数重跑安装器时会保留。

## 常驻基线

客户端只在 description 与请求匹配时才加载技能，小改动可能跳过 `rumo-coding-guidelines` 的基线规则，技能之间也可能接不上。安装器可以把核心规则、风险关卡和一张“什么情况用哪个技能”的路由表写进检测到的客户端的用户级说明文件：Claude Code 目录下的 `CLAUDE.md`，以及 Codex 目录下的 `AGENTS.md`。写入的内容位于 `rumo-engineering-skills:baseline` 标记之间，标记之外的内容不会改动。

<details>
<summary>写入、更新和移除</summary>

```powershell
.\install.ps1 -NoPull -Baseline
.\install.ps1 -NoPull -RemoveBaseline
```

```bash
./install.sh --no-pull --baseline
./install.sh --no-pull --remove-baseline
```

之后不带参数重跑安装器时会自动更新这段内容；没写入过的，安装结束时会提示一行。插件用户和其他客户端第一次运行 `rumo-setup` 时，它会问要不要写入当前客户端的用户级说明文件，不需要 clone 仓库；用的不是 Claude Code 或 Codex 时，它会先问你那个文件的路径。也可以在 clone 下来的仓库目录里直接运行辅助脚本，例如 `python3 skills/rumo-coding-guidelines/scripts/baseline_block.py --target ~/.claude/CLAUDE.md --install`，也可以手动把 [agents-snippet.md](skills/rumo-coding-guidelines/references/agents-snippet.md) 里的代码块贴进去。

</details>

## 更新与卸载

安装器只会写这几处：客户端技能目录里的 `rumo-*` 链接；你同意后写入 `CLAUDE.md`、`AGENTS.md` 的基线标记块；以及用 `-ProfilesRepo` 时保存的 `~/.rumo-engineering-skills/config.json`。

**更新。** 安装器：去掉 `-NoPull`（`--no-pull`）重跑 `.\install.ps1` 或 `./install.sh`，它会先 `git pull --ff-only` 拉取最新版本，再重新链接，已装的扩展和基线会保留，然后开新会话。如果 pull 成功而后续校验或安装失败，安装器会额外警告现有链接可能已经提供新内容；这不表示仓库已回滚。插件：先执行 `claude plugin marketplace update rumo-engineering-skills`，再执行 `claude plugin update rumo-engineering-skills@rumo-engineering-skills`，然后开新会话。已装的插件只在发版提升 `version` 后才会更新；每版改了什么见 [CHANGELOG.md](CHANGELOG.md)。安装器装的是指向本仓库的链接，想固定在某个版本时，在仓库目录执行 `git checkout v0.9.0` 这类发版标签，再加 `-NoPull`（`--no-pull`）重跑安装器；回到最新版本时先 `git checkout main`，再不带 `-NoPull` 重跑。

**卸载。** 安装器：可以先加 `-DryRun`（`--dry-run`）看会删什么，再运行 `.\install.ps1 -Uninstall` 或 `./install.sh --uninstall`。卸载只删除指向本仓库的 `rumo-*` 链接和常驻基线，不碰其他来源的技能；clone 下来的仓库、`~/.rumo-engineering-skills/config.json` 和项目 Profile 都会保留，不再需要时手动删除。插件：执行 `claude plugin uninstall rumo-engineering-skills@rumo-engineering-skills`，然后开新会话。

不要在资源管理器里删除 `rumo-*` 链接，也不要用 `Remove-Item -Recurse` 删除：这些操作可能顺着链接删掉仓库里的技能文件。

## 进阶

<details>
<summary>项目 Profile</summary>

Profile 是可选的，不是使用技能的前提。仓库名称、组件清单、主机、服务名、安装目录和凭据应放在本地 Profile 或私有 Profile 仓库中，绝不放进本仓库。创建和填写方法见[新手指南](GETTING_STARTED.md#4-项目-profile可选)。

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

环境变量：

- `RUMO_SKILLS_REPO`：固定的本地仓库
- `RUMO_SKILLS_REMOTE`：克隆地址
- `RUMO_SKILL_PROFILES_REPO`：私有 Profile 仓库
- `RUMO_PROJECT_PROFILE`：显式指定 Profile
- `CODEX_HOME`、`CLAUDE_HOME`、`AGENTS_HOME`：自定义客户端目录

安装时加 `-ProfilesRepo <path>` 或 `--profiles-repo <path>` 可把 Profile 仓库路径保存到 `~/.rumo-engineering-skills/config.json`。

</details>

<details>
<summary>开发与校验</summary>

改技能或脚本前先读[贡献指南](CONTRIBUTING.md)。

```powershell
py -3 scripts\verify_skills.py
py -3 -m unittest discover -s scripts\tests -p "test_*.py"
py -3 scripts\run_auxiliary_tests.py
```

```bash
python3 scripts/verify_skills.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/run_auxiliary_tests.py
```

Windows 没有 `py` 启动器时改用 `python`。`install.sh` 的测试只在 Linux、macOS 或 WSL 中运行，在 Windows 上会被跳过。校验器检查命名、frontmatter、界面元数据、相对链接、按默认与扩展分组的目录清单、默认技能篇幅、description 长度、技能内脚本路径、触发用例覆盖、多余的许可文件、JSON 语法、疑似密钥和被跟踪的凭据文件。如需拦截私有词汇，把词条写入 `~/.rumo-engineering-skills/forbidden-terms.txt`（或 `RUMO_FORBIDDEN_TERMS_FILE` 指定的文件），每行一个，正则以 `re:` 开头；该文件不要放进仓库。

这些命令检查的是仓库，不是安装结果。安装结果的检查方法见[新手指南](GETTING_STARTED.md#2-验证安装)。

</details>

<details>
<summary>评测覆盖</summary>

自动选用由调用模型的评测覆盖，客户端为 Claude Code 和 Codex CLI；pi 运行器可以用任意模型做低成本初筛，但不能代替这两者的结论。行为评测覆盖单技能用例、跨技能的 `chain-*` 用例，以及会实际运行测试的 Codex 用例。其他客户端只验证过安装和加载。各项评测能证明什么，见 [CONTRIBUTING.md](CONTRIBUTING.md#trigger-evals)。

</details>

## 文档

- [新手指南](GETTING_STARTED.md)
- [技能目录](skills/README.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [更新记录](CHANGELOG.md) · [版本说明](https://github.com/rumoii/rumo-engineering-skills/releases/latest)

## 安全

- 不要提交密码、凭据文件、Token、私钥或含私有材料的证书。
- 安装器、Profile 解析、脚本、测试和报告都不得打印密钥值。
- 默认只访问 localhost 或明确标识为开发、测试的环境。生产环境需要精确授权，并且除非另行批准变更，一律只读。

漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要开公开 issue。

## Star 趋势

<a href="https://star-history.com/#rumoii/rumo-engineering-skills&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=rumoii/rumo-engineering-skills&type=Date&theme=dark">
    <img alt="Star 趋势" src="https://api.star-history.com/svg?repos=rumoii/rumo-engineering-skills&type=Date" width="600">
  </picture>
</a>

## 许可

MIT，见 [LICENSE](LICENSE)。
