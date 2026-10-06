# Repository Guidance

This repository distributes reusable agent skills for Codex, Claude Code, and other clients that load `SKILL.md` directories. It contains no product source code.

- Keep every skill independent of a specific company, product, repository name, internal host, deployment path, or agent client. When a step depends on one client, label it as client-specific and give a client-neutral alternative or an explicit stop condition.
- Put private project facts in a local profile or optional private profiles checkout and access them through `rumo-project-profile`.
- Resolve bundled scripts relative to the installed skill directory.
- Preserve unrelated working-tree changes and installed skills from other sources.
- Validate frontmatter, metadata, relative links, helper scripts, installers, and the catalog before push.
- Never commit or print passwords, tokens, private keys, or private certificate material.
- State explicit stop conditions for ambiguous or state-changing workflows.

Commits and pushes follow `skills/rumo-git-commit/SKILL.md` and repository-local instructions.

## Skill Language Policy

- In `skills/*/SKILL.md`, write frontmatter `description` and the Markdown body in English. Clients select skills from frontmatter `name` and `description` only, so keep both self-sufficient.
- `skills/*/agents/openai.yaml` is optional Codex UI metadata; other clients ignore it. Keep `interface.display_name` in English only. Keep `interface.short_description` in Chinese so the skill list can show an English name with a Chinese explanation. Prefer English for `interface.default_prompt`.
- Preserve Chinese only when it is required as literal product data, such as UI text, branch/product labels, user trigger phrases, commit-message requirements, or examples that must intentionally produce Simplified Chinese output.
- Reference files under `skills/*/references/` may keep Chinese source material, scanned product text, and UI/business examples when translating them would reduce their value as product evidence.
