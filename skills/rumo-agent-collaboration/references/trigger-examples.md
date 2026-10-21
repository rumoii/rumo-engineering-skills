# Selection Examples

Read when checking whether collaboration and neighboring skills have distinct responsibilities. These are expected selections for a client with the default skills installed, not results from model evaluations.

| Request | Expected responsibility |
|---|---|
| Review the current diff without editing files. | `rumo-review`; no external CLI launch is authorized. |
| Ask Claude Code to review this diff, read-only. | `rumo-review` sets the review standard; `rumo-agent-collaboration` executes the named external route and records it. The scoped request supplies authorization. |
| Give Aider the parser implementation in this module. | `rumo-agent-collaboration` delegates the named development scope; coding and verification skills still apply. |
| Write a handoff document for the next engineer. | `rumo-handoff`; producing a document does not authorize launching a receiver. |
| Split the agreed migration plan into parallel tasks. | `rumo-plan`; decomposition alone does not authorize external execution. |
| Start three native subagents in this client. | The client handles its native subagents; this skill is not needed. |
| Continue the external CLI run recorded under this run ID. | `rumo-agent-collaboration` reconciles the record before resuming; disabled routes remain blocked. |

If this skill is unavailable, the review skill's own external-CLI reference remains the fallback. Do not count a static wording check as proof that a model selects these skills. Real trigger evaluation spends quota and requires separate authorization.
