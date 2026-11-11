# Writing For The Reader

Read this before drafting chapters, and again before the cold read. The guide is
for someone learning, not for someone auditing the author. Accuracy is still
required; the evidence goes to `report.md`, and the text explains.

## Know The Reader

Write a short reader profile before the outline: what the reader already does
every day, which words they already use, and what they have never opened. A
reader who uses a tool daily but has never read its source needs the purpose
and the everyday situation first, and code only as evidence for an idea already
explained. Write for that person, not for the author of the source.

## Shape Of Each Section

- Start from the reader's world: where they meet this, what goes wrong without
  it, or the question they would actually ask. Mechanism comes second.
- Carry one concrete picture through the chapter: a real request, a familiar
  object, or a small story. Reuse it instead of switching images.
- One idea per paragraph, and short paragraphs. When a section needs more than
  four or five, split it or cut it.
- After a mechanism, give the consequence the reader can use: "so when X
  happens, look at Y first".

## Words

- Explain a term the first time it appears, in one plain sentence, or avoid it.
  Count the unexplained terms in a paragraph; more than one means rewrite.
- Prefer the reader's verbs: "picks", "puts", "checks", not internal names for
  the same action. Use the source's exact name when the reader must find it in
  the code, and translate it once.
- Translate code line by line into what it does in the reader's terms. A list
  of function names is not an explanation.
- Leave out what only the author needs: revision hashes, test counts, internal
  ticket names, and how the guide was produced.

## Limits Without Hedging

Say a limit once, plainly, where it changes what the reader may conclude. Do
not attach evidence labels, "inference", or "not measured" to sentences the
reader would read the same way either way. One honest sentence such as "这段代码
是为讲解写的小例子" replaces a label on every line.

## Before And After

Taken from a guide whose readers found the first version unreadable.

Before:

> 仓库分发的是能被客户端读取的 SKILL.md 目录；Python 辅助脚本、安装器和仓库检查围绕这些目录服务。技能正文让 agent 知道应怎样工作，脚本才执行可确定的部分。这里没有一套在后台自行调度所有技能的产品程序。前一句是仓库定位；最后一句是基于入口结构的推断，没有检查所有客户端内部实现。

After:

> 书架上有二十多本操作手册，agent 没法每本都翻一遍。它只看书脊上的书名和封底的简介，挑出最对题的那本，拿下来以后才读正文，照着里面的步骤干活。

Before:

> 只修改 openai.yaml 的中文 short_description，能证明误触发已经修复吗？请给出证据缺口。

After:

> 只把 openai.yaml 里的中文简介写得更清楚，用错技能的问题能解决吗？

The first version is accurate but is written to defend each claim. The second
picks the reader's question, uses one picture, and keeps the same facts.
