# Adapters

Read when the user names a CLI that has no adapter, when an adapter is unverified, or when `check` reports a missing flag or version drift.

An adapter is a JSON file that tells `agent_run.py` how to drive one CLI: how to start a non-interactive turn, how to pass the prompt, which flags enforce each access level, where the reply and session ID appear in the output, and how to continue the session. The script holds no CLI-specific code.

## Where Adapters Live

- Bundled: `adapters/` in this skill. `agent_run.py list` shows them.
- User: `$RUMO_AGENT_ADAPTERS_DIR`, else `<runs-dir>/adapters/` (by default `~/.rumo-agent-runs/adapters/`). A user adapter with a bundled adapter's name replaces it, and `list`, `check`, and `show` say so.

## Bundled Adapters

| CLI | Status | Access levels |
|---|---|---|
| codex | flags checked on 0.162.0 | read-only, workspace-write |
| claude | flags checked on 2.1.305 | read-only, workspace-write |
| pi | flags checked on 1.3.0 | read-only, workspace-write (no shell) |
| qwen | flags checked and one read-only turn run on 0.25.2 | read-only, workspace-write |
| grok | flags checked on 1.0.41; the live run stopped at sign-in | read-only |
| cursor (`cursor-agent`) | unverified, from the CLI reference | read-only |
| gemini | disabled: headless Plan Mode can switch to unrestricted implementation | declared read-only is insufficient |
| opencode | disabled: managed config can override inline permissions | effective read-only permissions are unconfirmed |
| copilot | unverified, from GitHub CLI and SDK event references | read-only, native-write (file tools; no shell) |
| aider | unverified, from options and chat-mode references | read-only, native-write (code edits; caller runs checks) |
| cline | unverified, from CLI and Plan/Act references | read-only, native-write (Act defaults auto-approve) |
| goose | unverified, from command, permission, and output references | read-only (chat only), native-write (approve mode) |

"Flags checked" means each flag appeared in that version's `--help`; it does not prove the whole turn works. Each adapter's `notes` field records what was and was not exercised; `show` prints it.

Gemini's [Plan Mode reference](https://geminicli.com/docs/cli/plan-mode/#non-interactive-execution) says headless mode approves `exit_plan_mode` and then enables unrestricted implementation. OpenCode's [config precedence](https://opencode.ai/docs/config/#precedence-order) lets managed settings override inline permissions. Both declarations are retained for inspection with `disabled_reason`; establishing restrictive effective permissions is required before enabling either.

A disabled adapter cannot start or resume a turn, including a run saved before it was disabled. `list` reports `usable: false` and the reason; `show` prints its declaration with the same status. `check`, `start`, and `resume` refuse with exit 2 before invoking the CLI. Existing runs still support status, notes, and cancellation when process ownership is confirmed. Resume checks the saved declaration and the current selected adapter for a disable decision; other current settings never replace the saved snapshot. The existing user-over-bundled selection rule still applies.

## Not Included

- Amp: its plugins can rewrite its permission settings; a reliable read-only adapter has not been established.
- Kimi CLI: the documented stdin `--print` mode implicitly enables AFK approval and automatically handles plan-mode switches. The [print-mode reference](https://github.com/MoonshotAI/kimi-cli/blob/main/docs/en/customization/print-mode.md) and the [other published command reference](https://moonshotai.github.io/kimi-code/en/reference/kimi-command) describe different interfaces. No confirmed read-only stdin/file invocation is bundled.
- Crush: the [non-interactive implementation](https://github.com/charmbracelet/crush/blob/main/internal/app/app.go) automatically approves the session. No invocation with a reliable read-only boundary has been confirmed.
- agy and Devin: their input or output needs code beyond the declarative adapter contract.

These exclusions concern the adapter requirements, not whether each CLI can develop software.

## Fields

| Field | Meaning |
|---|---|
| `name`, `executable` | adapter name used on the command line; program looked up on PATH |
| `verified` | `{"version", "on", "live_run"}` when checked against an installed CLI, else `null` |
| `disabled_reason` | optional nonempty string; prevents checks and execution, while leaving the declaration available to inspect. Omit to enable; null, blank, and non-string values are invalid |
| `help` | list of `{"args", "flags"}`: literal subcommands followed by `--help`; `check` requires exit 0 and every flag in the output |
| `prompt` | `stdin`, or `file` with `{prompt_file}` in the templates. A prompt on the command line is refused |
| `access` | `read-only` (required), optional `workspace-write` and `native-write`, each a list of flags. A missing level is refused |
| `resume_access` | optional per-level flags for resume, when the CLI spells them differently there |
| `model` | flags for a named model, using `{model}`; omitted when the user named none |
| `start`, `resume` | argv templates. `{access}` and `{model}` expand to their flag lists; `{session}`, `{cwd}`, `{prompt_file}` are substituted in place |
| `env` | literal environment variables for the child, such as an inline permission config |
| `access_env` | optional mapping from an offered access level to environment variables; overrides `env` for that level, in the child only |
| `session` | `{"source": "preassign"}` (the script passes a new UUID as `{session}`), `{"source": "event", "match", "field"}`, or `{"source": "none"}` (one turn only) |
| `output` | `{"format": "text"}` (all of stdout is the reply) or `{"format": "jsonl", "final", "error"}` |
| `progress` | optional list of rules that `watch` renders as `[label] text` lines; display only |
| `interactive` | args a person uses to reopen the session, with `{session}` |
| `interactive_start` | optional argv for `open`: starts the CLI interactively with `{access}`, `{session}`, optional `{model}` and `{run_name}`, and `{opening}`, the script's one-line pointer to the brief. Requires a preassigned session; `{opening}` and `{run_name}` are refused anywhere else |
| `notes` | what was and was not exercised, and any known limit |

A `final` or `error` rule is `{"match": {...}, "field": ..., "pick", "transform"}`. `match` maps dotted paths to required values; an empty `match` takes every event. `field` is a dotted path or a list of candidates; the first nonempty text result wins. `pick` is `last` (default) or `join` for replies streamed in pieces. `transform: "text_parts"` joins the `text` parts of a content array. `error` may be a list of rules.

A `progress` rule uses the same `match` and `field`, plus a nonempty `label` and an optional `label_field` whose value is appended to the label, such as a tool name. Match only assistant output and tool events, never the user's messages, which carry the brief. `watch` uses the current adapter's rules for a run whose snapshot has none.

## Write One

1. Run the installed CLI's `--help` and its non-interactive subcommand's help, or use official documentation when it is unavailable. Record exact source links in `notes`; do not install the CLI without authorization. Find a non-interactive mode, prompt input through stdin or a file, output format, a read-only setting, and session resume if available.
2. No confirmed read-only setting: stop. The CLI cannot be used through this skill.
3. Add `workspace-write` only for a documented working-directory restriction. Otherwise use `native-write` for a documented development mode and disclose the lack of directory isolation, automatic approval defaults, and available tools. Unverified adapters may offer documented write modes, but keep `verified: null` until the local version and help have been checked. Never use a flag that skips approvals or the sandbox. `FORBIDDEN` in the script lists refused strings; checks also reject common short approval aliases, explicit sandbox disabling, and enabled allow-all/auto-approve settings. Use unambiguous long flags instead of `-f` or `-y`.
4. Without a JSON output, use `"output": {"format": "text"}`. Without session IDs, use `"session": {"source": "none"}`; the run is then one turn only.
5. Save it in the user adapter directory with `verified: null`, run `agent_run.py check <name>`, then `show <name> --access <requested-level>`, and show the user the command and adapter before the first launch. Missing CLI means check is unavailable, not passed.
6. After a run, compare the real output with the `final`, `error`, and `session` rules and fix them before relying on the adapter.

## Permission And Output Boundaries

`native-write` permits development through native CLI controls, not an added filesystem sandbox. Use a separate worktree for each parallel writer; the brief still limits authorized files and operations. Approval that the headless turn cannot collect is a blocker, not permission to change modes.

Goose uses `access_env` to select `GOOSE_MODE=chat` for read-only and `approve` for native-write. Chat mode cannot inspect files through tools: include required source or diffs in the brief. Cline Act defaults to automatic tool approval; show that fact before launching. Copilot and Aider develop files without shell execution here; the caller runs requested checks. Aider disables automatic commits, lint, tests, shell suggestions, gitignore changes, and update checks; its histories stay beside the recorded prompt.

Aider, Cline, and Goose are one-turn adapters. No reliable session ID is extracted for Cline; Goose explicitly uses `--no-session`. Do not transfer ownership to these single-turn routes. Copilot preassigns its session UUID and uses it again to resume.

Adapters are trusted executable declarations, not a sandbox for hostile files or CLI startup hooks. Validation checks declared fields, placeholders, help commands, and forbidden strings, including JSON-escaped settings; it cannot prove arbitrary executable behavior or all configuration precedence. Windows batch launchers refuse shell syntax in arguments; use a direct executable for those paths or values. Do not weaken this check or place a prompt in argv.

Output sample provenance is in [the fixture README](../scripts/fixtures/README.md). Constructed samples and mock tests establish parser/rendering behavior only. `verified.live_run` describes historical CLI evidence, not end-to-end acceptance of a modified adapter.

## Version Drift

`check` reports `version_drift` when the installed version differs from `verified.version`. The run still proceeds, because a missing flag already fails `check`; say in your report that the adapter was verified on another version. When a turn fails or the reply is missing after an update, inspect the raw `events.jsonl` before blaming the agent.
