---
name: rumo-study-guide
description: Use when creating a saveable HTML handout or study guide for repeated learning from a code repository, existing documents, or a topic needing research, including interview, exam, and project onboarding preparation. Do not use for a one-off explanation of current repository code (rumo-explain), research conclusions (rumo-research), a standalone engineering diagram or flowchart HTML preview (rumo-diagram), or a formal Word document (rumo-document-writing). The deliverable teaches through chapters, examples, self-tests, and review rather than only previewing a diagram.
---

# Rumo Study Guide

Produce an evidence-backed, reusable HTML guide for explaining, applying, and revisiting material.
Keep one reading layout; choose teaching components within each section.

## Workflow With Checkpoints

### 1. Establish The Reader And Purpose

Distinguish learning a system from preparing for a dated goal; confirm starting knowledge and target independence.
For interview, exam, or onboarding preparation, establish the deadline, study time, and success task.
Ask when essential context is missing.
Checkpoint: the reader, purpose, scope, and destination are known.

### 2. Define Observable Learning Goals

Write actions such as trace, explain, calculate, compare, or diagnose, not "understand X".
Read [references/writing.md](references/writing.md) before outlining.
Map each goal to evidence, explanation, a complete example, practice, and answer criteria.
For a sprint, order prerequisites and essential tasks first.
Checkpoint: each goal has a task the reader can attempt without the text.

### 3. Establish The Evidence

Read [references/sources.md](references/sources.md) before collecting material.
For repositories, record the commit and local changes, follow real call paths, and attach
file:line evidence. Run suitable examples when authorized.
For documents, preserve the source's claims and label added explanations.
For outside topics, follow rumo-research; if unavailable, use primary sources, check applicability, and expose disagreements.
Checkpoint: each key claim has a source or an explicit unknown label.

### 4. Write The Learning Units

Use question → explanation with adjacent figures → complete example → self-test.
Read [references/components.md](references/components.md) when choosing markup.
Distribute self-tests across chapters; the reader answers before the explanation unfolds, and each answer links back to its section.
Follow examples with similar tasks and add a reusable review question set.
Use prediction and experiments for mechanisms, code walkthroughs for code, and open retelling for synthesis.
For sprints, include priorities, estimated time, and a self-reported review list.
Label implemented behavior, inference, proposals, teaching-only examples, unchecked excerpts, and unresolved claims locally.
Checkpoint: answers explain why and retain the source's limits.

### 5. Build One Offline HTML File

Adapt [assets/template.html](assets/template.html); replace its demonstration content.
Keep the left contents column, inline learning components, and component switches.
Inline all styling, scripts, and illustrations; load no external resources.
Keep system/manual themes, presentation size, print styles, narrow layout, no-JavaScript reading and answers, and guarded localStorage.
Give each guide its own storage key; self-reports never certify mastery.
Checkpoint: the entire core lesson is available offline without scripting.

### 6. Verify The Artifact

Resolve all bundled `scripts/...` paths from this installed skill directory.
Run the checks in this order:
1. When embedding examples, `python scripts/build_examples.py <template.html> --out <guide.html> [--root <dir>]`,
   where `--root` is the directory the example paths are relative to. Inspect code first; allow only authorized, bounded local runs. Failure or timeout blocks verified output.
2. For code guides, `python scripts/verify_refs.py <guide.html> --root <dir> [--alias X=prefix/]... [--allow-empty]`
   on the built file, where `--root` is the source repository; require references unless the material truly contains none.
3. `node scripts/check_render.mjs <guide.html> [--out <dir>]` on the final file.
If Playwright is absent, report exit 2; obtain approval before any installation.
Try answering, revealing feedback, and following evidence/review links; inspect key claims and diagrams manually.
Readability is not proof of learning.

### 7. Deliver With Evidence Boundaries

Use the destination required by the user's workspace rules. Report four layers separately:
reference location, content checking, page usability, and learning effect.
Only reader feedback can support the last layer; do not infer it from
passing scripts. List files, exact checks, failures, and remaining uncertainties.

## Stop Conditions

- Ask before writing when the reader or learning goal remains unclear.
- Mark insufficient evidence as unresolved; never invent a missing fact.
- Stop before examples that need dependency installation or external services; get the user's approval first.
- Stop the affected check when a bundled helper or required runtime is missing; report the missing boundary rather than a pass.
- Do not add automatic grading, pretend AI feedback, or mastery claims based on scrolling or clicks.

## Evidence And Output

Deliver the single HTML file and a concise account of its sources and four verification layers.
Include the source revision or document date, checks actually run, and anything still requiring feedback or source checking.
