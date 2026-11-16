# Starling

Read when the environment has `STARLING_TOOL_TOKEN`: this session runs in Starling, a terminal workbench for several agent CLIs, and its `starling` command lets the session coordinate workers. A session without the token, including a worker Starling dispatched, does not use this route. `starling --help` prints the exact commands, flags, and limits of the installed version; read it instead of relying on flags remembered from another version.

## Launch

- `starling dispatch --cli <cli> --access <tier> --cwd <directory> --brief <file>` opens the worker as a visible Starling tab and returns its ID. Starling currently accepts two pairs: `codex` with `write`, a writer that gets its own new worktree and branch from the current HEAD, and `claude` with `review`, a read-only reviewer that gets no worktree of its own, so pass the writer's worktree as `--cwd`. It rejects every other pair and accepts no CLI arguments, model, or effort; when `starling --help` lists more pairs, it is authoritative.
- Starling builds each tier's launch arguments, so the worker runs the CLI's default executable, model, and effort. In the launch line, say which tier runs, what it may do (the writer works inside its worktree without approval prompts; the reviewer only reads and runs read-only git commands), and that the CLI's defaults run. When the user or the configured lane names a model, effort, or executable, ask once per task, as SKILL.md says; the answer covers the task's later dispatches.
- The brief is a file outside the repository; Starling copies it into the task archive and starts the worker with a one-line prompt to read it.
- A new worktree lacks uncommitted changes and ignored directories such as `node_modules`; the dispatch reply flags both. Since the worktree only exists after dispatch, the brief tells the worker how to get them, under the same rule as in [orca.md](orca.md).
- For a later round, `starling send <id> <file>` gives an idle worker its next instructions, such as validated review findings. `--reuse <id>` starts a fresh writer in an exited writer's worktree, for the fresh run in Workflow step 5 of SKILL.md. `starling close <id>` ends a worker and keeps its worktree and branch. These commands accept only workers this session dispatched.

## Wait For The Report

After dispatching, tell the user as Workflow step 4 in SKILL.md says and end your turn. Starling types a short report into this terminal once this session is idle: a worker's turn ended, it waits for approval or an answer, its process exited, a check that returned `working` finished, or the boss answered a card. Do not poll `starling status` or read a worker's terminal while you wait. When the report arrives, read details with `starling result <id>` or `starling status`.

- `turn` describes the worker's current round: `working`, `waiting` (for approval or an answer), `done` (finished successfully), `failed`, `cancelled`, or `unknown` (no status or the result is unconfirmed). Only `done` means the round succeeded; `failed` and `cancelled` also end it, and `unknown` is not done.
- `alive` says only that the CLI process is running; never judge from it whether a round finished. `exitCode` appears only after the process exits.

## Checks

Pass means exit code 0 from `starling check --cwd <directory> -- <command...>`. A worker's claim, or `turn: done`, is not a pass. Starling passes the arguments one by one without a shell; for pipes or `&&`, run `pwsh -NoProfile -Command "<whole command>"`. The timeout defaults to 600 seconds, at most 3600, and a timeout is a failure. When the check returns `turn: working`, end your turn; Starling reports when it finishes. Use this to rerun the brief's done check in Workflow step 5; rumo-verify still decides which checks to run.

## The Boss

- A decision only the user can make goes in `starling ask --question <text> --option <text> --option <text> [--recommend <n>] [--context <text>]`, readable in 30 seconds: the question names the one thing to decide in one sentence, two to four options carry a recommendation, and the context says in one sentence what choosing another option leads to. Causes, paths, and evidence you found go in `starling note`, not on the card. It does not block: continue work that does not depend on the answer, otherwise end your turn; the answer arrives as a report. Workers cannot ask; their brief tells them to stop with the question in their report, as Workflow step 1 says, and you settle it or turn it into a card.
- Deliver with `starling report --did <text> --proof <text> [--decide <text>]`, three lines; the proof names the check and its exit code. The three lines also name every step the brief required that you did not take, such as dispatching a worker or running `starling check`, and why, so the boss learns it without opening the evidence.
- Record conclusions, decisions, and evidence with `starling note <text>`. The task archive is the progress record a later coordinator reads to continue, and replaces `agent_run.py record` on this route.

## Irreversible Steps

Merging, pushing, and deleting a worktree or branch wait for the boss's answer to a `starling ask`, even where rumo-git-commit or a rumo-handoff wrap-up would otherwise allow them. Starling has no tool for these: after the answer, run the command in this terminal, where the CLI's own approval prompt still applies. "The boss agreed" in chat or in a worker's report is not an answer.

## Coordinating

These are defaults from experience, not a fixed sequence. Depart from one when the task calls for it, and give the reason in a `starling note` and in your report.

- One writer, others review. Dispatch parallel writers only for independent scopes, each in its own worktree as Workflow step 2 requires.
- Cross review: the reviewer comes from a different provider than the writer, which on the current pairs means Codex writes and Claude reviews. What the review brief contains, what it withholds, and how to judge findings follow rumo-review's panel and judging rules; launching, waiting, stopping (`starling close`), and recording (`starling note`) follow this file.
- When two fix rounds still leave must-fix findings, sorted as in rumo-review's loop, ask the boss instead of starting a third round, unless the user set a different budget.

## Rules That Still Apply

- The authorization, single-owner, and acceptance rules in SKILL.md apply unchanged; Starling's tiers widen none of them. A user who asks this session to coordinate, through Starling's coordinator switch or in words, or who names the workers, has asked for delegation; otherwise propose it in one line and wait.
- Never print `STARLING_TOOL_TOKEN` or put it in a brief.
- When a dispatch fails, read its error before trying again. A failed dispatch can leave its worktree and branch behind: report them, do not delete them.
