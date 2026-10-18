# 新用户使用说明

适合“已经把 `rumo-engineering-skills` clone 到本地，但不知道下一步做什么”的情况。还没 clone 的话先执行：

```bash
git clone https://github.com/rumoii/rumo-engineering-skills.git
```

## 1. 安装

Windows PowerShell：

```powershell
cd E:\path\to\rumo-engineering-skills
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -NoPull
```

Linux/macOS/WSL：

```bash
cd /path/to/rumo-engineering-skills
./install.sh --no-pull
```

安装器会检测本机客户端，把默认技能链接进对应的 skills 目录：

| 客户端 | 检测条件 | 技能目录 |
|--------|----------|----------|
| Codex | `codex` 命令、`~/.codex`，或显式 `CODEX_HOME` / `-CodexHome` / `--codex-home` | `~/.codex/skills` |
| Claude Code | `claude` 命令、`~/.claude`，或显式 `CLAUDE_HOME` / `-ClaudeHome` / `--claude-home` | `~/.claude/skills` |
| 共享 agents 目录 | `~/.agents` 已存在、`grok` 命令、`~/.grok`，或显式 `AGENTS_HOME` / `-AgentsHome` / `--agents-home` | `~/.agents/skills` |

- 未检测到的客户端会跳过；一个都没检测到时直接失败，不做任何改动。
- 安装器只管理 `rumo-*` 链接，不会删除其他来源的技能。
- 同名链接如果来自另一个仓库，安装器会先停下；确认要切换来源后再加 `-ReplaceForeignLinks` / `--replace-foreign-links`。
- 成功时每个客户端会输出一行 `<数量> skills linked in <目录>`，最后一行以 `Next:` 开头，提示下一步。
- 安装完成后重新开一个客户端会话，让技能列表重新加载。
- 装不上或装完看不到技能，见[遇到问题](#6-遇到问题)。
- 想让基线规则每次会话都生效，加 `-Baseline` / `--baseline`，见 README 的“常驻基线”；让 AI 代你安装时，用 README“让 AI 帮你安装”一节的提示词。

只用 Claude Code 的话，也可以不跑安装器，改为把默认技能装成插件，见 README 的“Claude Code 插件”一节。两种方式只能选一种，否则技能会重复出现。

### 可选扩展

图表、Word 文档、离线交付审计、日报、Linux 巡检、图片生成这几类技能默认不装，需要时再加：

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

### 其他客户端

安装器只直接管理上表的三个目录。其他客户端统一接到共享目录 `~/.agents/skills`，以后增减扩展只需重跑安装器，更新见 README 的“更新”一节。如果安装器没有检测到共享目录，安装时显式加 `-AgentsHome "$HOME\.agents"` 或 `--agents-home ~/.agents`。

| 客户端 | 接入方式 |
| --- | --- |
| deepseek harness、pi | 默认会读 `~/.agents/skills`，无需设置。如果在 pi 的 `settings.json` 的 `skills` 里另外写了本仓库路径，请删掉，以免重复加载 |
| qwen、grok 等只读自己目录的客户端 | 把它们的技能目录（例如 `~/.qwen/skills`、`~/.grok/skills`）换成指向 `~/.agents/skills` 的链接，见下方命令 |
| hermes | 在 hermes 的 `config.yaml` 中，把共享目录的绝对路径加入 `skills.external_dirs` |

建链接前，先确认原技能目录里没有其他来源的技能。如果有，先把它们移走，或者只为 `rumo-*` 单独建链接。

```powershell
New-Item -ItemType Junction -Path "$HOME\.qwen\skills" -Target "$HOME\.agents\skills"
```

```bash
ln -s ~/.agents/skills ~/.qwen/skills
```

```yaml
skills:
  external_dirs:
    - C:/Users/<you>/.agents/skills
```

有的客户端会同时读多个目录，例如 grok 开启 Claude 兼容时还会读 `~/.claude/skills`，这时同一个技能可能出现两次。遇到这种情况，关掉其中一个来源即可。各客户端的读取规则以其官方文档为准。

## 2. 验证安装

分三层确认，每层只证明自己那一层。

**第一层：仓库结构有效。**

```powershell
py -3 scripts\verify_skills.py
```

```bash
python3 scripts/verify_skills.py
```

Windows 没有 `py` 启动器时把 `py -3` 换成 `python`。看到 `Rumo skill validation passed` 说明技能文件本身没问题，但不说明已经装好。

**第二层：安装状态正确。**

用安装器时，检查客户端目录里的 `rumo-*` 链接都指向本仓库的 `skills/`(装了扩展的还有 `extras/`)。数量与 README 技能清单里的默认技能一致：

```powershell
Get-ChildItem "$HOME\.claude\skills" | Where-Object Name -like 'rumo-*' | Select-Object Name, LinkType, Target
```

```bash
ls -l ~/.claude/skills | grep ' rumo-'
```

把 `.claude` 换成 `.codex` 或 `.agents` 可以检查其他目录。用插件时，执行 `claude plugin list`，确认 `rumo-engineering-skills` 已安装并启用。

**第三层：新会话能调用。**

重新开一个客户端会话，点名调用一个技能，例如 Codex 用 `$rumo-verify`，Claude Code 用 `/rumo-verify`，插件方式用 `/rumo-engineering-skills:rumo-verify`。技能正常执行说明客户端已加载它。

点名调用成功不代表自动选择也没问题：客户端会不会根据自然语言描述选中正确的技能，这三层都不检查。

## 3. 开始使用

日常主线是 `clarify -> plan -> test -> verify -> review -> git-commit`，按任务大小取用其中几步。点名技能时，Codex 用 `$rumo-xxx`，Claude Code 用 `/rumo-xxx`；也可以只用自然语言描述，由客户端按技能描述自动选择。

示例(Codex 写法，Claude Code 把 `$` 换成 `/`)：

```text
$rumo-clarify 我想给订单列表加个导出功能。
```

```text
$rumo-debug 登录后偶尔跳回首页，先只读排查原因。
```

```text
$rumo-review 检查当前分支的未提交修改。
```

```text
$rumo-verify 我改完了，帮我确认可以提交。
```

`rumo-handoff`，以及扩展里的 `rumo-daily-report`、`rumo-linux-inspect`、`rumo-imagegen` 是仅手动调用的技能：不会被客户端自动选用，使用时必须点名，例如 `$rumo-handoff 整理交接文档`。

### 完整案例

下面三个案例取自仓库行为评测(`evals/chain-*` 和 Codex 的 `auth-change-verify`、`debug-then-fix`)的实际运行记录，只保留关键步骤。

**小改动保持轻量**

- 请求：`把 web/login.html 里登录按钮的文案从“登录”改成“进入工作台”。`
- 技能：不需要点名，也不会走 clarify 或 plan。
- 过程：读文件，改一行，只动这个文件，不新建测试或计划文件。
- 交付：一处改动和一句说明，四五轮对话即可完成。

**鉴权变更补齐验证**

- 请求：`给 orders/service.py 的 delete_order 加权限校验：只有 admin 角色或订单的下单人能删除，其他人抛 PermissionDenied。`
- 技能：`rumo-coding-guidelines` 打底，`rumo-test` 把它判为高风险改动。
- 过程：先补“下单人可删”和“他人被拒”的测试，确认它们在旧实现上失败；再实现校验，让权限判断在删除之前完成；最后运行全部测试。
- 交付：只改实现文件和测试文件，报告运行过的命令与结果，并写明验证范围只到本地的 FakeStore。没法运行测试时如实说明，不写“应该能通过”。

**只读排查转修复**

- 第一轮请求：`test_loader 挂了，读出来的第一个 ID 和预期不符。先只读查清原因并给出证据，不要改代码。`
- 技能：`rumo-debug`。
- 过程：读出文件头字节是 `EF BB BF`，用失败输出 `'﻿alpha' != 'alpha'` 证明是 UTF-8 BOM；全程不改文件。
- 第二轮请求：`原因确认了，按你的结论修好，并跑测试确认。`
- 过程：沿用上一轮的证据，不再从头排查；把读取编码改成 `utf-8-sig`，数据文件和原有断言都不动，重跑测试。
- 交付：一行修复，附通过的测试输出。

## 4. 项目 Profile(可选)

Profile 不是使用技能的前提。没有 Profile 时，技能会先从当前仓库发现事实。需要固定的项目配置时再创建：

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
$env:RUMO_PROJECT_PROFILE = "my-project"
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
export RUMO_PROJECT_PROFILE=my-project
```

默认目录：

```text
Windows: %USERPROFILE%\.rumo-skill-profiles\profiles\my-project\
Linux/macOS: ~/.rumo-skill-profiles/profiles/my-project/
```

刚创建时文件可以是空数组，项目建立后再填写仓库路径、技术栈、启动命令、运行环境和参考资料。检查格式：

```powershell
py -3 skills\rumo-project-profile\scripts\verify_profile.py `
  --profiles-root "$env:USERPROFILE\.rumo-skill-profiles"
```

```bash
python3 skills/rumo-project-profile/scripts/verify_profile.py \
  --profiles-root "$HOME/.rumo-skill-profiles"
```

团队使用私有 Profile 仓库时，安装时加 `-ProfilesRepo <path>` 或 `--profiles-repo <path>`，安装器只保存该路径。

## 5. 凭据和私有信息

- 不要把密码、Token、私钥或证书写进本仓库。
- 个人凭据放在本机被忽略的文件或环境变量里。
- 团队共享项目事实时，放进自己的私有 Profile 仓库；这不是使用技能的必需步骤。
- 不要把任何组织或项目的私有 Profile 复制到公共仓库。

## 6. 遇到问题

按看到的现象找对应小节。安装器报错时，提示原文是英文，可以直接搜索原文。

### 新会话里看不到 rumo-* 技能

1. 看安装器的输出里有没有 `skills linked in` 开头的那几行，目录是不是你在用的客户端(`.claude`、`.codex` 或 `.agents`)。缺了某个客户端，说明安装器没检测到它，用 `-ClaudeHome` / `--claude-home` 这类参数显式指定目录后重跑。
2. 按[第 2 节](#2-验证安装)第二层检查链接。
3. 一定要开新会话，已经打开的会话不会重新加载技能列表。
4. 用插件安装时，执行 `claude plugin list` 确认插件已启用；插件的技能名带前缀，例如 `/rumo-engineering-skills:rumo-verify`。

### 每个技能出现两次

同时用了安装器和插件，或者客户端同时读取多个技能目录(见[其他客户端](#其他客户端))。只保留一种方式：保留插件，就运行 `.\install.ps1 -Uninstall` 删掉安装器建的链接；保留安装器，就按 README 的“卸载”一节卸载插件。

### 提示 `Git is required` 或 `Python 3 is required`

按提示里的命令安装，Windows 上是 `winget install --id Git.Git` 或 `winget install --id Python.Python.3.12`。装完关掉终端再重新打开，让新的 PATH 生效，然后重跑安装器。安装器在这一步退出时没有改动任何东西。

如果 Windows 上执行 `python --version` 打开了 Microsoft Store 或没有任何输出，说明只有系统自带的占位程序，仍然需要按上面的命令安装 Python。

### 提示 `exists as a real file or directory`

客户端的技能目录里已经有一个同名的普通目录，例如以前手动复制过技能。安装器不会覆盖它。确认里面没有你自己改过的内容后，把它移走或改名，再重跑安装器。

### 提示 `points to ... use -ReplaceForeignLinks`

同名链接指向另一个仓库，例如你在别处另外 clone 过一份。确认要改用当前这份时，加 `-ReplaceForeignLinks`(`--replace-foreign-links`)重跑。

### PowerShell 提示“因为在此系统上禁止运行脚本”

直接运行了 `.\install.ps1`。改用完整命令 `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -NoPull`；或者先在同一个窗口里执行 `Set-ExecutionPolicy -Scope Process Bypass`，之后就能直接运行 `.\install.ps1`。这两种方式都只对当前这次运行或当前窗口生效。

### 插件命令报 unknown option，或者不认识 `--marketplace`

Claude Code 版本太旧。执行 `claude --version` 查看版本：低于 2.1.275 时，升级 Claude Code，或者按 README“Claude Code 插件”一节先添加插件市场再安装。

### 还是解决不了

开 issue 时附上下面三项，贴出前删掉用户名、公司路径和其他敏感信息：

- 安装器加 `-DryRun`(`--dry-run`)重跑的完整输出；
- `git -C <仓库路径> rev-parse HEAD` 的输出；
- 客户端名称和版本。
