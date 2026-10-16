---
name: rumo-linux-inspect
description: Use when explicitly asked for a read-only Linux inspection, either a hardware inventory that saves raw evidence and a concise Chinese device-configuration TXT, or a memory and performance inspection for high memory, OOM, garbage-collection, slow-log, process, or port symptoms. Never change the target, install packages, or operate services.
disable-model-invocation: true
---

# Rumo Linux Inspect

Collect Linux facts without changing the target. Pick the mode and read its reference in full before connecting.

| Mode | Produces | Reference |
| --- | --- | --- |
| Hardware inventory | A raw evidence TXT and a concise Simplified Chinese device-configuration TXT, returned verbatim in chat | [references/hardware-inventory.md](references/hardware-inventory.md) and [collection-commands.md](references/collection-commands.md) |
| Memory inspection | A local evidence directory and a risk classification | [references/memory-inspection.md](references/memory-inspection.md) |

## Shared Boundaries

- Confirm the target host, port, user, environment purpose, and SSH host fingerprint before connecting. Access only targets the user identified and authorized; production stays read-only.
- Run read-only commands only: no package changes, configuration edits, remote files, password changes, service operations, reboots, or deletions.
- Passwords and `sudo` prompts appear only in a visible interactive terminal. Never place credentials in arguments, scripts, environment variables, profiles, reports, or chat.
- Use `rumo-project-profile` for private install roots, log directories, and service patterns; there are no built-in hosts or paths.
- Treat a missing command, denied permission, empty field, and unsupported device as distinct evidence gaps. Do not infer facts the output does not prove.
- Report what was collected, where it was saved, and what the collected layer does not prove.
