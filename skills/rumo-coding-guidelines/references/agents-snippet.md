# Always-On Baseline

Clients load a skill only when its description matches the request, so small edits can skip `rumo-coding-guidelines`. Keep the block below in a project's or user's `AGENTS.md` or `CLAUDE.md` to keep the core rules in every session: run the installer with `-Baseline` / `--baseline`, run `scripts/baseline_block.py --target <file> --install` from this skill, or paste it by hand. It indexes the skills; it does not replace them.

```markdown
## Engineering baseline (rumo skills)

- Read the real entry point and call chain before editing; repository instructions override these defaults.
- Do only what was asked and what it necessarily implies; report unrelated problems instead of fixing them.
- No speculative abstractions, drive-by refactors, or reformatting of neighboring code.
- Before changing money, auth, migrations, durable data, concurrency, public interfaces, or irreversible effects, apply the risk gate in rumo-test.
- Never claim done without fresh evidence; use rumo-verify before handing back.
- Flow: rumo-clarify for unclear asks, rumo-plan for multi-step work, rumo-test, rumo-verify, rumo-review, and rumo-git-commit only on request. Guardrails: rumo-database-change-safety, rumo-filesystem-safety, rumo-remote-ops, rumo-interface, rumo-lifecycle-safety.
- Full rules: the rumo-coding-guidelines skill.
```
