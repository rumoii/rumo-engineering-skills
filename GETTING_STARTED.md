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
| 共享 agents 目录 | `grok` 命令、`~/.grok`，或显式 `AGENTS_HOME` / `-AgentsHome` / `--agents-home` | `~/.agents/skills` |

- 未检测到的客户端会跳过；一个都没检测到时直接失败，不做任何改动。
- 安装器只管理 `rumo-*` 链接，不会删除其他来源的技能。
- 同名链接如果来自另一个仓库，安装器会先停下；确认要切换来源后再加 `-ReplaceForeignLinks` / `--replace-foreign-links`。
- 安装完成后重新开一个客户端会话，让技能列表重新加载。

### 可选扩展

图表、Word 文档、前端、离线交付审计、日报、Linux 巡检、图片生成这几类技能默认不装，需要时再加：

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

## 2. 验证安装

```powershell
py -3 scripts\verify_skills.py
```

```bash
python3 scripts/verify_skills.py
```

Windows 没有 `py` 启动器时把 `py -3` 换成 `python`。看到 `Rumo skill validation passed` 即说明技能结构有效。

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

`rumo-handoff`、`rumo-project-profile`，以及扩展里的 `rumo-daily-report`、`rumo-linux-inspect`、`rumo-imagegen` 是仅手动调用的技能：不会被客户端自动选用，使用时必须点名，例如 `$rumo-handoff 整理交接文档`。

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
