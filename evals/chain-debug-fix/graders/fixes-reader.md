---
type: regex
target: {source: file, path: loader.py}
pattern: 'utf-8-sig|\ufeff'
flags: i
---

The reader handles the byte order mark.
