# 新用户使用说明

这份说明适合“已经把 `rumo-engineering-skills` clone 到本地，但还不知道下一步做什么”的情况。

如果还没有 clone，先执行：

```powershell
git clone https://github.com/rumoii/rumo-engineering-skills.git
```

```bash
git clone https://github.com/rumoii/rumo-engineering-skills.git
```

## 1. 安装到 Codex

先进入 clone 后的目录。Windows PowerShell：

```powershell
cd E:\path\to\rumo-engineering-skills
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -NoPull
```

Linux/macOS/WSL：

```bash
cd /path/to/rumo-engineering-skills
./install.sh --no-pull
```

安装脚本会把每个 `rumo-*` 技能链接到 Codex 的 skills 目录。它只管理
`rumo-*`，不会删除其他来源的技能。安装完成后，重新开始一个 Codex 会话，
让技能列表重新加载。

## 2. 先验证安装

在仓库根目录运行：

```powershell
py -3 scripts\verify_skills.py
```

```bash
python3 scripts/verify_skills.py
```

看到 `Rumo skill validation passed` 后，说明仓库内的技能结构有效。

## 3. 不需要项目配置时，直接使用技能

Profile 不是使用技能的前置条件。可以直接在 Codex 中提出任务，例如：

```text
请使用 $rumo-code-review，检查当前分支的未提交修改。
```

```text
请使用 $rumo-frontend-ui，分析当前页面的布局问题，但先不要修改代码。
```

```text
请使用 $rumo-test-evidence，为这个接口变更设计最小充分的测试证据。
```

技能会先根据当前仓库发现事实；没有 Profile 时，不会因为缺少项目配置而直接失败。

## 4. 有项目配置时，创建自己的本地 Profile

即使项目还没有建立，也可以先创建 Profile：

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
$env:RUMO_PROJECT_PROFILE = "my-project"
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
export RUMO_PROJECT_PROFILE=my-project
```

默认目录是：

```text
Windows: %USERPROFILE%\.rumo-skill-profiles\profiles\my-project\
Linux/macOS: ~/.rumo-skill-profiles/profiles/my-project/
```

刚创建时文件内容可以是空数组。项目建立后，再填写仓库路径、技术栈、启动命令、
运行环境和参考资料。可以用下面的命令检查：

```powershell
py -3 skills\rumo-project-profile\scripts\verify_profile.py `
  --profiles-root "$env:USERPROFILE\.rumo-skill-profiles"
```

```bash
python3 skills/rumo-project-profile/scripts/verify_profile.py \
  --profiles-root "$HOME/.rumo-skill-profiles"
```

然后在任务中明确要求使用 Profile：

```text
请使用 $rumo-project-profile 读取 my-project 的项目配置，
再使用 $rumo-frontend-dev 帮我分析本地启动问题。
```

## 5. 凭据和私有信息

- 不要把密码、Token、私钥或证书写入公共 `rumo-engineering-skills` 仓库。
- 个人可以把凭据放在本机 ignored 文件或环境变量中。
- 团队需要共享项目事实时，可以把 Profile 放入自己的私有仓库；这不是使用技能的必需步骤。
- 不要把任何组织或项目的私有 Profile 复制到公共仓库。

## 最短流程

如果只是想马上开始，Windows 下执行：

```powershell
cd E:\path\to\rumo-engineering-skills
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -NoPull
```

然后在 Codex 中直接说：

```text
请使用 $rumo-coding-guidelines，帮我实现这个需求，并保持最小改动。
```
