# Source Responsibilities

Read this before collecting evidence. Mixed-source guides share one teaching
workflow but retain the evidence boundary of each individual claim.

| Material | Evidence responsibility | Checks before writing |
| --- | --- | --- |
| Code repository | Pin the revision; distinguish source behavior, observed execution, and inferred design intent | Record commit and relevant local changes; read the real entry point and producer/consumer chain; inspect conditions, failures, and tests; attach file:line references; run suitable bounded examples when authorized |
| Existing documents | Attribute the author's statements at their original date; separate added explanations and independent verification | Record title, source, version/date, and section; compare rewrites with the original; preserve scope, caveats, and units; flag excerpts whose underlying sources remain unchecked |
| External research | Check important claims, applicability, disagreements, and uncertainty rather than teaching a contested claim as the only answer | Use rumo-research when available; otherwise consult primary documentation or research, verify changing facts and source dates, compare conflicting accounts, and cite each substantive conclusion |

## Repository Evidence

Record whether the guide describes the pinned commit or named local changes.
Read actual branches and call sites instead of assuming a function name proves
its role. Use `data-p`, `data-l`, and `data-s` on source-reference elements as
described in [components.md](components.md). Keep paths relative to the declared
root, with aliases only when needed for multiple roots. Include visible path
and line text so readers can locate evidence without an editor integration.

`scripts/verify_refs.py` checks file existence, line range, and a substring on
that line. It does not establish call order, meaning, correctness, deployment,
or learning. Manually check claims against surrounding conditions and callers.
Zero references fail unless `--allow-empty` was deliberately chosen for material
that has no source references; never use that option to conceal missing evidence.

For examples, inspect all executable code and its local dependencies first.
Do not execute untrusted or state-changing material merely to obtain an output.
Record inputs, runtime, command, result, and any isolation used. A source-only
snippet remains unrun. An actual local result does not prove production behavior.

## Document Evidence

Preserve the original source or a link with its version when the destination
rules allow it; a new Markdown manuscript is not mandatory. Identify the file
that owns future content edits and regenerate HTML when necessary. Do not modify
the original silently to make it agree with the lesson.

Mark paraphrases, diagrams, and supplemental explanations as additions where
they could be mistaken for original claims. If a document describes code that
was not checked, say "摘录未核对" near the excerpt. Source availability alone
does not make its claims true. For contradictions, retain both scopes or mark
the disputed point "未查明" instead of inventing a resolution.

## Research Evidence

Keep source links, publication/version dates, and the conditions under which a
result holds. Distinguish a study's measured finding from the author's opinion
and your teaching recommendation. Inspect methods and limitations before using
a numerical result; do not transfer a whole-system result to one HTML component.
Explain competing views and teach the conditions that decide between them.

## Report Four Independent Layers

| Layer | Report evidence for | Cannot establish |
| --- | --- | --- |
| Reference location | Files, lines, and expected strings resolve at the chosen revision | Correct interpretation |
| Content checking | Named claims, examples, diagrams, and answers were compared with sources or runs | Complete coverage of every claim unless actually checked |
| Page usability | Browser checks, offline/no-JS/print checks, and exercised learning controls | Reader learning |
| Learning effect | Reader feedback and independent or delayed attempts, with context | Universal benefits, or gains inferred from rendering success |

Report unperformed layers explicitly. Keep the destination and checks within
the user's authorization; stop affected execution for installation or external
service approval as required by the skill body.
