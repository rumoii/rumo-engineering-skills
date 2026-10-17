# Rumo Engineering Skills

[English](README.md) | 简体中文

一套精简的工程技能，适用于 Codex、Claude Code 以及其他能加载 `SKILL.md` 目录的 agent。技能本身不含任何公司、产品、主机或部署环境的信息；项目私有事实放在可选的本地 Profile 中。

## 工作主线

```text
clarify -> plan -> test -> verify -> review -> git-commit
```

每一步对应一个技能，按需选用即可：一行就能改完的修复直接写代码并验证；含糊的功能需求先用 `rumo-clarify` 对齐。

| 想做的事 | Codex | Claude Code |
| --- | --- | --- |
| 对齐含糊的需求 | `$rumo-clarify` | `/rumo-clarify` |
| 把已确认的工作拆成可验证的任务，再逐个执行 | `$rumo-plan` | `/rumo-plan` |
| 测试先行地实现 | `$rumo-test` | `/rumo-test` |
| 只读排查缺陷根因 | `$rumo-debug` | `/rumo-debug` |
| 声称完成前检查改动 | `$rumo-verify` | `/rumo-verify` |
| 只读评审差异 | `$rumo-review` | `/rumo-review` |
| 提交、合入、推送或开 PR | `$rumo-git-commit` | `/rumo-git-commit` |

客户端也会根据技能描述自动选择；除“仅手动调用”的技能外，点名不是必需的。

## 默认技能

默认安装。

| 技能 | 用途 |
| --- | --- |
| `rumo-clarify` | 需求不清时只问一轮带推荐答案的短问题；关键决策不明则暂停，绝不擅自取默认值 |
| `rumo-plan` | 短规格加可验证的任务拆分、按任务逐个执行已确认的计划，或持久化的工程决策记录 |
| `rumo-coding-guidelines` | 基线纪律：基于真实代码路径，只做请求和必要的工作，并以验证收尾 |
| `rumo-test` | 证据规划、测试先行实现，以及高风险改动的规格加证据流程 |
| `rumo-debug` | 复现、定位并用证据证明根因；除非请求包含修复，否则只读 |
| `rumo-verify` | 声称完成前确定真实改动范围并跑最小充分检查；建设仓库门禁 |
| `rumo-review` | 只读评审；明确要求时进入评审修复循环、做可删复杂度审计，或逐条处理别人给的评审意见 |
| `rumo-git-commit` | 按仓库约定提交、合入分支、整理历史、发布、推送与开 PR |
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

默认不安装，用 `-Extras`(PowerShell) 或 `--extras`(shell) 按需添加。

| 技能 | 用途 |
| --- | --- |
| `rumo-diagram` | Mermaid 业务流程图与经确认的工程拓扑图，含预览与导出 |
| `rumo-document-writing` | 正式的 Word 交付文档 |
| `rumo-offline-delivery-audit` | 离线交付包的完整性、溯源、安装、回滚与验收边界 |
| `rumo-daily-report` | 按日期文本文件增量生成中文日报(仅手动调用) |
| `rumo-linux-inspect` | 只读采集 Linux 硬件配置或巡检内存(仅手动调用) |
| `rumo-imagegen` | 通过用户自配的 OpenAI 兼容接口生成单张图片(仅手动调用) |

## 安装

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

安装器先校验仓库，再把默认技能链接到检测到的每个客户端(Codex、Claude Code 和共享的 `~/.agents` 目录)。它只管理 `rumo-*` 链接，不动其他技能。安装后重新开始一个 agent 会话，让客户端重新加载技能列表。客户端检测规则和 Profile 用法见 [GETTING_STARTED.md](GETTING_STARTED.md)。

管理扩展：

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

已安装的扩展在不带参数重跑安装器时会保留。

可选环境变量：`RUMO_SKILLS_REPO`(固定的本地仓库)、`RUMO_SKILLS_REMOTE`(克隆地址)、`RUMO_SKILL_PROFILES_REPO`(私有 Profile 仓库)、`RUMO_PROJECT_PROFILE`(显式指定 Profile)，以及 `CODEX_HOME`、`CLAUDE_HOME`、`AGENTS_HOME`(自定义客户端目录)。安装时加 `-ProfilesRepo <path>` 或 `--profiles-repo <path>` 可把 Profile 仓库路径保存到 `~/.rumo-engineering-skills/config.json`。

### Claude Code 插件

只用 Claude Code 时，也可以不 clone，直接把默认技能装成插件。在会话中执行(需要 Claude Code 2.1.275 或更高版本)：

```text
/plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills
```

在终端里用 `claude plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills`(需要 2.1.292 或更高版本)。更早的版本先添加插件市场再安装：

```bash
claude plugin marketplace add rumoii/rumo-engineering-skills
claude plugin install rumo-engineering-skills@rumo-engineering-skills
```

插件里的技能名带前缀，例如 `rumo-engineering-skills:rumo-clarify`。插件只对 Claude Code 生效，不含扩展；其他客户端仍用安装器。

同一台机器只选一种方式。安装器已经把技能链接进 `~/.claude/skills` 时再装插件，每个技能都会出现两次。更新插件：先执行 `claude plugin marketplace update rumo-engineering-skills`，再执行 `claude plugin update rumo-engineering-skills@rumo-engineering-skills`，然后开新会话。

### 常驻基线

客户端只在 description 与请求匹配时才加载技能，小改动可能跳过 `rumo-coding-guidelines` 的基线规则。想让这些规则每次会话都在，把 [agents-snippet.md](skills/rumo-coding-guidelines/references/agents-snippet.md) 里的代码块贴进项目或用户级的 `AGENTS.md`、`CLAUDE.md`。它是一份指回技能本身的简短索引，同时写明每一步该用哪个技能。

## 项目 Profile

Profile 是可选的。仓库名称、组件清单、主机、服务名、安装目录和凭据应放在本地 Profile 或私有 Profile 仓库中，绝不放进本仓库。

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

## 校验

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

这些命令检查的是仓库，不是安装结果。安装后先确认链接(`ls -l ~/.claude/skills`)或 `claude plugin list`，再开新会话点名调用一个技能，例如 `/rumo-verify`，插件方式为 `/rumo-engineering-skills:rumo-verify`。点名调用成功只说明客户端加载了技能，不说明客户端会自动选中它。

## 安全

- 不要提交密码、凭据文件、Token、私钥或含私有材料的证书。
- 安装器、Profile 解析、脚本、测试和报告都不得打印密钥值。
- 默认只访问 localhost 或明确标识为开发、测试的环境。生产环境需要精确授权，并且除非另行批准变更，一律只读。

漏洞报告见 [SECURITY.md](SECURITY.md)，贡献规则见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

MIT，见 [LICENSE](LICENSE)。
