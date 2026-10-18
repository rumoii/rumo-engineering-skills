# Remote Investigation

Use this reference only after the target environment and its purpose are known.

## First Pass

Confirm host, account, and clock before searching business logs:

```bash
hostname
id -un
date -Is
```

If the owning service is known, query its state and bounded logs directly. Choose process, listener, or container queries only when the symptom requires them. `scripts/remote_probe.py` prints process and listener listings for initial discovery when service ownership is unknown; it is not a required first step.

Identify services by process name, systemd unit, or `/proc/<pid>/cgroup`, not by full command lines, which often carry passwords, tokens, or connection strings. When one process must be pinned down further, inspect only that PID and mask secrets before anything reaches chat or an evidence file. `scripts/remote_probe.py --keyword` caps matches and masks common secret shapes such as `password=`, bearer tokens, and credentials in URLs; the masking is best effort, so still review its output before saving it.

Resolve install roots, service names, log directories, database access, and middleware commands from the selected project profile or from verified runtime configuration. Do not reuse example paths as facts.

## Evidence Order

1. Confirm clock and host/account identity; identify the relevant service and artifact version as needed.
2. Narrow the time window and identifiers.
3. Inspect the owning service log and its immediate caller or consumer.
4. Query only the required rows or metadata with read-only statements.
5. Inspect cache, queue, object store, or client state only when the causal route reaches it.
6. Capture sender and receiver evidence for cross-environment behavior.

Prefer literal searches until a regular expression is necessary and reviewed. Redact credentials and sensitive payload fields from saved evidence. A successful transport request does not prove business completion; verify the durable or client-visible side effect.

## Stop Conditions

Stop and report the boundary when the environment purpose is unclear, credentials are unavailable, a query would require writes, the time window is too broad to avoid unrelated data, or project configuration cannot identify the owning service safely.
