# Remote Investigation

Use this reference only after the target environment and its purpose are known.

## First Pass

Collect read-only identity and ownership facts before searching business logs:

```bash
hostname
date -Is
uname -a
ps -eo pid,ppid,user,%cpu,%mem,rss,etime,comm,unit --sort=-rss | head -40
ss -lntp 2>/dev/null | head -120
docker ps --format '{{.ID}} {{.Image}} {{.Names}} {{.Status}}' 2>/dev/null || true
```

Identify services by process name, systemd unit, or `/proc/<pid>/cgroup`, not by full command lines, which often carry passwords, tokens, or connection strings. When one process must be pinned down further, inspect only that PID and mask secrets before anything reaches chat or an evidence file. `scripts/remote_probe.py --keyword` caps matches and masks common secret shapes such as `password=`, bearer tokens, and credentials in URLs; the masking is best effort, so still review its output before saving it.

Resolve install roots, service names, log directories, database access, and middleware commands from the selected project profile or from verified runtime configuration. Do not reuse example paths as facts.

## Evidence Order

1. Confirm clock, host identity, owning service of each process, listeners, and artifact version.
2. Narrow the time window and identifiers.
3. Inspect the owning service log and its immediate caller or consumer.
4. Query only the required rows or metadata with read-only statements.
5. Inspect cache, queue, object store, or client state only when the causal route reaches it.
6. Capture sender and receiver evidence for cross-environment behavior.

Prefer literal searches until a regular expression is necessary and reviewed. Redact credentials and sensitive payload fields from saved evidence. A successful transport request does not prove business completion; verify the durable or client-visible side effect.

## Stop Conditions

Stop and report the boundary when the environment purpose is unclear, credentials are unavailable, a query would require writes, the time window is too broad to avoid unrelated data, or project configuration cannot identify the owning service safely.
