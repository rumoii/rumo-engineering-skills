# Remote Memory Inspection

Collect read-only Linux evidence and classify risk without changing services or configuration. The target must be explicitly identified as development or test, or separately authorized for production read-only access.

Run this workflow manually or invoke it from an external scheduler. It does not create or manage cron jobs, operating-system tasks, or agent automations.

Use `rumo-project-profile` for install roots, log directories, service patterns, runtime type, and private credentials. This workflow has no default host, product, path, or password. Declare a JVM in `runtime.json` as a product with `"runtime": "jvm"` and a remote `"pid_file"`, then pass `--profile <profile-dir>`; PID files and `jcmd` are probed read-only, never created or installed.

## Evidence

- host identity, time, kernel, uptime, memory and swap;
- top processes by RSS with process name and owning systemd unit or cgroup, never full command lines;
- process status, threads, file descriptors, and container usage;
- optional JVM diagnostics when the profile declares a JVM runtime and tools are available;
- kernel OOM evidence, and for `--log-dir` a per-file count of memory and error patterns rather than log text;
- listeners and middleware processes relevant to the suspected route.

Run `scripts/remote_memory_inspection.py --host <host> --user <user> [--root <path>] [--log-dir <path>] [--profile <profile-dir>] --dry-run` before live collection. The live command uses SSH keys by default and saves a local evidence directory. It never restarts services or writes remotely. Missing thread, descriptor, JVM, or log evidence is marked `not collected` or unreadable, never zero or inferred healthy. When a count points at a specific problem, read the relevant lines in a targeted follow-up and mask secrets before saving them.

Classify observed pressure as process heap, native memory, thread or descriptor growth, middleware/container pressure, kernel OOM, repeated application errors, or insufficient evidence. State what the collected layer does not prove.
