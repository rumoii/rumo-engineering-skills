---
name: rumo-study-guide
description: Use when creating a saveable HTML handout or study guide for repeated learning from a code repository, existing documents, or a topic needing research, including interview, exam, and project onboarding preparation. Do not use for a one-off explanation of current repository code (rumo-explain), research conclusions (rumo-research), a standalone engineering diagram or flowchart HTML preview (rumo-diagram), or a formal Word document (rumo-document-writing). The deliverable teaches through chapters, examples, self-tests, and review rather than only previewing a diagram.
---

# Rumo Study Guide

Produce an evidence-backed, reusable HTML guide for explaining, applying, and revisiting material; keep one reading layout with teaching components within each section.

## Workflow With Checkpoints

### 1. Establish The Reader And Purpose

Distinguish learning a system from preparing for a dated goal; confirm starting knowledge and target independence.
Write a short reader profile: what the reader uses daily, which words they know, and what they have never opened.
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
Record each key claim, its source, and its label in `report.md` next to the guide.
Checkpoint: each key claim has a source or an explicit unknown label in `report.md`.

### 4. Write The Learning Units

Read [references/voice.md](references/voice.md) before drafting; the text is written for the reader in the profile, not for an auditor.
Use why care → explanation with adjacent figures → complete example → self-test.
Read [references/components.md](references/components.md) when choosing markup.
Distribute self-tests across chapters; the reader answers before the explanation unfolds, and each answer links back to its section.
Follow examples with similar tasks and add a reusable review question set.
Use prediction and experiments for mechanisms, code walkthroughs for code, and open retelling for synthesis.
For sprints, include priorities, estimated time, and a self-reported review list.
Keep evidence labels in `report.md`; in the text, state a limit plainly only where the reader would otherwise be misled.
After drafting, trim with rumo-prose when it is installed.
Checkpoint: answers explain why, terms are explained at first use, and the source's limits that matter to the reader remain.

### 5. Design, Then Build One Offline HTML File

Start from [assets/template.html](assets/template.html): a skeleton with the script hooks and functional rules, and no visual design.
Before writing markup, add a short design plan to `report.md`: the visual direction and why it fits this subject and reader, four to six color tokens and the type, how wide screens are used with text and figures side by side and how narrow screens stack, and the figure each chapter needs.
Follow the new-design process in rumo-frontend when it is installed; do not reuse an earlier guide's look by default.
Keep the script hooks listed in [references/components.md](references/components.md).
Whatever the look, the page must work offline with everything inlined, follow system and manual themes, offer presentation size, print light, fit a 390-pixel screen, show the lesson and answers without JavaScript, and survive blocked localStorage.
Give each guide its own storage key; self-reports never certify mastery.
Checkpoint: the entire core lesson is available offline without scripting.

### 6. Verify The Artifact

Resolve bundled `scripts/...` paths from this installed skill directory; run build_examples → link_refs → verify_refs → check_render:
1. When embedding examples, `python scripts/build_examples.py <template.html> --out <guide.html> [--root <dir>]`,
   where `--root` is the directory the example paths are relative to. Inspect code first; allow only authorized, bounded local runs. Failure or timeout blocks verified output.
2. For code guides, `python scripts/link_refs.py <guide.html> --root <dir> [--alias X=prefix/]...`.
   Use editor links for readers with local code, switching between VS Code and Cursor; otherwise use fixed-commit web links. Ask when the setup is unknown.
   Read [references/components.md](references/components.md) for link templates and options.
3. `python scripts/verify_refs.py <guide.html> --root <dir> [--alias X=prefix/]... [--allow-empty]`
   on the built file, where `--root` is the source repository; require references unless the material truly contains none.
4. `node scripts/check_render.mjs <guide.html> --out <dir>` on the final file.
Look at the saved screenshots against the design plan: no large empty areas on a wide screen, every figure beside the text it explains, figures legible in both themes.
It checks widths/themes, errors, anchors, ids, external requests, initialization, expanded narrow layout, no-JS content, blocked storage, dark print colors, and source-switch persistence when links exist.
If Playwright is absent, report exit 2; obtain approval before any installation.
Cold read: give a fresh agent that has not seen the sources only the page text and the reader profile.
It reads as that reader and lists every sentence it cannot follow, every term not yet explained, and every place that needs a picture; revise until the list is empty.
When no fresh agent is available, say the cold read was not done and ask the user to read first.
Manually check answer correctness, agreement between figures and text, and review links.
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

Deliver the single HTML file and `report.md` with the evidence record, the cold-read result, and the four verification layers.
Include the source revision or document date, checks actually run, and anything still requiring feedback or source checking.
