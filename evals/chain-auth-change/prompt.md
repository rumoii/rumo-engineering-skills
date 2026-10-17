---
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
tags: [behavior]
---

给 orders/service.py 的 delete_order 加权限校验：只有 admin 角色或订单的下单人能删除，其他人抛 PermissionDenied。
