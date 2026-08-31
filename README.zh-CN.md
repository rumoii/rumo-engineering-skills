# Rumo Engineering Skills

[English](README.md) | 简体中文

一组可复用的 Codex、Claude Code 和智能体工程技能，不依赖特定公司、产品、仓库结构、主机或部署环境。

这是 `rumo-*` 技能命名空间的公共主仓库。这些技能适用于个人、团队和企业工程场景，但不包含任何组织专属的运维知识。

具体项目的仓库名称、组件清单、主机、服务名称、安装目录和凭据应保存在本地 Profile 或可选的私密 Profile 仓库中。可以使用自带的 `rumo-project-profile` 初始化程序创建本地 Profile；只有团队通过私密仓库共享 Profile 时才需要设置 `RUMO_SKILL_PROFILES_REPO`。

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

## 快速开始

如果你刚刚克隆本仓库，请阅读[新用户使用说明](GETTING_STARTED.md)。其中介绍了安装、校验、直接调用 Skill、可选本地 Profile 和凭据安全边界。

先克隆公共仓库：

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

如果客户端中已有同名 `rumo-*` 链接指向其他仓库，安装程序会在修改任何客户端前停止。只有明确要切换到本公共仓库时，才使用 `-ReplaceForeignLinks` 或 `--replace-foreign-links`。

安装程序只管理 `rumo-*` 链接，会保留其他命名空间和来源的 Skill。安装完成后，请新建一个智能体会话，让客户端重新加载 Skill 列表。

## Skill 清单

- `rumo-project-profile`: 为其他 Skill 解析和校验私密项目配置。
- `rumo-bug-root-cause`: 基于证据排查源码、运行时、数据、中间件、部署和客户端问题。
- `rumo-coding-guidelines`: 约束代码修改保持范围明确、改动最小并经过验证。
- `rumo-http-api`: 设计和审查兼容、安全、可重试、成本受控且可运维的 HTTP/JSON 接口。
- `rumo-code-review`: 执行一次只读的工程代码审查。
- `rumo-review-fix-loop`: 按需循环执行审查、修复、验证和复审。
- `rumo-change-verification`: 核对准确变更范围并选择最小充分验证。
- `rumo-test-evidence`: 根据风险规划测试和验收证据。
- `rumo-lifecycle-safety`: 处理资源所有权、重试、取消、超时、关闭和清理。
- `rumo-interface-evolution`: 安全演进 API、消息、配置和持久化格式。
- `rumo-database-change-safety`: 规划有边界的数据库变更、授权、备份、验证和回滚。
- `rumo-repository-gates`: 建立确定性的仓库 CI 和静态校验门禁。
- `rumo-engineering-decision`: 记录需要长期保留的重要工程决策。
- `rumo-find-simplifications`: 基于使用方和兼容性证据寻找可移除的工程复杂度。
- `rumo-prose-standard`: 规范注释、诊断、日志、仓库文档、提示词和界面文字。
- `rumo-daily-report`: 跨会话增量生成按日期保存的中文工程日报。
- `rumo-git-commit`: 按仓库约定完成提交、分支落地、历史整理、发布和推送。
- `rumo-frontend-dev`: 排查本地前端启动、代理、端口、证书和运行时配置。
- `rumo-frontend-ui`: 开发前端页面、复用组件、统一布局并执行视觉质量检查。
- `rumo-browser-evidence`: 生成可追溯的截图、页面状态、DOM 证据和可选 GIF。
- `rumo-incremental-deploy`: 依据 Profile 规划并指导有边界的制品部署、备份、验证和回滚。
- `rumo-offline-delivery-audit`: 审计离线制品完整性、来源、安装、回滚和验收边界。
- `rumo-old-coder`: 通过已批准的可执行规格和可复现验证链完成高可靠开发。
- `rumo-remote-memory-inspection`: 对远程 Linux 内存和性能问题进行只读检查。
- `rumo-linux-hardware-inventory`: 只读采集 Linux 硬件信息并生成简洁交付结果。
- `rumo-document-writing`: 编写和检查正式 Word 交付文档。
- `rumo-engineering-topology-diagram`: 建模、预览、导出和校验工程架构与拓扑图。
- `rumo-mermaid-diagram`: 创建 Mermaid 业务流程图并导出 PNG 或 SVG。
- `rumo-imagegen`: 通过用户配置的 OpenAI 兼容接口生成一张图片。
- `rumo-insight`: 基于本地 Codex 历史证据分析工程工作方式。

## 校验

Windows：

```powershell
py -3 scripts\verify_skills.py
py -3 -m unittest discover -s scripts\tests -p "test_*.py"
```

Linux 和 macOS：

```bash
python3 scripts/verify_skills.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

贡献或发布前还应执行各 Skill 自带的辅助测试：

```powershell
py -3 scripts\run_auxiliary_tests.py
```

```bash
python3 scripts/run_auxiliary_tests.py
```

校验器会检查 Skill 命名、Frontmatter、界面元数据、相对链接、JSON 语法、清单一致性、禁止出现的项目专属内容和被跟踪的凭据文件。

## 安装

请在一个稳定的本地仓库目录中运行安装程序。安装前会先执行校验，并且只替换 `rumo-*` 链接，不会影响其他 Skill。

```powershell
.\install.ps1 -NoPull
```

```bash
./install.sh --no-pull
```

可选环境变量：

- `RUMO_SKILLS_REPO`：本仓库的稳定本地目录。
- `RUMO_SKILLS_REMOTE`：自定义克隆地址。
- `RUMO_SKILL_PROFILES_REPO`：私密项目 Profile 仓库目录。
- `RUMO_PROJECT_PROFILE`：自动匹配存在歧义时明确指定的 Profile ID。
- `CODEX_HOME`、`CLAUDE_HOME`、`AGENTS_HOME`：自定义客户端主目录。

默认远程仓库：`https://github.com/rumoii/rumo-engineering-skills.git`。

PowerShell 安装程序在原生 Windows 上创建 Junction；Shell 安装程序在 macOS、Linux 和 WSL 上创建符号链接。增加、删除或重命名 Skill 后，需要重新运行安装程序。

## 安全

- 不要提交 `pwd.md`、包含凭据的 `.env` 文件、Token、私钥或包含私密材料的证书。
- 安装程序、Profile 解析、证据脚本、测试和报告都不得打印秘密值。
- 项目专属 Profile 必须保持私密，每次推送前都应确认远程仓库可见性。
- 默认只访问本机或用户明确指定的开发、测试环境。操作生产环境需要准确授权；除非用户另行授权修改，否则生产环境保持只读。

私密报告漏洞或意外泄露的方法请参阅[安全策略](SECURITY.md)，参与贡献请参阅[贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)。
