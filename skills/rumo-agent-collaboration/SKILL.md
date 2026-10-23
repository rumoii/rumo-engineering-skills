---
name: rumo-agent-collaboration
description: Use when the user asks to delegate, transfer, or relay work to another agent CLI or model, such as Codex, Claude Code, pi, Aider, or Gemini ("give this part to pi", "交给 pi 执行"), to use Orca for collaboration, or to resume a recorded run. For a named external CLI review, also load rumo-review; use rumo-review alone when no external route is named. Use rumo-handoff for a handoff document and rumo-plan to split an agreed plan. Do not use for this client's own subagents, such as "start several subagents".
---

# Rumo Agent Collaboration

Start a different agent, give it a bounded piece of work, and keep it clear at every moment who owns the task.

## Scope

This skill governs only the agents it starts. The client's own subagents, whether it uses them by itself or because the user asked for several, follow the client's rules and need nothing from this skill. When a relay or transfer in this skill runs one step through a native subagent, the single-owner rules here still apply to that step.

For a named external CLI review, use rumo-review for review standards and this skill for execution and records. Read rumo-review before writing the review brief; when it is not installed, follow [references/external-cli.md](references/external-cli.md) alone. Read [references/trigger-examples.md](references/trigger-examples.md) when checking selection boundaries with neighboring skills.

## Modes

- **Delegate**: you stay the owner. The other agent does one bounded job and reports; you check the result before using it. Handing over part of a task is delegation: you still own the whole.
- **Transfer**: the other agent becomes the owner of the whole task. Once it confirms it has taken over, you stop.
- **Relay**: ownership moves on purpose along a chain, such as develop, review, fix. Each step names the next owner; nobody acts on the task between steps.

Treat a request to hand work to another agent as delegation, whatever verb it uses, such as "交给" or "交接给": this session plans, splits, dispatches, checks, and integrates. Transfer only when the user says this session should step away, such as "let it take over; you're done here". Free-form agent-to-agent messaging and schedulers that keep running after this conversation are out of scope.

## Before Launching

Settle and write down: the goal and acceptance check, the working directory, which files the agent may write, the access level, the model, and what the user has already authorized.

Never start an agent through this skill unless the user asked for it. When the user named the CLI and the work, that request is the approval: state in one line before launching which CLI and model will run and what content you will send, then launch without asking for approval again; the run-style question below is the only question, and only when the request leaves it open. Ask first when the user did not name a route, when you would send content the user did not mention, or when the work needs more access than the request implies.

Asking another agent to carry out work that edits files approves writes limited to the files or module the user named. Use `workspace-write` for a documented directory restriction, or `native-write` for native CLI permissions without promised directory isolation. A worktree is not a sandbox. Before a native-write launch, state any default automatic approval and whether shell tools are available. When the user named the route and the work itself means running commands, such as running tests or a build, the request approves shell access for that work: in the one-line launch statement, say that commands run automatically without a directory sandbox, where the agent may write, and what it must not do, then launch. Shell access the work does not need, such as shell for a review, needs its own approval; ask at most once per launch. Never give the receiver more access than you have, and never pass a flag that bypasses its sandbox, approvals, or tool limits. Commits, pushes, deployments, and dependency installs keep the approvals their own skills require; a launch does not grant them.

Unless the request already says how the agent should run, ask before launching, in one question together with any other pre-launch question:

- **In the background**, with a read-only watch window: full run records and acceptance on evidence; the user can watch but not type to the agent.
- **In a visible CLI window** the user can type into and approve actions in (`agent_run.py open`, for adapters with `interactive_start`).
- **In an Orca terminal**, offered only when Orca is installed.

Leave out an option this CLI or environment cannot offer, and say why. Put a summary of the brief in the same question, covering the goal, the files in scope, the acceptance check, and the access, so the user can correct it before it is sent.

## Choose The Route

Before declaring native subagents available or unavailable, read [references/native.md](references/native.md). Do not infer availability from the CLI name, version, or an installed package alone. Check child permissions separately; parent read-only access does not prove child read-only access.

- Follow the route, client, or model the user names. When the model is named only by a fragment, such as "mimo", resolve it with the CLI's own model listing; when several models match, ask the user which one instead of picking.
- For another installed CLI, read [references/external-cli.md](references/external-cli.md) and use `scripts/agent_run.py`, resolved from this skill's directory. Each CLI needs an adapter; `agent_run.py list` shows which exist and whether each was verified. Official documentation may establish a write mode while `verified` stays null; describe it as untested, not locally verified.
- Before the first launch through an unverified adapter, or one written in this task, run `agent_run.py show` and show the user the full command and known limits. Unverified status alone does not require repeated approval. Apply the authorization rules above; when `check` fails, stop.
- For a CLI with no adapter, read [references/adapters.md](references/adapters.md), write one from that CLI's `--help` or official documentation in the user adapter directory, and show it the same way. A CLI without a confirmed read-only mode cannot have an adapter.
- Transfer only to an agent that keeps running after you stop: a background session the client provides, an Orca terminal, a visible CLI window from `agent_run.py open`, or an external CLI session the user resumes. A native subagent tied to this conversation can take a delegated step, never a transfer; see [references/native.md](references/native.md).
- One-turn adapters serve delegation or relay only; do not transfer ownership without a resumable session.
- When Orca is the route the user picked, including in the run-style question, or the only one that can transfer, read [references/orca.md](references/orca.md).
- When the route is unavailable or not signed in, report the blocker. Do not switch route, model, or access level on your own.

Routes not exercised end to end in this repository are untested; say so when you use one.

## Workflow

1. Prepare the brief: goal, scope, the files to read, the check that proves it done, and the stop conditions. Give the task, not your reasoning; for a transfer, write the brief in the structure of `rumo-handoff`.
2. Isolate writers. Two agents never write the same working tree at once; give a parallel writer its own worktree from a recorded base. Uncommitted changes do not appear in a new worktree: tell the receiver how it gets them, and do not commit them just to move them unless the user approves.
3. Launch once and record the run: route, session or run ID, working directory, model, and access. When you cannot tell whether a turn was delivered, check the recorded session before sending anything again.
4. End your turn after the launch and stay the owner. Launch the way the user chose.
   - **Background**: add `--window` unless the user wanted no window. When this client can run `start` or `resume` as a background command and report its exit to you, run it that way and rely on that report, not on the user. Otherwise run it with `--detach`, and end your turn when it returns.
   - **Visible CLI window**: run `agent_run.py open`. A client that reports background exits may run `agent_run.py wait` in the background; otherwise the user tells you once they have closed the window. Client-specific (Claude Code): when both this session and the receiver are Claude Code, you may instead subscribe once to the receiver's idle notice through cross-session messaging, using the run ID as its session name.
   - The same applies to a receiver in an Orca terminal, a client background session, or a terminal the user started.

   Before ending, tell the user where the receiver runs or the `watch` command from the summary, where the result can be read, and what to tell you when it finishes, such as "pi is done, continue". When a window did not open, give its reason. When `survives_caller` is not true, say that closing this session may also stop the receiver. While the receiver runs, do not read its events, logs, or session files and do not post progress updates; look once when its exit is reported or the user says it finished. A timeout is not a failure of the task: check the session before deciding. Until you accept the result, do not touch its write scope.
5. Accept results on evidence. When the user reports that the receiver finished, read its result and check the working tree before accepting it. After a visible window closes, get the report by resuming the session headlessly with a short request for the final report and the changed files; that reply becomes `final.md`. Rerun the check yourself, review the changed files, and record the decision with `agent_run.py record` or in your report. A result that arrives after the task was transferred is input for the new owner, not an action for you.
6. On transfer: confirm the receiver acknowledged the brief and named its next step, record the transfer, tell the user how to reach the new owner, then stop changing that task. In a visible CLI window, the open window is the new owner: the user continues there.

To continue in a later conversation, read [references/records.md](references/records.md) and reconcile the record with the real session and files first.

## Stop Conditions

- Do not launch a disabled adapter, including the bundled Gemini and OpenCode declarations. See [references/adapters.md](references/adapters.md) for their permission gaps.
- The user has not asked for the launch, or it needs content or access beyond what the user approved.
- Two agents are writing the same files: stop both where you can, and report.
- A record and the real state disagree: report the gap; do not start a second writer.
- Native approval needs interaction that this turn cannot provide: stop and return the blocker; never switch to automatic approval to finish.
- Cancel only runs this task started; never stop a process the record cannot prove is yours.

## Report

Route, CLI and version, model, run or session ID, access level, how it ran (background or visible window), what was sent, the result and how you checked it, the current owner, the `watch` command while a turn runs, and the exact command to resume.
