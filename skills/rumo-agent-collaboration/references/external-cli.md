# External CLI Through agent_run.py

Read when the route is another installed agent CLI. `scripts/agent_run.py` runs one non-interactive turn at a time, records it, and resumes the same session by ID. It drives any CLI that has an adapter; see [adapters.md](adapters.md) for the bundled list and for adding one.

## Quick Start

```text
# Read-only work: runs in the background and opens a watch window for the user
python <skill-dir>/scripts/agent_run.py start <cli> --cwd <dir> --prompt-file <brief.md> --access read-only [--model <id>] [--detach]
# Work that edits files or runs commands: a visible CLI window
python <skill-dir>/scripts/agent_run.py open <cli> --cwd <dir> --prompt-file <brief.md> --access <level> [--model <id>]
# After the user says it finished
python <skill-dir>/scripts/agent_run.py status <run-id>
python <skill-dir>/scripts/agent_run.py record <run-id> --outcome accepted|rejected|note --note "<text>"
```

- `start` and `open` check the CLI and the adapter's flags themselves, so do not run `list`, `check`, or `show` first for a verified adapter. Only before the first launch through an unverified adapter or one written in this task, run `agent_run.py show` and show the user the full command and known limits. Unverified status alone does not require repeated approval. Official documentation may establish a write mode while `verified` stays null: call it untested, not locally verified.
- In a client that runs background commands and reports their exit, run `start` that way without `--detach`; elsewhere add `--detach`. `--no-window` skips the watch window.
- Write the brief to a file outside the repository. Use `py -3` instead of `python` on Windows when that is the configured launcher.

Read on only when a command refuses, a run looks wrong, or the work needs more than this:

- [Check First](#check-first): `list`, `check`, `show`, disabled adapters, sign-in
- [Resolve The Model](#resolve-the-model)
- [Access Levels](#access-levels)
- [Run](#run): every command, exit codes, `--detach`, `watch`, the watch window, `wait`, `runs`, `open`
- [Brief Contents](#brief-contents), [Worktrees](#worktrees), [Transfer Through A CLI](#transfer-through-a-cli)

## Check First

```text
python <skill-dir>/scripts/agent_run.py list
python <skill-dir>/scripts/agent_run.py check <cli>
python <skill-dir>/scripts/agent_run.py show <cli> --access read-only [--model <id>]
```

- `list` shows each adapter's source, whether it was verified, its access levels, whether the CLI is installed, and `disabled_reason` when execution is blocked.
- `check` confirms the CLI is installed and that its help lists the adapter's declared flags. A failed help command or missing flag exits 2: stop and report it rather than guessing a replacement flag. This does not validate flag values or prove runtime permissions. `version_drift` is a warning to report, not a blocker.
- `show` prints the exact start and resume commands without running anything. Show it to the user before the first launch through an unverified or newly written adapter.

`disabled_reason` blocks `check`, `start`, and `resume` before the CLI is invoked; `show` stays available for inspection. Gemini CLI and OpenCode are bundled but disabled pending reliable read-only permissions. A Gemini model behind another client still uses that client's adapter. First-use disclosure does not require another confirmation when the named route, task, and content are already authorized.

A CLI that is installed but not signed in fails on the first turn; never sign in, copy credentials, or change its configuration for the user.

### Subagent Availability In This Invocation

When the task needs the receiving client's own subagents, apply [native.md](native.md) to its actual invocation before claiming they are available. The bundled pi adapter intentionally disables MCP and extension discovery with `--no-mcp` and `--no-extensions`. An installed subagent package does not make its tools available in that invocation. This is a launch restriction, not evidence that pi lacks subagents. Keep the adapter's restrictions; do not remove them or add shell access to recover subagents. If the required child capability or its read-only policy cannot be confirmed, use an already authorized verified route or report the blocker.

## Resolve The Model

Pass the model with `--model`; the record keeps the exact value sent.

- pi: run `pi --list-models <fragment>`, for example `pi --list-models mimo`, and pass the full `provider/id` it prints. Cursor (`cursor-agent --list-models`) and OpenCode (`opencode models`) list models the same way.
- claude: `--model` accepts an alias such as `opus` or a full model ID; pass what the user named.
- codex, qwen, grok, gemini, copilot, aider, cline, goose: pass the name as the user gave it; an unknown name fails on the first turn. Report that failure instead of trying other names.
- More than one listed match for a fragment: ask the user which one.

Without a named model, omit `--model` so the CLI uses its configured default, and report that default from the first turn's output when it shows one.

## Access Levels

`--access` accepts `read-only`, `workspace-write`, or `native-write`. Each adapter maps a level to CLI flags or environment settings. `show` prints the command, environment names, and notes. A missing level is refused. Officially documented development modes may be offered with `verified: null`; that means untested, not locally verified. Pick read-only unless writes were authorized.

`workspace-write` is intended for a working-directory restriction. `native-write` keeps native CLI permissions without promising directory isolation. Disclose default automatic approval and shell availability before launching native-write. Saved records keep the flags they ran with. A tool allowlist is not an OS directory sandbox, so pi's write level is `native-write`: edits without asking, no shell. Wider access still requires approval.

Copilot and Aider native-write edit files; the caller executes requested checks. Cline Act has a documented auto-approve default. Goose approve mode can require interaction: if this turn cannot collect approval, stop and report it without changing mode. Goose read-only is chat-only, so include the code or diff in the brief.

## Run

```text
python <skill-dir>/scripts/agent_run.py start <cli> --cwd <dir> --prompt-file <brief.md> --access read-only [--model <id>] [--timeout 1800]
python <skill-dir>/scripts/agent_run.py start <cli> --cwd <isolated-dir> --prompt-file <brief.md> --access native-write
python <skill-dir>/scripts/agent_run.py resume <run-id> --prompt-file <follow-up.md>
python <skill-dir>/scripts/agent_run.py start <cli> ... [--detach] [--no-window]
python <skill-dir>/scripts/agent_run.py open <cli> --cwd <dir> --prompt-file <brief.md> --access read-only [--model <id>]
python <skill-dir>/scripts/agent_run.py watch <run-id> [--turn <n>] [--hold]
python <skill-dir>/scripts/agent_run.py wait <run-id> [--turn <n>]
python <skill-dir>/scripts/agent_run.py runs [--active]
python <skill-dir>/scripts/agent_run.py status <run-id>
python <skill-dir>/scripts/agent_run.py cancel <run-id>
python <skill-dir>/scripts/agent_run.py record <run-id> --outcome accepted|rejected|transferred|note --note "<text>"
```

- Write the brief to a file outside the repository; the script sends it on stdin or as the file the adapter names, never on the command line.
- The timeout must be finite and greater than zero. Prompt stdin is backed by the recorded file, so a child that never reads it cannot block the recorder before the timeout.
- Starting and resuming require a reliable process identity implementation, currently Windows and Linux/WSL. Other platforms refuse before launch; inspecting records remains available.
- Each command prints a UTF-8 JSON summary: state, exit code, session ID, whether the adapter was verified, the path of the final reply, and `interactive_resume` with the directory and command a person uses to continue the session by hand.
- Exit codes: `0` the turn finished with a reply; `1` it failed, was cancelled, or produced no reply; `2` refused or an I/O/preflight operation failed (inspect the record before retrying); `3` the turn hit the timeout and was stopped. A failed or empty turn is not evidence that work is done or that there is nothing to find.
- `--detach` on `start` or `resume` hands the turn to a recorder process outside the caller's process group and returns once the turn is launched. Exit 0 then means launched, not finished: the summary's `state` stays a running state, and it adds `recorder_pid`, `recorder_pid_started`, `watch` (the command that follows the turn), and `survives_caller`. On Windows `survives_caller` is false when the caller's job object forbids breakaway, so ending the caller's session may also end the recorder; on Linux it is null, because a new session does not survive a cgroup or container teardown. A recorder that does not move the turn past `created` makes `start` exit 2 with the end of `recorder.log` from the run directory.
- `watch` prints one line per event that the adapter's `progress` rules match, such as a tool call or a reply, and skips the brief and other user messages. Without rules it prints an event count every 10 seconds and the start of the final reply. It waits up to a minute for a turn that is not recorded yet, ends with the turn, and exits with the turn's code; it exits 2 when the record still shows a running turn whose process has been gone for a minute, or a turn created but never launched. `--hold` waits for Enter at the end so a window stays readable. Interrupting `watch` leaves the run running.
- `start` and `resume` open a terminal window running `watch --hold` for the new turn unless given `--no-window`; the summary's `window` says whether it opened, how (`wt-tab`, `console`, or `x-terminal-emulator`), and why not. On Windows, every window opens as a tab of one Windows Terminal window named `rumo-agents` when `wt` is available and no argument contains `;`; otherwise as a new console. On Linux it needs `DISPLAY` or `WAYLAND_DISPLAY` and `x-terminal-emulator`, and `opened` means only that the terminal did not fail within a second, not that a window appeared; that path is untested here. A tab uses Windows Terminal's environment, not the caller's.
- `wait` prints nothing until the turn ends, then the summary, and exits with the turn's code. Use it only as a background command in a client that reports its exit; do not loop on it.
- `runs` lists recorded runs newest first with their mode, state, and the command to watch an active headless run or reopen a finished session; `--active` keeps only runs still running. An unreadable record appears as an error row.
- `open` starts the CLI interactively, through the adapter's `interactive_start`, in a terminal window the user can type into; the window opens the same way as the watch window. The brief stays in `turns/1/prompt.md`; only a one-line pointer to it travels on the command line. A host process inside the window records the turn as `interactive` while the CLI runs and `closed` when it exits or, best effort, when the window is closed; a host killed before it records leaves a turn to reconcile with `cancel`. The access flags are the adapter's for that level, and the CLI asks the user in the window for anything those flags do not pre-approve. There is no timeout. Only adapters with a preassigned session offer `interactive_start`, so that after the window closes `resume` can ask the same session for its final report. The bundled claude, qwen, pi, and grok adapters have one; codex reports its session only in headless events and has none.
- Long turns: in a client that runs background commands and notifies on completion, run `start` or `resume` that way; otherwise use `--detach`. Either way, set `--timeout` above the longest expected turn, because the recorder stops the turn at that limit.
- `resume` refuses disabled adapters, a previous turn still running or without a recorded end, and an adapter whose session source is `none`. For a turn with no recorded end, inspect the backend session first. `cancel` can mark it `abandoned` only when the process is confirmed gone or its PID has a different strong identity. Unknown identity, including an old POSIX timestamp, blocks automatic cancellation and recovery; see [records.md](records.md).

## Brief Contents

Give the receiver the goal, the files in scope, the acceptance check, the access it has, what it must not do (commit, push, install, touch files outside scope), and what to return: changed files, checks run with results, and anything unfinished. Withhold your own reasoning and earlier conclusions when you want an independent result.

## Worktrees

`--cwd` is where the receiver works. For a parallel writer, create a worktree on its own branch from a recorded base commit and point `--cwd` at it. A worktree separates files; it is not a permission sandbox. Remove it only after its branch lands or the user discards it, following `rumo-filesystem-safety` when installed.

## Transfer Through A CLI

Transfer requires a recorded resumable session. Aider, Cline, and Goose are one-turn adapters here: use them for delegation or relay steps, not ownership transfer. Interactive resume commands use native defaults and may differ from recorded access: inspect them before reopening; do not claim they preserve the sandbox.

With `open`, the visible window is the receiver taking over: record `--outcome transferred` once the user confirms it started, and stop changing the task. Otherwise, the first turn proves the receiver read the brief and can work. Ask it to restate the goal and its next step in that turn. After it does, record `--outcome transferred`, give the user the `interactive_resume` command, and stop changing the task.
