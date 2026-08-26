---
name: rumo-remote-memory-inspection
description: Use for scheduled or manual read-only inspection of remote Linux hosts with high memory, OOM, garbage-collection, slow-log, process, port, or performance symptoms. Use explicit targets and optional project profiles instead of built-in environments.
---

# Remote Memory Inspection

Collect read-only Linux evidence and classify risk without changing services or configuration. The target must be explicitly identified as development or test, or separately authorized for production read-only access.

Use [`rumo-project-profile`](../rumo-project-profile/SKILL.md) for install roots, log directories, service patterns, runtime type, and private credentials. The skill itself has no default host, product, path, or password.

## Evidence

- host identity, time, kernel, uptime, memory and swap;
- top processes by RSS and command line;
- process status, threads, file descriptors, and container usage;
- optional JVM diagnostics when the profile declares a JVM runtime and tools are available;
- kernel OOM evidence and bounded recent logs;
- listeners and middleware processes relevant to the suspected route.

Run `scripts/remote_memory_inspection.py --host <host> --user <user> [--root <path>] [--log-dir <path>] --dry-run` before live collection. The live command uses SSH keys by default and saves a local evidence directory. It never restarts services or writes remotely.

Classify observed pressure as process heap, native memory, thread or descriptor growth, middleware/container pressure, kernel OOM, repeated application errors, or insufficient evidence. State what the collected layer does not prove.
