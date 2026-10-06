---
name: rumo-mermaid-diagram
description: >
  Use when creating, revising, previewing, or exporting Mermaid flowcharts and business process diagrams
  (流程图、业务链路图、校验/审核分支图) as Markdown + HTML preview + PNG/SVG assets.
  Covers light-theme defaults, pass/fail/engine branch styling, layout hygiene, and headless PNG export.
  Triggers: 流程图, mermaid 图, 导出 png, 业务流程图, flow diagram, process diagram,
  /rumo-mermaid-diagram, "画流程图", "导出流程图".
---

# Rumo Mermaid Diagram

Produce business process flowcharts that stay versionable in Git and export to delivery images.

| Deliverable | Role |
|-------------|------|
| `*.md` | Mermaid source of truth plus short explanation tables |
| `*-preview.html` or `*-flow.html` | Interactive preview with PNG/SVG export |
| `*.png` | Documentation or delivery image (default light theme, 4:3) |

Use this skill for staged flows with decisions, outcome branches, external tools, and pass/fail criteria. Do not use it for arbitrary image generation such as screenshots or photos. Use `rumo-engineering-topology-diagram` for architecture, deployment, or network topology.

## 1. Gather Content

Confirm from repository documents or the user:

1. Stages, for example intake → processing → verification → outcome.
2. Roles and systems, including external tools or validators that act in the flow.
3. Decision points and branches: the success path and the reject or rework path.
4. Pass/fail rules, when relevant, such as item-level versus whole-request criteria.
5. Label language and theme. Write node labels in the language the user or document uses. Default to the light theme (`#f7f9fc` canvas); use dark only when asked.

Do not invent business rules. Ground pass/fail text in repository documents or user statements.

## 2. Write Mermaid In Markdown

Create or update `docs/<name>.md` or the project's equivalent path: a title, a short purpose, the `mermaid` fenced block, and tables for rules that do not fit on nodes.

Layout rules:

- Prefer three stage columns: `flowchart LR` with inner `direction TB` subgraphs.
- Put dual outcomes as sibling subgraphs under the result stage (success green, failure red).
- Avoid back-edges that reverse rank order, such as failure → intake. End with a terminal node like "return to intake and resubmit" instead.
- Use an invisible link (`passBranch ~~~ failBranch`) to pin success left and failure right when needed.
- Keep node text short; use `<br/>` for at most 2–4 lines.
- Use decision diamonds for yes/no and boxes for actions.
- Use product-facing names on nodes rather than internal aliases.
- Apply the semantic classes:

```text
passStyle    fill:#e8f8ef stroke:#2f9e62 color:#14532d   # pass / success
failStyle    fill:#fdecec stroke:#d45454 color:#7f1d1d   # fail / reject
engineStyle  fill:#e8f1ff stroke:#3b82f6 color:#1e3a8a   # external engine or tool
compareStyle fill:#fff7e6 stroke:#d97706 color:#7c2d12   # verification / comparison rule
```

## 3. Preview HTML

Copy `templates/flow-preview.html` into the target repository and rename it as needed. Then:

1. Set the page title, toolbar title, and hint text.
2. Paste the same Mermaid into `#fallback-source`.
3. Point `loadSource()` at the sibling `.md` so HTTP preview follows the Markdown.
4. Keep `dark = false` for the light default.

The template already provides fit, theme toggle, scale, PNG/SVG export, theme-aware rewriting of the four semantic classes, and a 1600×1200 (4:3) export frame at 2–4× scale.

## 4. Export PNG

Resolve `SKILL_DIR` from the directory containing this loaded `SKILL.md`, not from a source checkout or the target project. If it cannot be resolved, stop and report the path blocker instead of guessing.

Install the declared runtime dependency once in the installed skill directory, then run the exporter from the target project so relative paths belong to that project:

```bash
npm install --omit=dev --prefix "$SKILL_DIR"
node "$SKILL_DIR/scripts/export-mermaid-png.mjs" --html docs/<name>.html --out docs/<name>.png --scale 3
node "$SKILL_DIR/scripts/export-mermaid-png.mjs" --md docs/<name>.md --out docs/<name>.png --title "<diagram title>" --scale 3
```

In PowerShell, use `$SkillDir` and the same arguments with Windows paths; quote paths that contain spaces.

Requirements:

- Node.js 18 or later and the declared `playwright-core` dependency.
- Network access to jsDelivr for Mermaid and svg-pan-zoom used by the preview HTML, or vendored copies when the project forbids CDNs.
- Headless Chrome, Chromium, or Edge discovered by the script, a Playwright-managed browser, or an explicit `CHROME_PATH`.

After export, open the PNG and check stage order, readable branch labels, the four semantic colors where used, removal of names the user asked to drop, and text overflow.

## 5. Iterate With The User

| User ask | Action |
|----------|--------|
| 明亮色系 / light theme | Keep the light default; re-export PNG |
| 补充如何检验 / add judgment rules | Expand comparison and decision subgraphs plus the Markdown tables |
| 去掉某标签 / remove a label | Edit Mermaid and `#fallback-source`; re-export |
| 双分支成功/失败 / dual outcomes | Green and red subgraphs with the semantic classes |
| 布局乱 / messy layout | Remove reverse edges, simplify subgraphs, pin order with `~~~` |

Re-export the PNG whenever Mermaid changes and the PNG is a delivered artifact.

## Deliverable Checklist

- [ ] Markdown Mermaid renders without syntax errors in preview.
- [ ] HTML fallback matches the Markdown Mermaid.
- [ ] Light-theme PNG regenerated at the requested path.
- [ ] Pass/fail or dual-branch semantics are visible when the flow has outcomes.
- [ ] Markdown tables explain rules that do not fit on nodes.
- [ ] No secrets, local absolute paths, or agent process notes in delivered documents.

## References

- Style and layout details: [references/style-and-layout.md](references/style-and-layout.md)
- Preview template: [templates/flow-preview.html](templates/flow-preview.html)
- Export CLI: [scripts/export-mermaid-png.mjs](scripts/export-mermaid-png.mjs)

## Response Discipline

- State which files were created or updated, the theme, and the export scale.
- If PNG export failed (no browser or no network), leave the Markdown and HTML working and report the blocker with the exact command tried.
