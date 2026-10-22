# External CLI Through agent_run.py

Read when the route is another installed agent CLI. `scripts/agent_run.py` runs one non-interactive turn at a time, records it, and resumes the same session by ID. It drives any CLI that has an adapter; see [adapters.md](adapters.md) for the bundled list and for adding one.

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

Use `py -3` instead of `python` on Windows when that is the configured launcher.

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

`workspace-write` is intended for a working-directory restriction. `native-write` keeps native CLI permissions without promising directory isolation. Disclose default automatic approval and shell availability before launching native-write. Existing mappings and saved records keep their flags; a tool allowlist, including pi's existing write level, is not an OS directory sandbox. Wider access still requires approval.

Copilot and Aider native-write edit files; the caller executes requested checks. Cline Act has a documented auto-approve default. Goose approve mode can require interaction: if this turn cannot collect approval, stop and report it without changing mode. Goose read-only is chat-only, so include the code or diff in the brief.

## Run

```text
python <skill-dir>/scripts/agent_run.py start <cli> --cwd <dir> --prompt-file <brief.md> --access read-only [--model <id>] [--timeout 1800]
python <skill-dir>/scripts/agent_run.py start <cli> --cwd <isolated-dir> --prompt-file <brief.md> --access native-write
python <skill-dir>/scripts/agent_run.py resume <run-id> --prompt-file <follow-up.md>
python <skill-dir>/scripts/agent_run.py status <run-id>
python <skill-dir>/scripts/agent_run.py cancel <run-id>
python <skill-dir>/scripts/agent_run.py record <run-id> --outcome accepted|rejected|transferred|note --note "<text>"
```

- Write the brief to a file outside the repository; the script sends it on stdin or as the file the adapter names, never on the command line.
- The timeout must be finite and greater than zero. Prompt stdin is backed by the recorded file, so a child that never reads it cannot block the recorder before the timeout.
- Starting and resuming require a reliable process identity implementation, currently Windows and Linux/WSL. Other platforms refuse before launch; inspecting records remains available.
- Each command prints a UTF-8 JSON summary: state, exit code, session ID, whether the adapter was verified, the path of the final reply, and `interactive_resume` with the directory and command a person uses to continue the session by hand.
- Exit codes: `0` the turn finished with a reply; `1` it failed, was cancelled, or produced no reply; `2` refused or an I/O/preflight operation failed (inspect the record before retrying); `3` the turn hit the timeout and was stopped. A failed or empty turn is not evidence that work is done or that there is nothing to find.
- Long turns: in a client that runs background commands and notifies on completion, run `start` or `resume` that way; otherwise run it once in the foreground with a client timeout longer than `--timeout`.
- `resume` refuses disabled adapters, a previous turn still running or without a recorded end, and an adapter whose session source is `none`. For a turn with no recorded end, inspect the backend session first. `cancel` can mark it `abandoned` only when the process is confirmed gone or its PID has a different strong identity. Unknown identity, including an old POSIX timestamp, blocks automatic cancellation and recovery; see [records.md](records.md).

## Brief Contents

Give the receiver the goal, the files in scope, the acceptance check, the access it has, what it must not do (commit, push, install, touch files outside scope), and what to return: changed files, checks run with results, and anything unfinished. Withhold your own reasoning and earlier conclusions when you want an independent result.

## Worktrees

`--cwd` is where the receiver works. For a parallel writer, create a worktree on its own branch from a recorded base commit and point `--cwd` at it. A worktree separates files; it is not a permission sandbox. Remove it only after its branch lands or the user discards it, following `rumo-filesystem-safety` when installed.

## Transfer Through A CLI

Transfer requires a recorded resumable session. Aider, Cline, and Goose are one-turn adapters here: use them for delegation or relay steps, not ownership transfer. Interactive resume commands use native defaults and may differ from recorded access: inspect them before reopening; do not claim they preserve the sandbox.

The first turn proves the receiver read the brief and can work. Ask it to restate the goal and its next step in that turn. After it does, record `--outcome transferred`, give the user the `interactive_resume` command, and stop changing the task.
