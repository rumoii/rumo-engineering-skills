# Mermaid Flow Style And Layout

## Default visual system (light)

| Token | Value | Use |
|-------|-------|-----|
| Canvas | `#f7f9fc` | PNG background, page bg |
| Toolbar | `#eef2f7` | Preview chrome |
| Border | `#d0d7e2` | UI borders |
| Text | `#1f2328` | Default labels |
| Pass | fill `#e8f8ef`, stroke `#2f9e62`, text `#14532d` | Success path |
| Fail | fill `#fdecec`, stroke `#d45454`, text `#7f1d1d` | Reject / fail path |
| Engine | fill `#e8f1ff`, stroke `#3b82f6`, text `#1e3a8a` | External simulators / tools |
| Compare | fill `#fff7e6`, stroke `#d97706`, text `#7c2d12` | Verification / comparison |

Dark theme is optional for preview only; delivery PNG should stay light unless the user asks otherwise.

## Structure patterns

### A. Three-stage business flow

```text
一、入口/上传  →  二、处理/仿真/检验  →  三、结果双分支
```

- Outer: `flowchart LR`
- Each stage: `subgraph` with `direction TB`
- Result stage: nested success / fail subgraphs with `direction TB` (or `LR` + `~~~` to pin order)

### B. Dual engines after a type decision

```text
暂态/类型决策 ──电磁──► Engine A
              ──机电──► Engine B
Both ──► normalize outputs ──► validator
```

### C. How to verify + how to judge

Separate subgraphs:

1. **如何检验**: what is compared (e.g. sim vs HIL; equivalent vs detailed)
2. **如何判定**: item pass criteria, whole-order pass criteria (green/red boxes)

Do not collapse both into a single vague node like “对比仿真与基准数据” when the user needs judgment detail.

## Layout hygiene

1. **No reverse rank edges** from late stages back to early stages if they scramble column order. Use text “回到第 X 步” instead.
2. Prefer **edge labels** on decisions: `符合要求` / `不符合要求` / `通过` / `未通过`.
3. Keep subgraph titles short: `一、…` `二、…` `三、…`.
4. If Mermaid places fail left of success, add `passBranch ~~~ failBranch` after both subgraphs.
5. Export frame is 4:3 (1600×1200 logical). Very tall TB-only graphs shrink hard; prefer LR stages for dense content.

## Mermaid snippet: semantic classes

```mermaid
classDef passStyle fill:#e8f8ef,stroke:#2f9e62,color:#14532d
classDef failStyle fill:#fdecec,stroke:#d45454,color:#7f1d1d
classDef engineStyle fill:#e8f1ff,stroke:#3b82f6,color:#1e3a8a
classDef compareStyle fill:#fff7e6,stroke:#d97706,color:#7c2d12
class successNodes passStyle
class failNodes failStyle
class engineNodes engineStyle
class compareNodes compareStyle
```

Preview HTML rewrites these classDefs when toggling dark mode so one source works for both themes.

## Naming

- Product terms over internal package names on the diagram.
- One tool name per engine node when the user asked to drop aliases (e.g. `PSModel` only).
- Chinese body labels for business steps; English only for product/tool proper names.

## Markdown companion tables

Use tables under the diagram for:

- Engine role matrix
- Pass / fail criteria
- Comparison object matrix (single-machine vs station)

Keep tables in sync when node text changes.
