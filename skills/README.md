# Skills

Every skill uses the `rumo-` namespace and stays independent of any company, product, host, or deployment. Project-specific facts come from `rumo-project-profile` and a local or private profile.

`skills/` holds the default set that the installers always link. Optional skills live in the repository's `extras/` directory and are installed on request with `-Extras` or `--extras`.

## Default

| Skill | Purpose |
| --- | --- |
| `rumo-clarify` | Lightweight requirement clarification with one round of recommended-answer questions |
| `rumo-plan` | Short spec and verifiable task breakdown, or a durable engineering decision record |
| `rumo-coding-guidelines` | Baseline discipline for grounded, minimal, verified code changes |
| `rumo-test` | Evidence planning, test-first implementation, and high-assurance spec and evidence |
| `rumo-debug` | Reproduce, localize, and prove a root cause; read-only by default |
| `rumo-verify` | Exact change scope and smallest sufficient checks; repository gates |
| `rumo-review` | Read-only review, explicit review-fix loop, or simplification audit |
| `rumo-git-commit` | Commit, branch landing, history cleanup, release, and push workflow |
| `rumo-interface` | Compatible interface and stored-format evolution, with HTTP contract checks |
| `rumo-lifecycle-safety` | Ownership, retry, cancellation, timeout, shutdown, and cleanup |
| `rumo-database-change-safety` | Authorized, backed-up, bounded, reversible database writes |
| `rumo-filesystem-safety` | Deletion and bulk cleanup scaled to the blast radius |
| `rumo-remote-ops` | Remote Linux queries and changes, service deployment, backup and restore, artifact deployment |
| `rumo-prose` | Prose quality for code, diagnostics, docs, UI strings, and agent-facing files |
| `rumo-handoff` | Self-contained handoff documents (manual only) |
| `rumo-project-profile` | Private project profile resolution and validation |

## Extras

| Skill | Purpose |
| --- | --- |
| `rumo-diagram` | Mermaid flowcharts and confirmed topology diagrams with preview and export |
| `rumo-document-writing` | Formal Word delivery documents |
| `rumo-frontend` | Frontend page work, dev-server troubleshooting, and requested browser evidence |
| `rumo-offline-delivery-audit` | Offline package integrity, provenance, installation, rollback, and acceptance limits |
| `rumo-daily-report` | Incremental Chinese daily reports (manual only) |
| `rumo-linux-inspect` | Read-only Linux hardware inventory or memory inspection (manual only) |
| `rumo-imagegen` | One image through a configured OpenAI-compatible endpoint (manual only) |
