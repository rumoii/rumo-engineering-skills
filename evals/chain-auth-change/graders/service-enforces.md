---
type: regex
target: {source: file, path: orders/service.py}
pattern: 'raise PermissionDenied'
---

The service rejects callers who are neither admin nor owner.
