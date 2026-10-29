---
name: rumo-agent-collaboration
description: Use when the user asks to delegate, transfer, or relay work to another agent CLI or model, such as Codex, Claude Code, pi, qwen, or grok ("give this part to pi", "交给 pi 执行"), to use Orca for collaboration, or to resume a run this skill recorded. Not for taking over another agent's session yourself. Reviews by another model, even a named CLI, belong to rumo-review alone. Use rumo-handoff for a handoff document and rumo-plan to split an agreed plan. A bare request for this client's own subagents, such as "start several subagents", does not need this skill.
---

# Rumo Agent Collaboration

Hand a bounded piece of work to another agent where the user can see it, end your turn, and accept the result on evidence.

## Scope

This skill picks the route for the agents it starts. A lane on the current client's own CLI, such as a `claude` lane inside Claude Code or a `codex` lane inside Codex, runs as the client's own subagent: it starts no second CLI and returns its result to this session. Every other lane runs through `scripts/agent_run.py`. A plain request for the client's subagents with no lane or model follows the client's own rules, except that a relay or transfer step run through one keeps the single-owner rules here. Before declaring native subagents available or unavailable, read [references/native.md](references/native.md).

Reviews by another model, including a named external CLI, belong to rumo-review alone: its panel runs them with this skill's scripts. [references/trigger-examples.md](references/trigger-examples.md) marks the boundaries with neighboring skills.

## Ownership

You stay the owner: treat any request to hand work to another agent as delegation, whatever verb it uses, such as "交给" or "交接给". Transfer ownership only when the user says this session should step away, such as "let it take over; you're done here". In a relay (develop, review, fix), each step names the next owner, and nobody acts on the task between steps. Free-form agent-to-agent messaging and schedulers that keep running after this conversation are out of scope.

## Authorization

Never start an agent through this skill unless the user asked for it. When the user named the CLI and the work, that request is the approval: state in one line before launching which CLI, model, and effort will run and what content you will send, then launch. Keep it to that line; do not ask again. A configured `delegate` lane counts as a named CLI. Ask first when the user named no route and none is configured, when you would send content the user did not mention, or when the work needs more access than the request implies.

- Pick read-only unless the work edits files; asking for edits approves writes limited to the files or module the user named. Use `workspace-write` only where the adapter documents a directory restriction. `native-write` has no directory isolation: state its default automatic approval and whether shell tools are available. A worktree is not a sandbox.
- When the work itself means running commands, such as tests or a build, the request approves shell access for that work: say in the same line that commands run automatically without a directory sandbox, where the agent may write, and what it must not do. Shell access the work does not need, such as shell for a review, needs its own approval; ask at most once per launch.
- Never give the receiver more access than you have, and never pass a flag that bypasses its sandbox, approvals, or tool limits. The Orca route is the exception the user configured: agents run with the default arguments the user set in Orca, and pi with the matching worktree setting in [references/orca.md](references/orca.md); add nothing beyond them and do not change them. Commits, pushes, deployments, and dependency installs keep the approvals their own skills require.

## Workflow

1. **Brief.** Write the goal, scope, files to read, the stop conditions, and the exact command or observation that proves the work done, to a file outside the repository; acceptance reruns that check. Give the task, not your reasoning; for a transfer, use the structure of `rumo-handoff`. Set the detail by the kind of work, not by the receiver's strength: work to carry out gets the steps, scope, and acceptance spelled out; work to design gets the goal, constraints, and how the result will be judged, and suits the strongest lane. A weaker lane gets smaller stages and more checkpoints. Name the report path and a line the receiver prints when done, so a wait can recognize the finish.
2. **Isolate writers.** Two agents never write the same working tree at once; give a parallel writer its own worktree from a recorded base. Uncommitted changes do not appear in a new worktree: tell the receiver how it gets them, and do not commit them just to move them unless the user approves.
3. **Launch once, where the user can see it.** Follow the route, model, and effort the user names. For anything they leave out, use the user's configuration: `scripts/agent_config.py lanes delegate` when no CLI is named, taking the lane whose `use` label fits the work and otherwise the first, and the configured lane's model and effort when the named CLI has one; pass them as `--model`, `--effort`, and `--executable` when the lane has one. Exit 3 means nothing is configured: ask, and mention that `rumo-setup` saves the choice.
   - Match the lane to the work when the lanes differ in strength: routine edits, tests, and searches suit a cheaper lane; work that the risk gate in `rumo-coding-guidelines` rates high, or that spans modules, suits the strongest configured lane. Say which lane you chose and why.
   - Pick the route. A lane on the current client's own CLI runs as a native subagent with the lane's model and effort ([references/native.md](references/native.md)); when the subagent tool is missing or cannot take that model or effort, run the same lane through `scripts/agent_run.py`; never drop or change the model. Read-only work on another installed CLI runs through `scripts/agent_run.py start`, resolved from this skill's directory ([references/external-cli.md](references/external-cli.md)), even inside Orca, because only an adapter enforces read-only. Work that edits files or runs commands goes to an Orca worktree when this session runs inside Orca, whose terminals set `ORCA_TERMINAL_HANDLE` ([references/orca.md](references/orca.md)); otherwise it goes to `agent_run.py open`, a CLI window the user can type into, even when Orca is installed. When the CLI has no interactive template, use `start` and say why.
   - Through `agent_run.py`, a CLI with no adapter needs one first ([references/adapters.md](references/adapters.md)); a CLI without a confirmed read-only mode cannot have an adapter. The Orca route needs no adapter.
4. **Tell the user and end your turn.** In one short message: where the receiver runs, where the result will be, and how you will learn that it finished, which for a client that cannot be woken when a background run ends means the user telling you; the route's reference says what to add, such as the `watch` command. Leave the full report for acceptance. While the receiver runs, read its output only to learn whether it finished or stalled, as the route's reference describes; otherwise do not read its events, logs, or session files, and do not post progress updates. Until you accept the result, do not touch its write scope.
5. **Accept on evidence.** When the receiver finishes, read its result and check the working tree before accepting it. Rerun the brief's done check yourself. When the result fails it, do not patch it up in the same session: start a fresh run with the original brief, every later instruction, and the failed run's report and changes, and tell the user when a stronger lane would fit the work better; switch lanes only with their agreement. When a receiver stops partway, for example out of quota, another lane may continue in the same worktree once the user agrees; its brief gives the original brief's path, what the first receiver did (unverified), what remains, a ban on reset, stash, or discarding the changes, and any failing-test evidence still owed. After a visible window closes, get the report by resuming the session headlessly with a short request for the final report and the changed files. Rerun the check yourself and record the decision with `agent_run.py record`, or in your report for Orca and native routes. A timeout is not a failure of the task: check the session before deciding.
6. **Transfer.** Only to an agent that keeps running after you stop, never to a native subagent tied to this conversation; do not transfer ownership without a resumable session. Confirm the receiver acknowledged the brief and named its next step, record the transfer, tell the user how to reach the new owner, then stop changing that task. A result that arrives later is input for the new owner, not an action for you.

To continue in a later conversation, read [references/records.md](references/records.md) and reconcile the record with the real session and files first.

## Stop Conditions

- Do not launch a disabled adapter, including the bundled Gemini and OpenCode declarations. See [references/adapters.md](references/adapters.md) for their permission gaps.
- Two agents are writing the same files: stop both where you can, and report.
- A record and the real state disagree: report the gap; do not start a second writer.
- Native approval needs interaction that this turn cannot provide: stop and return the blocker; never switch to automatic approval to finish.
- Cancel only runs this task started; never stop a process the record cannot prove is yours.
- The route is unavailable, not signed in, or refused: report the blocker. Do not switch route, model, or access level on your own.
- You cannot tell whether a turn was delivered: check the recorded session before sending anything again.

## Report

At acceptance: route, CLI, version and model, run ID, access, how it ran, what was sent, the result and how you checked it, the current owner, and the command to resume. Do not describe an adapter as tested end to end unless its `verified.live_run` is true.
