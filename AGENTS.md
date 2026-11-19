# Repository Guidance

This repository distributes reusable agent skills for Codex, Claude Code, and other clients that load `SKILL.md` directories. It contains no product source code; its scripts are helpers bundled with the skills, plus the installers and repository checks.

- Keep every skill independent of a specific company, product, repository name, internal host, deployment path, or agent client. When a step depends on one client, label it as client-specific and give a client-neutral alternative or an explicit stop condition.
- Put private project facts in a local profile or optional private profiles checkout and access them through `rumo-project-profile`.
- Resolve bundled scripts relative to the installed skill directory.
- Preserve unrelated working-tree changes and installed skills from other sources.
- Validate frontmatter, metadata, relative links, helper scripts, installers, and the catalog before push. Before pushing a change that adds, removes, merges, or renames a skill, or alters a description, run the acceptance in `CONTRIBUTING.md`.
- Never commit or print passwords, tokens, private keys, or private certificate material.
- State explicit stop conditions for ambiguous or state-changing workflows.
- Write every skill in your own words. Do not copy text from other projects, and do not add attribution notes or separate license files inside skill directories.

Commits and pushes follow `skills/rumo-git-commit/SKILL.md` and repository-local instructions.

## Layout

- `skills/` holds the default skills that the installers always link; `extras/` holds optional skills installed with `-Extras` or `--extras`. A default skill must not link to an extra.
- Follow the skill structure in `CONTRIBUTING.md` and `skills/rumo-prose/references/agent-docs.md`.

## Skill Language Policy

- In `skills/*/SKILL.md` and `extras/*/SKILL.md`, write frontmatter `description` and the Markdown body in English. Clients select skills from frontmatter `name` and `description` only, so keep both self-sufficient.
- `agents/openai.yaml` in each skill is optional Codex UI metadata; other clients ignore it. Keep `interface.display_name` in English only. Keep `interface.short_description` in Chinese so the skill list can show an English name with a Chinese explanation. Prefer English for `interface.default_prompt`.
- Preserve Chinese only when it is required as literal product data, such as UI text, branch/product labels, user trigger phrases, commit-message requirements, or examples that must intentionally produce Simplified Chinese output.
- Reference files under each skill's `references/` may keep Chinese source material, scanned product text, and UI/business examples when translating them would reduce their value as product evidence.

## Rules And Their Checks

Which rule above a machine check enforces. When a rule marked "none" or "partial" is broken, propose a check for it (`rumo-reflect`); propose deleting a rule once its mistake can no longer happen.

| Rule | Enforced by |
| --- | --- |
| No company, product, or host names | `verify_skills.py` private forbidden-terms list (partial; neutral wording is otherwise none) |
| Private project facts stay in profiles | none |
| Bundled scripts resolve from the skill directory | `verify_skills.py` script references must exist in the same skill (partial) |
| Installed skills from other sources are preserved | `scripts/tests/test_install_ps1.py`, `test_install_sh.py` (unrelated directories and foreign links) |
| Frontmatter, metadata, links, catalog well formed | `verify_skills.py` |
| Installers work | `scripts/tests/test_install_ps1.py`, `test_install_sh.py` |
| Description changes get a real-client trigger run | none (`CONTRIBUTING.md` acceptance) |
| No credentials or private keys committed | `verify_skills.py` credential-file and key/token patterns |
| Explicit stop conditions | `scripts/tests/test_skill_rules.py` pins selected ones (partial) |
| No attribution notes; no license files in skills | license files: `verify_skills.py`; attribution: none |
| A default skill never links to an extra | `verify_skills.py` link check |
| `display_name` English, `short_description` Chinese | `verify_skills.py` metadata check |
| `SKILL.md` description and body in English | none |
| Rules whose loss lets an agent overstep or overclaim | `scripts/tests/test_skill_rules.py` pinned sentences |
