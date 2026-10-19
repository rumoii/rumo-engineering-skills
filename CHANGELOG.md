# 更新记录

每个版本的完整说明见 [GitHub Releases](https://github.com/rumoii/rumo-engineering-skills/releases)。插件用户只在 `.claude-plugin/plugin.json` 的 `version` 提升后才会收到更新，所以每次发版都要提升版本号，并在这里补一节。

## 未发布

- `rumo-review`：新增评审结论取舍规则，适用于独立评审、评审机器人和他人意见；经用户同意后，可以调用本机另一个 CLI 做跨模型只读复审。
- `rumo-git-commit`：用户明确要求时，可跟进已开 PR 的 CI 检查。等待期间不轮询；修复前先给失败分类；修好后提交、推送仍需用户明确要求；不合并 PR，也不标记 ready。
- `rumo-plan`：出方案时，各选项须在结构上真正不同，并对照三类设计问题自查。
- 新增扩展 `rumo-reflect`：复盘当前会话中反复出现的错误和用户的纠正，逐条与用户讨论该在哪里修正，用户批准后才改；用户要求复盘时自动加载，被反复纠正时 agent 会在交付时提议复盘，但不会自动开始。
- 评测：被测 agent 能看到的提示、git 元数据和工作路径中，不再出现评测相关字样；运行器拒绝名称里含这类字样的输出目录。
- 插件清单新增 `version` 字段，并新增本文件。

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
