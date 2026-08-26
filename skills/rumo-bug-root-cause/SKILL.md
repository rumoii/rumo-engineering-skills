---
name: rumo-bug-root-cause
description: Use when investigating software defects, test failures, remote-environment anomalies, or unexplained UI and API behavior. Build an evidence-backed root-cause chain across source, runtime, data, middleware, deployment, and client boundaries.
---

# Bug Root Cause

Turn a symptom into the shortest verifiable causal chain. Diagnose read-only by default; implementing a fix, changing data, restarting services, or editing configuration requires separate authorization.

## Establish Facts

Capture the affected repository or service, environment purpose, exact time window, actor or client version, expected result, actual result, reproduction state, identifiers, screenshots, requests, and relevant error text. Convert relative dates to exact timestamps before querying logs.

Use [`rumo-project-profile`](../rumo-project-profile/SKILL.md) when project-specific paths, services, hosts, schemas, or credentials are required. If no profile matches, discover from the current repository and ask only for facts that cannot be established safely.

## Trace The Ownership Chain

1. Locate the visible entrypoint: route, screen, command, scheduled job, message, import, or protocol action.
2. Trace the caller and contract through frontend, API, controller, service, persistence, queue, worker, remote peer, and client as applicable.
3. Identify which process and artifact actually own the behavior in the named environment.
4. Form a falsifiable runtime hypothesis before collecting broad evidence.
5. Collect the narrowest logs, read-only queries, cache or queue state, process facts, and deployment metadata that can prove or disprove it.
6. Correlate every conclusion to file-and-line evidence, timestamped runtime evidence, a stored record, or a captured request.

For cross-process behavior, prove both producer and consumer routes. For deployment or identity problems, compare process arguments, addresses, ports, configuration, durable identity, and active artifact versions before blaming application logic.

## Remote Investigation

- Access only localhost or an environment explicitly identified as development or test. Ask before accessing an environment whose purpose is unclear.
- Treat production as read-only unless the user authorizes the exact mutation.
- Start with identity, process, port, artifact, log, container, and clock checks.
- Prefer bounded `tail`, `rg` or `grep`, catalog queries, read-only `SELECT`, queue descriptions, and recent container logs.
- Never print passwords, tokens, private keys, or complete sensitive payloads.
- Run `scripts/remote_probe.py --host <host> --root <remote-root> --log-dir <log-dir>` to print a generic read-only SSH probe.

## Report

State the symptom, confirmed cause, causal chain, affected boundary, exact evidence, likely fix boundary, unresolved conflicts, and evidence not obtained. Distinguish source reasoning from runtime, deployment, browser, terminal, and field proof.

Use [`rumo-database-change-safety`](../rumo-database-change-safety/SKILL.md) before any database write and [`rumo-interface-evolution`](../rumo-interface-evolution/SKILL.md) for producer-consumer compatibility changes.
