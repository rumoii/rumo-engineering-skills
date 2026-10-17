---
type: regex
target: {source: file, path: test_loader.py}
pattern: 'self\.assertEqual\(load_ids\("ids\.txt"\)\[0\], "alpha"\)'
---

The failing assertion stays; adding a regression test beside it is fine.
