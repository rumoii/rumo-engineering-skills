# Orca

Read when Orca is installed and the work edits files or runs commands, when the user chose Orca, or when it is the only route that can keep a transferred task running. Orca ships guides that match its CLI version; read them instead of relying on commands remembered from another version:

```text
orca skills get orca-cli
orca skills get orchestration
```

## Map The Modes

| This skill | Orca role | What that means |
|---|---|---|
| Transfer | Handoff owner | Start the other agent in its own terminal or worktree through `orca-cli`; create no supervised run and do not monitor it afterward. |
| Delegate, Relay | Coordinator | Use the supervised loop in the orchestration guide: dispatch, wait for completion or questions, and validate each result before accepting it. |

For a delegation the user will watch, you may instead start the worker in its own terminal without a supervised run and end your turn as Workflow step 4 in SKILL.md allows. You remain the owner; read and validate the result when the user reports completion.

When a prompt you receive carries Orca's injected task and dispatch IDs, you are a dispatched worker: follow that preamble, not this skill's workflow.

## Rules That Still Apply

- The approval, access, and single-owner rules in SKILL.md apply unchanged; Orca's options do not widen them.
- A successful send proves the message was queued, not that the agent acted on it. Confirm progress from the worker's own report or the orchestration status the guide names.
- When a start command fails, read its output before trying again; do not start a second worker for the same task.
- Record the Orca task or terminal ID in your report and, for a transfer, tell the user how to open that terminal.
