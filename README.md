<div align="center">

# Rumo Engineering Skills

让 AI 编程 agent 先问清、再动手、用证据交付的工程技能

[![版本](https://img.shields.io/github/v/release/rumoii/rumo-engineering-skills?label=%E7%89%88%E6%9C%AC&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/releases/latest)
[![Stars](https://img.shields.io/github/stars/rumoii/rumo-engineering-skills?label=Stars&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/stargazers)
[![许可证](https://img.shields.io/github/license/rumoii/rumo-engineering-skills?label=%E8%AE%B8%E5%8F%AF%E8%AF%81)](LICENSE)
![客户端](https://img.shields.io/badge/%E5%AE%A2%E6%88%B7%E7%AB%AF-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20SKILL.md-4b6b8a)

**[快速开始](#快速开始)** · [新手指南](GETTING_STARTED.md) · [技能清单](#默认技能) · [遇到问题](GETTING_STARTED.md#6-遇到问题) · [English](README.en.md)

</div>

一套精简的工程技能，适用于 Claude Code、Codex 以及其他能加载 `SKILL.md` 目录的 agent。技能本身不含任何公司、产品、主机或部署环境的信息。

不需要先学工程规范：装上之后，agent 会自己先问清需求、改完拿证据验证，遇到删库、删文件、改服务器这类操作会先停下来确认。

这套技能由我编写。我所在公司的研发部门自 2026 年 6 月起已有数十人在日常使用，他们用的是加入了具体业务内容的定制版；这里是去掉业务内容的通用版。

## 装上之后有什么不同

| 你说 | 没装时常见的做法 | 装上之后 |
| --- | --- | --- |
| “做个导出功能” | 猜一个方案直接开写 | 先把要确认的问题一次问完，每个问题附推荐选项（`rumo-clarify`） |
| “页面报 500，查一下” | 边猜边改代码 | 先复现、定位，用证据说明根因；没让修就不改代码（`rumo-debug`） |
| “把测试库的旧数据清掉” | 直接执行 `DELETE` | 先只读确认是哪个库、会影响多少行，备份和回滚准备好、你明确同意后才写（`rumo-database-change-safety`） |
| “做完了吗？” | 没跑测试就说“已完成” | 列出实际跑过的命令和结果，没跑的直接说明（`rumo-verify`） |

## 支持范围

| 客户端 | 安装方式 | 验证程度 |
| --- | --- | --- |
| Claude Code | 插件或安装器 | 安装、加载、自动选用评测、行为评测（含跨技能用例） |
| Codex | 安装器 | 安装、加载、自动选用评测、行为评测（含实际运行测试的用例） |
| 其他读取 `~/.agents/skills` 的客户端 | 安装器 + 共享目录 | 只验证过安装和加载 |

点名调用成功只说明客户端加载了技能，不说明它会根据自然语言自动选中技能。其他客户端的接入方式见[新手指南](GETTING_STARTED.md#其他客户端)。

## 快速开始

### Claude Code 插件

只用 Claude Code 时推荐这种方式，不需要 clone。在会话里执行，然后开一个新会话(需要 Claude Code 2.1.275 或更高版本)：

```text
/plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills
```

在终端里用 `claude plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills`(需要 2.1.292 或更高版本)。更早的版本先添加插件市场再安装：

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
```

AI 没收到这段提示词、只按 README 安装时，也遵守同一条规则：没有用户明确同意，绝不加 `--baseline` 或 `-Baseline`，因为它会改用户自己的说明文件。

### 用安装器安装

需要 Git 和 Python 3，不需要管理员权限。`-ExecutionPolicy Bypass` 只对这一次运行生效，不改系统设置。

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

安装器先校验仓库，再把默认技能链接到检测到的每个客户端(Codex、Claude Code 和共享的 `~/.agents` 目录)。它只管理 `rumo-*` 链接，不动其他技能。成功时每个客户端会输出一行 `<数量> skills linked in <目录>`，最后一行以 `Next:` 开头。装完开一个新会话，让客户端重新加载技能列表。

## 使用

装好后照常提需求，技能会按描述自动触发。日常主线：

```text
clarify -> plan -> test -> verify -> review -> git-commit
```

每一步对应一个技能，按需选用即可：一行就能改完的修复直接写代码并验证；含糊的功能需求先用 `rumo-clarify` 对齐。想指定技能时可以点名调用：

| 想做的事 | Codex | Claude Code |
| --- | --- | --- |
| 对齐含糊的需求 | `$rumo-clarify` | `/rumo-clarify` |
| 把已确认的工作拆成可验证的任务，再逐个执行 | `$rumo-plan` | `/rumo-plan` |
| 测试先行地实现 | `$rumo-test` | `/rumo-test` |
| 只读排查缺陷根因 | `$rumo-debug` | `/rumo-debug` |
| 声称完成前检查改动 | `$rumo-verify` | `/rumo-verify` |
| 只读评审差异 | `$rumo-review` | `/rumo-review` |
| 提交、合入、推送或开 PR | `$rumo-git-commit` | `/rumo-git-commit` |

标注“仅手动调用”的技能不会被自动选用，使用时必须点名。[完整案例](GETTING_STARTED.md#完整案例)展示了三个请求从提出到交付的全过程。

### 遇到问题

- 装不上、装完看不到技能、技能出现两次：先看新手指南的[遇到问题](GETTING_STARTED.md#6-遇到问题)，按看到的现象找对应小节。
- 安装器报错时，加 `-DryRun`(`--dry-run`)重跑，保存完整输出。
- 仍未解决：[提交问题](https://github.com/rumoii/rumo-engineering-skills/issues/new/choose)，附上 `-DryRun` 输出、`git rev-parse HEAD` 和客户端版本。issue 是公开的，贴出前删掉用户名、公司路径和代码。

## 默认技能

默认安装。

| 技能 | 用途 |
| --- | --- |
| `rumo-clarify` | 合并当前可回答的问题并给出推荐，必要时补问新决策；关键事项不擅自取默认值 |
| `rumo-plan` | 短规格加可验证的任务拆分、按任务逐个执行已确认的计划，或持久化的工程决策记录 |
| `rumo-coding-guidelines` | 基线纪律：基于真实代码路径，只做请求和必要的工作，并以验证收尾 |
| `rumo-test` | 证据规划、测试先行实现，以及高风险改动的规格加证据流程 |
| `rumo-debug` | 复现、定位并用证据证明根因；除非请求包含修复，否则只读 |
| `rumo-verify` | 声称完成前确定真实改动范围并跑最小充分检查；建设仓库门禁 |
| `rumo-review` | 只读评审差异或审计指定范围的现存问题；明确要求时进入修复循环、做可删复杂度审计、处理评审意见，或经你同意后调用本机另一个 CLI 跨模型复审 |
| `rumo-git-commit` | 按仓库约定提交、合入分支、整理历史、发布、推送、开 PR，以及跟进已开 PR 的 CI 检查 |
| `rumo-interface` | API、消息、配置和持久化格式的兼容演进，含 HTTP 契约检查 |
| `rumo-lifecycle-safety` | 长期运行任务的归属、重试、取消、超时、关闭与资源清理 |
| `rumo-database-change-safety` | 经授权、有备份、影响有界且可回滚的数据库写入 |
| `rumo-filesystem-safety` | 按影响范围分级处理删除与批量清理 |
| `rumo-remote-ops` | 远程 Linux 查询与变更、服务部署、备份恢复和制品部署 |
| `rumo-prose` | 保留全部事实的注释、报错、日志、界面文案、文档与 agent 文件 |
| `rumo-frontend` | 前端页面开发与新界面设计、可访问性检查、本地开发服务排障、按需采集浏览器证据 |
| `rumo-handoff` | 生成自包含的交接文档，便于其他会话或客户端接力(仅手动调用) |
| `rumo-project-profile` | 为其他技能解析和校验私有项目 Profile |

## 可选扩展

默认不安装，只能通过安装器添加，插件不含扩展。

| 技能 | 用途 |
| --- | --- |
| `rumo-diagram` | Mermaid 业务流程图与经确认的工程拓扑图，含预览与导出 |
| `rumo-document-writing` | 正式的 Word 交付文档 |
| `rumo-offline-delivery-audit` | 离线交付包的完整性、溯源、安装、回滚与验收边界 |
| `rumo-daily-report` | 按日期文本文件增量生成中文日报(仅手动调用) |
| `rumo-linux-inspect` | 只读采集 Linux 硬件配置或巡检内存(仅手动调用) |
| `rumo-imagegen` | 通过用户自配的 OpenAI 兼容接口生成单张图片(仅手动调用) |

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

客户端只在 description 与请求匹配时才加载技能，小改动可能跳过 `rumo-coding-guidelines` 的基线规则。安装器可以把这些规则的简短索引写进检测到的客户端的用户级说明文件：Claude Code 目录下的 `CLAUDE.md`，以及 Codex 目录下的 `AGENTS.md`。

```powershell
.\install.ps1 -NoPull -Baseline
.\install.ps1 -NoPull -RemoveBaseline
```

```bash
./install.sh --no-pull --baseline
./install.sh --no-pull --remove-baseline
```

写入的内容位于 `rumo-engineering-skills:baseline` 标记之间，标记之外的内容不会改动。之后不带参数重跑安装器时会自动更新这段内容；没写入过的，安装结束时会提示一行。插件用户和其他客户端可以直接运行辅助脚本，例如 `python3 skills/rumo-coding-guidelines/scripts/baseline_block.py --target ~/.claude/CLAUDE.md --install`，也可以手动把 [agents-snippet.md](skills/rumo-coding-guidelines/references/agents-snippet.md) 里的代码块贴进去。

## 更新与卸载

安装器只会写这几处：客户端技能目录里的 `rumo-*` 链接；你同意后写入 `CLAUDE.md`、`AGENTS.md` 的基线标记块；以及用 `-ProfilesRepo` 时保存的 `~/.rumo-engineering-skills/config.json`。

### 更新

安装器：去掉 `-NoPull`(`--no-pull`)重跑，它会先 `git pull --ff-only` 拉取最新版本，再重新链接，已装的扩展和基线会保留。然后开新会话。

```powershell
.\install.ps1
```

```bash
./install.sh
```

插件：先执行 `claude plugin marketplace update rumo-engineering-skills`，再执行 `claude plugin update rumo-engineering-skills@rumo-engineering-skills`，然后开新会话。

### 卸载

安装器：可以先加 `-DryRun`(`--dry-run`)看会删什么。卸载只删除指向本仓库的 `rumo-*` 链接和常驻基线，不碰其他来源的技能；clone 下来的仓库、`~/.rumo-engineering-skills/config.json` 和项目 Profile 都会保留，不再需要时手动删除。

```powershell
.\install.ps1 -Uninstall
```

```bash
./install.sh --uninstall
```

不要在资源管理器里删除 `rumo-*` 链接，也不要用 `Remove-Item -Recurse` 删除：这些操作可能顺着链接删掉仓库里的技能文件。

插件：执行 `claude plugin uninstall rumo-engineering-skills@rumo-engineering-skills`，然后开新会话。

## 项目 Profile

Profile 是可选的，不是使用技能的前提。仓库名称、组件清单、主机、服务名、安装目录和凭据应放在本地 Profile 或私有 Profile 仓库中，绝不放进本仓库。创建和填写方法见[新手指南](GETTING_STARTED.md#4-项目-profile可选)。

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

<details>
<summary>环境变量</summary>

- `RUMO_SKILLS_REPO`：固定的本地仓库
- `RUMO_SKILLS_REMOTE`：克隆地址
- `RUMO_SKILL_PROFILES_REPO`：私有 Profile 仓库
- `RUMO_PROJECT_PROFILE`：显式指定 Profile
- `CODEX_HOME`、`CLAUDE_HOME`、`AGENTS_HOME`：自定义客户端目录

安装时加 `-ProfilesRepo <path>` 或 `--profiles-repo <path>` 可把 Profile 仓库路径保存到 `~/.rumo-engineering-skills/config.json`。

</details>

## 开发与校验

改技能或脚本前先读[贡献指南](CONTRIBUTING.md)。

<details>
<summary>校验命令</summary>

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

Windows 没有 `py` 启动器时改用 `python`。`install.sh` 的测试只在 Linux、macOS 或 WSL 中运行，在 Windows 上会被跳过。校验器检查命名、frontmatter、界面元数据、相对链接、按默认与扩展分组的目录清单、默认技能篇幅、多余的许可文件、JSON 语法、疑似密钥和被跟踪的凭据文件。如需拦截私有词汇，把词条写入 `~/.rumo-engineering-skills/forbidden-terms.txt`(或 `RUMO_FORBIDDEN_TERMS_FILE` 指定的文件)，每行一个，正则以 `re:` 开头；该文件不要放进仓库。

这些命令检查的是仓库，不是安装结果。安装结果的检查方法见[新手指南](GETTING_STARTED.md#2-验证安装)。

</details>

<details>
<summary>评测覆盖</summary>

自动选用由调用模型的评测覆盖，客户端为 Claude Code 和 Codex CLI。行为评测覆盖单技能用例、跨技能的 `chain-*` 用例，以及会实际运行测试的 Codex 用例。其他客户端只验证过安装和加载。各项评测能证明什么，见 [CONTRIBUTING.md](CONTRIBUTING.md#trigger-evals)。

</details>

## 文档

- [新手指南](GETTING_STARTED.md)
- [技能目录](skills/README.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [版本说明](https://github.com/rumoii/rumo-engineering-skills/releases/latest)

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
