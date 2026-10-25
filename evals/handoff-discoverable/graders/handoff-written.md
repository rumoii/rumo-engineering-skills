---
type: regex
target: {source: file, path: notes/tasks/csv-export/HANDOVER.md}
pattern: '^(?=[\s\S]*python -m unittest test_export)(?=[\s\S]*(?:documentation|文档))'
flags: i
---

The handoff records both the passing test command and the unwritten user documentation.
