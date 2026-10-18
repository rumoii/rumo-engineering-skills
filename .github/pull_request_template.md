<!-- 贡献规则见 CONTRIBUTING.md，中英文都可以。一个 PR 只做一件事。 -->
<!-- See CONTRIBUTING.md. Chinese or English is fine. One change per pull request. -->

## 改了什么 / What changed

<!-- 动了哪些技能、脚本或文档；agent 的行为前后有什么不同。 -->

## 为什么 / Why

<!-- 用户场景：agent 在什么请求下做错了，或者缺了什么。有 issue 就写 Fixes #编号。 -->

## 范围 / Scope

- [ ] 默认技能 / default skills (`skills/`)
- [ ] 可选扩展 / extras (`extras/`)
- [ ] 安装脚本或插件 / installers or plugin
- [ ] 评测、辅助脚本或文档 / evals, scripts, or docs

## 验证 / Verification

<!-- 只勾实际跑过的。没跑的写明原因，以及哪些环境或场景没有覆盖。 -->

- [ ] `python scripts/verify_skills.py`
- [ ] `python -m unittest discover -s scripts/tests -p "test_*.py"`
- [ ] `python scripts/run_auxiliary_tests.py`
- [ ] 改了某个 `description`：跑过 trigger evals，下面写明客户端、版本和结果 / changed a `description`: ran trigger evals
- [ ] 改写或删减了技能正文：跑过 behavior evals 或 `scripts/run_regression.py`，下面写明结果 / rewrote or trimmed skill text: ran behavior evals or the regression set

## AI 使用说明 / AI disclosure

<!-- 必填。没用 AI 就写“没有使用”。用了就写出具体工具和模型版本，不要只写“AI”。 -->

- 是否使用 AI / Used AI:
- 工具和模型版本 / Tool and model version:
- 用在哪里（找问题 / 写技能 / 写脚本 / 写测试）/ Used for:
- [ ] 我逐行读过全部改动；技能文本是自己写的，没有照搬其他项目 / I read every changed line, and the skill text is written in my own words
