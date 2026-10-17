---
type: regex
target: {source: file, path: tests/test_service.py}
pattern: '(?:assertRaises|raises)\(\s*PermissionDenied'
---

The tests cover the denied path, not only the allowed one.
