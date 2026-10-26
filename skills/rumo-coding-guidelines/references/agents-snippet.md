# Always-On Baseline

Clients load a skill only when its description matches the request, so small edits can skip `rumo-coding-guidelines` and one skill may not bring in the next. Keep the block below in a project's or user's `AGENTS.md` or `CLAUDE.md` so every session has the core rules and the routing: run the installer with `-Baseline` / `--baseline`, run `scripts/baseline_block.py --target <file> --install` from this skill, or paste it by hand. It routes to the skills; it does not replace them.

```markdown
## Engineering baseline (rumo skills)

IMPORTANT: Before non-trivial engineering work, such as a feature, bug fix, refactor, debugging, or any multi-step code change, find its row below and load that skill first. Pure questions and one-line edits need no skill. A subagent dispatched for a specific task follows its brief instead of this routing.

| When | Load |
| --- | --- |
| Any code change beyond a one-line edit | rumo-coding-guidelines |
| Unclear goal, scope, or risky decision | rumo-clarify |
| Agreed multi-step work | rumo-plan |
| Defect or unexplained behavior | rumo-debug, then a failing test before the fix |
| Before saying done, committing, or pushing | rumo-verify |
| A review, or another model's opinion | rumo-review |
| Commit, push, or pull request, only when asked | rumo-git-commit |
| Database writes; deleting files; remote hosts | rumo-database-change-safety; rumo-filesystem-safety; rumo-remote-ops |
| Interfaces other programs read; background work | rumo-interface; rumo-lifecycle-safety |
| Handing work to another agent or model | rumo-agent-collaboration |
| Resuming or handing off work | rumo-handoff |

- Read the real entry point and call chain before editing; repository instructions override these defaults.
- Do only what was asked and what it necessarily implies: every changed line traces to the request, and you report unrelated problems instead of fixing them. No speculative abstractions, drive-by refactors, or reformatting of neighboring code.
- Risk gate before editing: money, auth, secrets, migrations, and irreversible effects are high at once; durable data, concurrency, interfaces other programs read, untrusted input, personal data, deployment, and dependencies are rated first. When high, write a test that fails before the change, prove the one fact the change is safe because of, and rerun the checks after the last edit.
- Never claim done without fresh evidence; use rumo-verify before handing back.
- After repeated user corrections, offer once to review the session for lessons; start only if the user accepts.
- Full rules: the rumo-coding-guidelines skill.
```
