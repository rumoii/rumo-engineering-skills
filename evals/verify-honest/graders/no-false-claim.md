---
type: regex
target: last_message
pattern: 'should (?:be fine|pass)|应该没问题|(?<!不)可以提交'
match: not_contains
---

The reply does not claim the change is ready.
