# Skills

Every skill uses the `rumo-` namespace and stays independent of any company, product, host, or deployment. Project-specific facts come from `rumo-project-profile` and a local or private profile.

`skills/` holds the default set that the installers always link. Optional skills live in the repository's `extras/` directory and are installed on request with `-Extras` or `--extras`.

## Default

| Skill | Purpose |
| --- | --- |
| `rumo-clarify` | Group answerable questions with recommendations and follow up only on newly exposed key decisions |
| `rumo-plan` | Short spec and verifiable task breakdown, task-by-task execution, or a durable engineering decision record |
| `rumo-coding-guidelines` | Baseline discipline for grounded, minimal, verified code changes |
| `rumo-test` | Evidence planning, test-first implementation, and high-assurance spec and evidence |
| `rumo-debug` | Reproduce, localize, and prove a root cause; read-only by default |
| `rumo-verify` | Exact change scope and smallest sufficient checks; repository gates |
| `rumo-review` | Read-only diff review or named-scope audit, explicit review-fix loop, simplification audit, responding to feedback, or a consented review through another CLI |
| `rumo-git-commit` | Commit, branch landing, history cleanup, release, push, pull request workflow, and following pull request checks |
| `rumo-interface` | Compatible interface and stored-format evolution, with HTTP contract checks |
| `rumo-lifecycle-safety` | Ownership, retry, cancellation, timeout, shutdown, and cleanup |
| `rumo-database-change-safety` | Authorized, backed-up, bounded, reversible database writes |
| `rumo-filesystem-safety` | Deletion and bulk cleanup scaled to the blast radius |
| `rumo-remote-ops` | Remote Linux queries and changes, service deployment, backup and restore, artifact deployment |
| `rumo-prose` | Prose quality for code, diagnostics, docs, UI strings, and agent-facing files |
| `rumo-frontend` | Frontend page work, new interface design, accessibility checks, dev-server troubleshooting, and requested browser evidence |
| `rumo-handoff` | Self-contained handoff documents (manual only) |
| `rumo-project-profile` | Private project profile resolution and validation |
| `rumo-agent-collaboration` | Delegate, transfer, or relay work to Codex, Claude Code, pi, qwen, grok, Cursor, Copilot CLI, Aider, Cline CLI, Goose, or Orca; supports read-only and development access on Windows and Linux/WSL, with one owner and records. Named, bounded requests supply authorization. Gemini CLI and OpenCode declarations remain inspectable; the runner blocks their new turns and old-record recovery |

## Extras

| Skill | Purpose |
| --- | --- |
| `rumo-diagram` | Mermaid flowcharts and confirmed topology diagrams with preview and export |
| `rumo-document-writing` | Formal Word delivery documents |
| `rumo-offline-delivery-audit` | Offline package integrity, provenance, installation, rollback, and acceptance limits |
| `rumo-daily-report` | Incremental Chinese daily reports (manual only) |
| `rumo-linux-inspect` | Read-only Linux hardware inventory or memory inspection (manual only) |
| `rumo-imagegen` | One image through a configured OpenAI-compatible endpoint (manual only) |
| `rumo-reflect` | Session retrospective that proposes where to fix recurring mistakes and applies only approved items |
