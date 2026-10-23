---
name: rumo-agent-collaboration
description: Use when the user asks to delegate, transfer, or relay work to another agent CLI or model, such as Codex, Claude Code, pi, Aider, or Gemini ("give this part to pi", "交给 pi 执行"), to use Orca for collaboration, or to resume a recorded run. For a named external CLI review, also load rumo-review; use rumo-review alone when no external route is named. Use rumo-handoff for a handoff document and rumo-plan to split an agreed plan. Do not use for this client's own subagents, such as "start several subagents".
---

# Rumo Agent Collaboration

Hand a bounded piece of work to another agent where the user can see it, end your turn, and accept the result on evidence.

## Scope

This skill governs only the agents it starts; the client's own subagents follow the client's rules, except that a relay or transfer step run through one keeps the single-owner rules here. Before declaring native subagents available or unavailable, read [references/native.md](references/native.md).

For a named external CLI review, use rumo-review for review standards and this skill for execution and records. Read rumo-review before writing the review brief. [references/trigger-examples.md](references/trigger-examples.md) marks the boundaries with neighboring skills.

## Ownership

You stay the owner: treat any request to hand work to another agent as delegation, whatever verb it uses, such as "交给" or "交接给". Transfer ownership only when the user says this session should step away, such as "let it take over; you're done here". In a relay (develop, review, fix), each step names the next owner, and nobody acts on the task between steps. Free-form agent-to-agent messaging and schedulers that keep running after this conversation are out of scope.

## Authorization

Never start an agent through this skill unless the user asked for it. When the user named the CLI and the work, that request is the approval: state in one line before launching which CLI, model, and effort will run and what content you will send, then launch. Keep it to that line; do not ask again. A configured `delegate` lane counts as a named CLI. Ask first when the user named no route and none is configured, when you would send content the user did not mention, or when the work needs more access than the request implies.

- Pick read-only unless the work edits files; asking for edits approves writes limited to the files or module the user named. Use `workspace-write` only where the adapter documents a directory restriction. `native-write` has no directory isolation: state its default automatic approval and whether shell tools are available. A worktree is not a sandbox.
- When the work itself means running commands, such as tests or a build, the request approves shell access for that work: say in the same line that commands run automatically without a directory sandbox, where the agent may write, and what it must not do. Shell access the work does not need, such as shell for a review, needs its own approval; ask at most once per launch.
- Never give the receiver more access than you have, and never pass a flag that bypasses its sandbox, approvals, or tool limits. Commits, pushes, deployments, and dependency installs keep the approvals their own skills require.

## Workflow

1. **Brief.** Write the goal, scope, files to read, the check that proves it done, and the stop conditions to a file outside the repository. Give the task, not your reasoning; for a transfer, use the structure of `rumo-handoff`.
2. **Isolate writers.** Two agents never write the same working tree at once; give a parallel writer its own worktree from a recorded base. Uncommitted changes do not appear in a new worktree: tell the receiver how it gets them, and do not commit them just to move them unless the user approves.
3. **Launch once, where the user can see it.** Follow the route, model, and effort the user names. For anything they leave out, use the user's configuration: `scripts/agent_config.py lanes delegate` when no CLI is named, taking the lane whose `use` label fits the work and otherwise the first, and the configured lane's model and effort when the named CLI has one; pass them as `--model`, `--effort`, and `--executable` when the lane has one. Exit 3 means nothing is configured: ask, and mention that `rumo-setup` saves the choice.
   - Another installed CLI runs through `scripts/agent_run.py`, resolved from this skill's directory; the Quick Start in [references/external-cli.md](references/external-cli.md) has the commands. `start` checks the CLI itself and runs without a window; `watch` shows its progress. Read-only work runs this way. A CLI with no adapter needs one first ([references/adapters.md](references/adapters.md)); a CLI without a confirmed read-only mode cannot have an adapter. Do not call an adapter tested end to end unless its `verified.live_run` is true.
   - Work that edits files or runs commands goes to an Orca terminal when Orca is installed ([references/orca.md](references/orca.md)), otherwise to `agent_run.py open`, a CLI window the user can type into. When the CLI has no interactive template, use `start` and say why.
   - When the route is unavailable, not signed in, or refused, report the blocker. Do not switch route, model, or access level on your own.
   - When you cannot tell whether a turn was delivered, check the recorded session before sending anything again.
4. **Tell the user and end your turn.** In one short message: where the receiver runs, where the result will be, and what to tell you when it finishes; for `start`, add the `watch` command that shows its progress, and when `survives_caller` is not true, that closing this session may also stop the receiver. Leave the full report for acceptance. When this client runs background commands and reports their exit, run `start`, or `agent_run.py wait` after `open`, that way and rely on that report, not on the user; `open` returns once the window opens, not when the work is done. Otherwise add `--detach` to `start`, or after `open` wait for the user. While the receiver runs, do not read its events, logs, or session files and do not post progress updates. Until you accept the result, do not touch its write scope.

   Client-specific (Claude Code): when both sides are Claude Code, you may instead subscribe once to the receiver's idle notice through cross-session messaging, using the run ID as its session name.
5. **Accept on evidence.** When the user reports that the receiver finished, read its result and check the working tree before accepting it. After a visible window closes, get the report by resuming the session headlessly with a short request for the final report and the changed files. Rerun the check yourself and record the decision with `agent_run.py record`, or in your report for Orca and native routes. A timeout is not a failure of the task: check the session before deciding.
6. **Transfer.** Only to an agent that keeps running after you stop, never to a native subagent tied to this conversation; do not transfer ownership without a resumable session. Confirm the receiver acknowledged the brief and named its next step, record the transfer, tell the user how to reach the new owner, then stop changing that task. A result that arrives later is input for the new owner, not an action for you.

To continue in a later conversation, read [references/records.md](references/records.md) and reconcile the record with the real session and files first.

## Stop Conditions

- Do not launch a disabled adapter, including the bundled Gemini and OpenCode declarations. See [references/adapters.md](references/adapters.md) for their permission gaps.
- Two agents are writing the same files: stop both where you can, and report.
- A record and the real state disagree: report the gap; do not start a second writer.
- Native approval needs interaction that this turn cannot provide: stop and return the blocker; never switch to automatic approval to finish.
- Cancel only runs this task started; never stop a process the record cannot prove is yours.

## Report

At acceptance: route, CLI, version and model, run ID, access, how it ran, what was sent, the result and how you checked it, the current owner, and the command to resume.
