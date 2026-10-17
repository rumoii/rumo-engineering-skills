---
type: regex
target: {source: file, path: api/orders.py}
pattern: '"currency"[\s\S]*"CNY"|"CNY"[\s\S]*"currency"'
---

The response adds currency with the stated default.
