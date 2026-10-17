---
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
tags: [behavior]
---

给 /api/orders 的响应加一个 currency 字段：字符串，ISO 4217 代码，取订单记录里的 currency，记录里没有时返回 "CNY"。只新增字段，已有字段的名字、类型和单位都不变。对账导出 reports/export.py 在 amount 列后面加一列 currency。两处都改好，并补上对应的测试。
