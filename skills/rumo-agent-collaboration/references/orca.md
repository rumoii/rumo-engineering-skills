# Orca

Read when this session runs inside Orca and the work edits files or runs commands, when the user chose Orca, or when it is the only route that can keep a transferred task running. Orca ships guides that match its CLI version; read them for exact commands instead of relying on commands remembered from another version. No Orca skill has to be installed for this: the CLI prints the guides, and the receiver only reads its brief.

```text
orca skills get orca-cli
orca skills get orchestration
```

## Launch

- Give each writer its own worktree and start the agent in the same command: Orca's worktree creation takes the base branch, the agent with its model and effort, and the opening prompt. Record the base commit. For a worktree that already exists, launch the agent into it instead.
- Keep the prompt to one line that points at the brief, such as "Read the brief at <path> and follow it exactly. Do not commit or push." The brief lives outside the repository.
- A new worktree lacks ignored dependencies such as `node_modules`. The brief says where they come from, such as a link to the main checkout or the repository's setup step, and forbids installing them; the user picks which per project.
- The Orca route needs no adapter, so it can start a CLI that `agent_run.py` cannot, such as Kimi.

## Map The Modes

Start the other agent in its own terminal or worktree through `orca-cli`, create no supervised run, and end your turn as Workflow step 4 in SKILL.md allows. For a delegation you remain the owner: read and validate the result when the wait below ends or the user reports completion. For a transfer, do not monitor it afterward.

Use the supervised loop in the orchestration guide (dispatch, wait for completion or questions, validate each result) only for a relay or when the user asks for supervised coordination.

When a prompt you receive carries Orca's injected task and dispatch IDs, you are a dispatched worker: follow that preamble, not this skill's workflow.

## Wait For The Result

When this client runs background commands and reports their exit, as Claude Code does, start one background wait per agent and rely on its exit, not on the user. Otherwise, wait for the user as Workflow step 4 says.

- For an agent that Orca's `terminal wait --for tui-idle` supports, as the orca-cli guide lists, run that with a timeout, and run it again when it times out.
- For any other agent, run `scripts/orca_wait.py --terminal <handle> --report <report path> --marker <done line>`, resolved from this skill's directory. It only reads the terminal and exits with one line: done (the report changed after the wait began and the marker is on screen), idle (the screen unchanged for `--idle` seconds, 200 by default), stopped, or lost.
- When a wait ends, read the terminal and the report to tell a finished agent from one asking a question or waiting for approval. After handling it, start a new wait if the agent continues.

## Rules That Still Apply

- The approval, access, and single-owner rules in SKILL.md apply unchanged; Orca's options do not widen them.
- A successful send proves the message was queued, not that the agent acted on it. Confirm progress from the worker's own report or the orchestration status the guide names.
- When a start command fails, read its output before trying again; do not start a second worker for the same task.
- Record the Orca task or terminal ID in your report and, for a transfer, tell the user how to open that terminal.
