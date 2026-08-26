# Repository Guidance

This repository distributes reusable agent skills. It contains no product source code.

- Keep every skill independent of a specific company, product, repository name, internal host, or deployment path.
- Put private project facts in a local profile or optional private profiles checkout and access them through `rumo-project-profile`.
- Resolve bundled scripts relative to the installed skill directory.
- Preserve unrelated working-tree changes and installed skills from other sources.
- Validate frontmatter, metadata, relative links, helper scripts, installers, and the catalog before push.
- Never commit or print passwords, tokens, private keys, or private certificate material.
- State explicit stop conditions for ambiguous or state-changing workflows.

Commits and pushes follow `skills/rumo-git-commit/SKILL.md` and repository-local instructions.
