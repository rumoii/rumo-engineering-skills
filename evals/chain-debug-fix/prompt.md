---
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
tags: [behavior]
---

test_loader 在 CI 上挂了，输出在 ci.log：读出来的第一个 ID 和预期不符。先查清原因，确认后直接修好。
