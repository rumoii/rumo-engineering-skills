# Native Subagents

Read only when a relay or transfer in this skill runs a step through the current client's own subagent feature, or transfers to a background session the client provides. Ordinary use of the client's subagents, whether the client starts them itself or the user asks for them directly, does not need this skill. Each section applies to one client only. Tool names and flags change between versions: confirm them in the client's tool list or `--help` before use. A client with no subagent feature delegates through [external-cli.md](external-cli.md) instead.

## What Native Delegation Gives You

A native subagent starts with a fresh context and reports back into this conversation. It usually shares the parent's permission settings and provider, so nothing new leaves the machine beyond what this client already sends. It still spends quota: tell the user before starting more than one, or a long one.

Most native subagents end when the parent conversation ends. Use them to delegate, not to transfer.

## Claude Code

- **Delegate**: the Agent tool starts a subagent with its own context. Choose a read-only agent type for exploration or review; pass the brief as the prompt. Background runs notify on completion, so do not poll.
- **Transfer**: `claude --bg` starts a background session that outlives this one and prints its ID. `claude agents` lists them, `claude logs <id>` shows recent output, `claude attach <id>` opens one, and `claude stop <id>` stops it. Pass the brief on stdin or as the prompt, and start it with a permission mode no wider than the current session's.

## Codex

Codex may expose a subagent or multi-agent tool depending on version and configured features. Use it only when it appears in the current tool list; do not enable features on the user's behalf. Without it, delegate through `codex exec` in [external-cli.md](external-cli.md).

## pi

The `@gotgenes/pi-subagents` extension, when installed, adds `subagent` to start an agent (foreground or background), `get_subagent_result` to collect its result, and `steer_subagent` to send a correction while it runs. Its agents run inside the parent pi process and are released with it, so they serve delegation only. Without the extension, delegate through `pi -p` in [external-cli.md](external-cli.md).

## Accepting The Result

A subagent's summary is a claim. Read the files it changed, rerun the check named in the brief, and report what you verified yourself.
