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
- Start every agent through `--agent <id>` on `worktree create` or `agent launch`, with Orca's own agent ID, such as `qwen-code` for qwen. Only that path adds the default arguments the user set in Orca, which decide the agent's permissions; the worktree is not a sandbox, so say in the launch line that the agent runs with those permissions. When Orca refuses the ID, stop and report: a CLI started by hand in `terminal create --command` falls back to its own approval mode and stops at prompts.
- For pi, whose prompts come from its permission extension rather than Orca's arguments, create the worktree without `--agent`, write `{"yoloMode": true}` to `.pi/extensions/pi-permission-system/config.json` inside it, then start pi with `agent launch --agent pi --worktree <the new worktree's ID>`. Pi reads that file only when Orca starts it with `--approve`, set as pi's default argument in Orca. Delete the file when the task ends, whether it was accepted, failed to launch, stopped, or passed to another lane, keep it out of the changes, and check for a leftover one before reusing a worktree.
- When the launch result says the prompt was `not-delivered`, read the terminal. Kimi asks "Trust this folder?" in every new folder; for a worktree this task created, choose Trust, then send the same one-line prompt with `terminal send --enter` and read the terminal again to confirm it started. Report any other startup prompt to the user.

## Map The Modes

Start the other agent in its own terminal or worktree through `orca-cli`, create no supervised run, and end your turn as Workflow step 4 in SKILL.md allows. For a delegation you remain the owner: read and validate the result when the wait below ends or the user reports completion. For a transfer, do not monitor it afterward.

Use the supervised loop in the orchestration guide (dispatch, wait for completion or questions, validate each result) only for a relay or when the user asks for supervised coordination.

When a prompt you receive carries Orca's injected task and dispatch IDs, you are a dispatched worker: follow that preamble, not this skill's workflow.

## Wait For The Result

When this client runs background commands and reports their exit, as Claude Code does, start one background wait per agent and rely on its exit, not on the user. Otherwise, wait for the user as Workflow step 4 says.

Run `scripts/orca_wait.py --terminal <handle> --report <report path> --marker <end line>`, resolved from this skill's directory, for every agent, with one `--marker` for each end line the brief names, such as one for finishing and one for stopping. It only reads Orca and exits with one line:

- done: the report changed after the wait began and one of the markers is on screen; the line names which.
- attention: Orca has shown the agent at an approval or question prompt for `--attention` seconds, 60 by default.
- idle: Orca has shown the agent's turn ended for `--attention` seconds without done, for example a stop report whose line differs from the marker, or the screen has not changed for `--idle` seconds, 200 by default. The screen check covers agents whose state Orca does not report.
- stopped: the terminal exited or its handle went stale.
- lost: every read failed for `--lost` seconds.

On attention, read the terminal to see what the agent waits for, then tell the user which agent, which worktree, and what it asks; also send a push notification when the client has one. Do not answer the prompt yourself. Start the next wait with the `--seen` value from the attention line, so the same prompt is not reported again; if it stays unanswered, that wait ends in idle.

On idle, read the terminal and the report to tell a finished agent from one asking a question or waiting for approval. After handling any exit, start a new wait if the agent continues.

## Rules That Still Apply

- The approval, access, and single-owner rules in SKILL.md apply unchanged apart from its Orca exception; Orca's options widen them no further.
- A successful send proves the message was queued, not that the agent acted on it. Confirm progress from the worker's own report or the orchestration status the guide names.
- When a start command fails, read its output before trying again; do not start a second worker for the same task.
- Record the Orca task or terminal ID in your report and, for a transfer, tell the user how to open that terminal.
