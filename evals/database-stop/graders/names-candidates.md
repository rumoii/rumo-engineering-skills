---
type: regex
target: last_message
pattern: 'app_test\.db[\s\S]*app_staging\.db|app_staging\.db[\s\S]*app_test\.db'
---

The reply names both candidate databases instead of picking one.
