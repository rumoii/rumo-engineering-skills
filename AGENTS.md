@CLAUDE.md

## Skill Language Policy

- In `skills/*/agents/openai.yaml`, keep `interface.display_name` in English only. Keep `interface.short_description` in Chinese so the skill list can show an English name with a Chinese explanation. Prefer English for `interface.default_prompt`.
- In `skills/*/SKILL.md`, write frontmatter `description` and the Markdown body in English.
- Preserve Chinese only when it is required as literal product data, such as UI text, branch/product labels, user trigger phrases, commit-message requirements, or examples that must intentionally produce Simplified Chinese output.
- Reference files under `skills/*/references/` may keep Chinese source material, scanned product text, and UI/business examples when translating them would reduce their value as product evidence.
