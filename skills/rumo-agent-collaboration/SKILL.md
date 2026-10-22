---
name: rumo-agent-collaboration
description: Use when the user asks to delegate or transfer work to another agent CLI or model, such as Codex, Claude Code, pi, qwen, grok, Cursor, Gemini, OpenCode, GitHub Copilot CLI, Aider, Cline CLI, or Goose ("give this part to pi", "交给 pi 执行", "用 mimo 的 pi 跑", "let Codex do it"); to relay development, review, and fixes between agents; to use Orca for collaboration; or to resume a recorded run. Supports read-only and development tasks with explicit access and one owner per task. For a named external CLI review, pair with rumo-review. Use rumo-review alone for reviews without an external route, rumo-handoff for a handoff document, and rumo-plan to split an agreed plan. Do not use for this client's own subagents, such as "start several subagents", which the client handles itself.
---

# Rumo Agent Collaboration

Start a different agent, give it a bounded piece of work, and keep it clear at every moment who owns the task.

## Scope

This skill governs only the agents it starts. The client's own subagents, whether it uses them by itself or because the user asked for several, follow the client's rules and need nothing from this skill. When a relay or transfer in this skill runs one step through a native subagent, the single-owner rules here still apply to that step.

For a named external CLI review, use rumo-review for review standards and this skill for execution and records. Read [references/trigger-examples.md](references/trigger-examples.md) when checking selection boundaries with neighboring skills.

## Modes

- **Delegate**: you stay the owner. The other agent does one bounded job and reports; you check the result before using it. Handing over part of a task is delegation: you still own the whole.
- **Transfer**: the other agent becomes the owner of the whole task. Once it confirms it has taken over, you stop.
- **Relay**: ownership moves on purpose along a chain, such as develop, review, fix. Each step names the next owner; nobody acts on the task between steps.

When the request does not make clear whether part or all of the task moves, ask. Free-form agent-to-agent messaging and schedulers that keep running after this conversation are out of scope.

## Before Launching

Settle and write down: the goal and acceptance check, the working directory, which files the agent may write, the access level, the model, and what the user has already authorized.

Never start an agent through this skill unless the user asked for it. When the user named the CLI and the work, that request is the approval: state in one line before launching which CLI and model will run and what content you will send, then launch without asking again. Ask first when the user did not name a route, when you would send content the user did not mention, or when the work needs more access than the request implies.

Asking another agent to carry out work that edits files approves writes limited to the files or module the user named. Use `workspace-write` for a documented directory restriction, or `native-write` for native CLI permissions without promised directory isolation. A worktree is not a sandbox. Before a native-write launch, state any default automatic approval and whether shell tools are available. Wider access, such as shell access for pi, needs its own approval. Never give the receiver more access than you have, and never pass a flag that bypasses its sandbox, approvals, or tool limits. Commits, pushes, deployments, and dependency installs keep the approvals their own skills require; a launch does not grant them.

## Choose The Route

Before declaring native subagents available or unavailable, read [references/native.md](references/native.md). Do not infer availability from the CLI name, version, or an installed package alone. Check child permissions separately; parent read-only access does not prove child read-only access.

- Follow the route, client, or model the user names. When the model is named only by a fragment, such as "mimo", resolve it with the CLI's own model listing; when several models match, ask the user which one instead of picking.
- For another installed CLI, read [references/external-cli.md](references/external-cli.md) and use `scripts/agent_run.py`, resolved from this skill's directory. Each CLI needs an adapter; `agent_run.py list` shows which exist and whether each was verified. Official documentation may establish a write mode while `verified` stays null; describe it as untested, not locally verified.
- Before the first launch through an unverified adapter, or one written in this task, run `agent_run.py show` and show the user the full command and known limits. Unverified status alone does not require repeated approval. Apply the authorization rules above; when `check` fails, stop.
- For a CLI with no adapter, read [references/adapters.md](references/adapters.md), write one from that CLI's `--help` or official documentation in the user adapter directory, and show it the same way. A CLI without a confirmed read-only mode cannot have an adapter.
- Transfer only to an agent that keeps running after you stop: a background session the client provides, an Orca terminal, or an external CLI session the user resumes. A native subagent tied to this conversation can take a delegated step, never a transfer; see [references/native.md](references/native.md).
- One-turn adapters serve delegation or relay only; do not transfer ownership without a resumable session.
- When Orca is the route the user picked, or the only one that can transfer, read [references/orca.md](references/orca.md).
- When the route is unavailable or not signed in, report the blocker. Do not switch route, model, or access level on your own.

Routes not exercised end to end in this repository are untested; say so when you use one.

## Workflow

1. Prepare the brief: goal, scope, the files to read, the check that proves it done, and the stop conditions. Give the task, not your reasoning; for a transfer, write the brief in the structure of `rumo-handoff`.
2. Isolate writers. Two agents never write the same working tree at once; give a parallel writer its own worktree from a recorded base. Uncommitted changes do not appear in a new worktree: tell the receiver how it gets them, and do not commit them just to move them unless the user approves.
3. Launch once and record the run: route, session or run ID, working directory, model, and access. When you cannot tell whether a turn was delivered, check the recorded session before sending anything again.
4. Wait without polling when the client can notify you; otherwise wait once with a long enough timeout, or end your turn as described next. A timeout is not a failure of the task: check the session before deciding. Completion notification stays the first choice: when you launched the run as a background command whose exit this client reports to you, rely on that report, not on the user. Only when no notification can reach you, because this client cannot notify or the receiver runs where it cannot watch, such as an Orca terminal, a client background session, or a terminal the user started, you may end your turn after the launch and stay the owner. Before ending, tell the user where the receiver runs, where its result can be read, and what to tell you when it finishes. Until then, do not touch its write scope.
5. Accept results on evidence. When the user reports that the receiver finished, read its result and check the working tree before accepting it. Rerun the check yourself, review the changed files, and record the decision with `agent_run.py record` or in your report. A result that arrives after the task was transferred is input for the new owner, not an action for you.
6. On transfer: confirm the receiver acknowledged the brief and named its next step, record the transfer, tell the user how to reach the new owner, then stop changing that task.

To continue in a later conversation, read [references/records.md](references/records.md) and reconcile the record with the real session and files first.

## Stop Conditions

- Do not launch a disabled adapter, including the bundled Gemini and OpenCode declarations. See [references/adapters.md](references/adapters.md) for their permission gaps.
- The user has not asked for the launch, or it needs content or access beyond what the user approved.
- Two agents are writing the same files: stop both where you can, and report.
- A record and the real state disagree: report the gap; do not start a second writer.
- Native approval needs interaction that this turn cannot provide: stop and return the blocker; never switch to automatic approval to finish.
- Cancel only runs this task started; never stop a process the record cannot prove is yours.

## Report

Route, CLI and version, model, run or session ID, access level, what was sent, the result and how you checked it, the current owner, and the exact command to resume.
