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
| Engine | fill `#e8f1ff`, stroke `#3b82f6`, text `#1e3a8a` | External engines / tools |
| Compare | fill `#fff7e6`, stroke `#d97706`, text `#7c2d12` | Verification / comparison |

Dark theme is optional for preview only; delivery PNG should stay light unless the user asks otherwise.

## Structure patterns

### A. Three-stage business flow

```text
1. Intake  →  2. Processing / verification  →  3. Dual outcome branches
```

- Outer: `flowchart LR`
- Each stage: `subgraph` with `direction TB`
- Result stage: nested success / fail subgraphs with `direction TB` (or `LR` + `~~~` to pin order)

### B. Dual engines after a type decision

```text
Request type decision ──type X──► Engine A
                      ──type Y──► Engine B
Both ──► normalize outputs ──► validator
```

### C. How to verify + how to judge

Separate subgraphs:

1. **How to verify**: what is compared (for example, produced output versus a reference baseline)
2. **How to judge**: item pass criteria and whole-request pass criteria (green/red boxes)

Do not collapse both into a single vague node like "compare output with baseline" when the user needs judgment detail.

## Layout hygiene

1. **No reverse rank edges** from late stages back to early stages if they scramble column order. Use a terminal node such as "return to step X" instead.
2. Prefer **edge labels** on decisions, such as `meets requirements` / `does not meet` or `pass` / `fail`, in the diagram's label language.
3. Keep subgraph titles short and numbered by stage.
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
- One tool name per engine node when the user asked to drop aliases.
- Write business-step labels in the diagram's label language; keep product and tool proper names as written.

## Markdown companion tables

Use tables under the diagram for:

- Engine role matrix
- Pass / fail criteria
- Comparison object matrix (what is compared at each level)

Keep tables in sync when node text changes.
