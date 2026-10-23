# Native Subagents

Read before assessing native subagent availability for a collaboration route, running a relay step through the current client's subagents, or transferring to a client-provided background session. Ordinary use of the client's subagents, whether the client starts them itself or the user asks for them directly, does not need this skill. Each client section below applies only to that client.

## Establish Current Capabilities

Do not infer availability from the CLI name, version, or an installed package alone. Check child permissions separately; parent read-only access does not prove child read-only access.

Inspect the current tool list first, then extension loading and registration, then invocation flags and permissions; consult local help or implementation only for remaining gaps. A missing exposed tool does not by itself prove the client lacks an implementation. Report one of: available, installed but not loaded, disabled for this invocation, confirmed absent, or unconfirmed. State the evidence and its limits; do not read credentials to discover capabilities.

Check starting, background execution, result collection, completion notification, steering, and lifetime separately. Starting a subagent does not prove background survival or completion notification. An installed package or a CLI version is not proof that its tools are loaded or allowed in this session.

## Permissions And Lifetime

Verify the child's tools, permissions, model, and provider separately from the parent's. Do not assume that a child inherits a read-only policy or sends data to the same provider. Apply the launch authorization and content limits in SKILL.md. Native work still spends quota: tell the user before starting more than one subagent, or a long one.

When child read-only access cannot be established, use an already authorized read-only route or report the blocker. Do not enable shell tools, extensions, or wider approvals to make a route available.

Distinguish turn completion, session switching, and parent process exit. Confirm whether background work survives each event and whether completion can trigger a new parent turn. When cross-turn survival and notification are confirmed, finish the current turn and let the client notify you; do not block on result collection merely to keep the turn open. Otherwise report the missing capability rather than promise an automatic return. Delegate to a child tied to the parent process; transfer only to a session whose independent lifetime has been established.

## Claude Code

- **Delegate**: when the Agent tool is exposed and allowed, it starts a subagent with its own context. Check the agent type's tools and permission policy before read-only exploration or review; pass the brief as the prompt. Use completion notifications when the current runtime supports them, without polling.
- **Transfer**: `claude --bg` starts a background session that outlives this one and prints its ID. `claude agents` lists them, `claude logs <id>` shows recent output, `claude attach <id>` opens one, and `claude stop <id>` stops it. Pass the brief on stdin or as the prompt, and start it with a permission mode no wider than the current session's.

## Codex

Codex may expose a subagent or multi-agent tool depending on version and configured features. Use it only when it appears in the current tool list and is allowed; do not enable features on the user's behalf. If native delegation is unavailable, use an authorized `codex exec` route in [external-cli.md](external-cli.md) or report the blocker.

## pi

When loaded and allowed in the current session, the `@gotgenes/pi-subagents` extension provides `subagent` to start an agent (foreground or background), `get_subagent_result` to collect its result, and `steer_subagent` to send a correction while it runs. Check registration, invocation flags, and the selected child's configuration; installation alone proves none of those. Its agents run inside the parent pi process and are released with it, so they serve delegation only. A normal parent turn ending is distinct from that process exiting. Verify notification behavior and the child's effective tools rather than infer them from the parent's `--tools` list.

The bundled external pi adapter disables extension discovery for its invocation; see [external-cli.md](external-cli.md). Report that invocation's limitation instead of saying pi has no subagent feature. Do not change those restrictions to load an installed package. Use an already authorized route or report the blocker when the requested capability is unavailable.

## Classification Examples

These are expected judgments for static rule checks, not results from model evaluations.

| Evidence | Judgment |
|---|---|
| Extension registered and allowed; start tool exposed | Available for starting; check other capabilities separately. |
| Package installed; tool missing; loading not checked | Unconfirmed; check loading, do not declare absence. |
| Package installed; runtime confirms it was not loaded | Installed but not loaded. |
| Invocation disables the extension or denies the tool | Disabled for this invocation. |
| Current runtime confirms no built-in or extension implementation | Confirmed absent. |
| Parent allows only reads; child tool policy is unknown | Child read-only access is unconfirmed; use a verified route or stop. |
| Parent turn ended; process still alive | Check cross-turn survival and notification; do not infer process exit. |

## Accepting The Result

A subagent's summary is a claim. Read the files it changed, rerun the check named in the brief, and report what you verified yourself.
