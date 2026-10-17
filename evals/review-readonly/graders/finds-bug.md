---
type: regex
target: last_message
pattern: 'paid_total|超[过出](?:订单)?(?:已|实)?付|(?:没有|无|缺少?)(?:金额)?上限|不限制(?:退款)?金额|(?:没|未)(?:有)?(?:跟|和|与)(?:订单)?(?:实付|已付|订单)?金额比较|超额退款|exceeds? (?:the )?(?:amount )?paid|more than (?:was )?paid|over-?refund|no upper (?:bound|limit)'
flags: i
---

The review names the lost upper bound: a refund can now exceed the amount paid.
