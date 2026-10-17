---
name: rumo-debug
description: Use when investigating a software defect, failing test, flaky behavior, remote-environment anomaly, or unexplained UI or API behavior. Reproduce, localize, and prove the cause with an evidence chain across source, runtime, data, middleware, deployment, and client boundaries; stay read-only unless the request also asks for the fix. Do not use for planned database writes or for reviewing a diff.
---

# Rumo Debug

Turn a symptom into the shortest causal chain that evidence can prove.

## Authority

Investigation is read-only by default. Fixing code, changing data, restarting services, or editing configuration needs the original request to include the fix or a separate go-ahead. Database writes always go through `rumo-database-change-safety`.

## 1. Pin Down The Facts

Record the affected repository or service, environment and its purpose, exact time window (convert "this morning" into timestamps before querying logs), client or actor version, expected and actual result, reproduction steps, identifiers, and error text. Use `rumo-project-profile` when project-specific paths, hosts, or schemas are needed; otherwise discover from the repository and ask only for facts that cannot be established safely.

## 2. Reproduce

Reproduce at the cheapest layer that shows the symptom. If it does not reproduce, compare environment, data, version, and timing before guessing. For flaky behavior, find the condition that makes it deterministic.

## 3. Localize

1. Find the visible entry point: route, screen, command, scheduled job, message, import, or protocol action.
2. Trace callers and contracts through every layer that applies, and identify which process and artifact actually own the behavior in that environment.
3. State one falsifiable hypothesis, then collect the narrowest logs, read-only queries, cache or queue state, and deployment facts that confirm or refute it. Read [references/workflows.md](references/workflows.md) to pick the route.
4. For cross-process behavior, prove both the producer and the consumer side; when the fix changes what one side sends or expects, plan it with `rumo-interface`. For deployment or identity problems, compare process arguments (with secrets masked), ports, configuration, and active artifact versions before blaming application logic.

## 4. Minimize

Strip the reproduction to the smallest input and state that still fails, and find the earliest wrong state transition.

## 5. Fix (Only When Requested)

Write a failing regression test first, make the smallest fix, and verify with `rumo-test` and `rumo-verify`. Keep the fix inside the proven cause.

## Remote Environments

Read [references/remote-investigation.md](references/remote-investigation.md) before touching a remote host. By default access only localhost or an environment identified as development or test, and ask when the purpose is unclear. Production access needs the user's explicit go-ahead and stays read-only unless the user authorizes the exact change. Never print passwords, tokens, keys, or full sensitive payloads. `scripts/remote_probe.py --host <host> --root <remote-root> --log-dir <log-dir>` prints a generic read-only probe.

## Stop Conditions

- Choose whether to continue, change strategy, or pause from new evidence, narrowing causes, reproducibility, remaining risk, and cost; there is no default hypothesis or fix-attempt limit. Respect the user's explicit budget and stopping instructions.
- Continue while evidence advances the investigation inside the authorized scope. When failures repeat without information gain, stop that strategy and recheck the environment, version, running artifact, data, and owning component. Never repeat the same patch without new evidence.
- If a different safe strategy can obtain the missing evidence, pursue it. Otherwise report the ruled-out hypotheses, remaining uncertainty, and the exact input, access, or external condition needed.
- Ask before a fix needs a product decision or changes beyond the proven cause and existing authorization. Do not re-request approval for work already covered.

## Report

Use [references/report-template.md](references/report-template.md). State the symptom, confirmed or likely cause, causal chain, evidence with file, line, or timestamp, fix boundary, unresolved conflicts, and evidence not obtained. Keep source reasoning separate from runtime proof.

A causal chain that can be checked:

```text
Symptom: exported CSV for order 1042 shows 0.00 total since the 10-14 release.
Trigger: orders created with a coupon go through CouponPricing (pricing/coupon.py:57).
Earliest wrong state: line 63 rounds the discount before currency conversion, so total_minor becomes 0.
Evidence (source): pricing/coupon.py:57-63; test_coupon_rounding reproduces it.
Evidence (runtime): export log 2026-10-15T09:12:44Z order=1042 total_minor=0; 10-13 build shows 1999.
Not obtained: whether pre-release coupon orders were re-exported.
```

Not a causal chain: "There's a missing null check in export, that's probably it." It names no trigger, no wrong state, and no evidence, so nobody can confirm or refute it.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "This code looks wrong, that must be it." | A smell is not a cause until the trigger-to-symptom route is shown. |
| "I'll patch it while I'm here." | Fixing without authorization changes what the user asked for. |
| "The request returned 200, so the backend is fine." | Transport success says nothing about the durable or visible effect. |
| "Logs are noisy, I'll scan everything." | Narrow the window and identifiers first; broad scans hide the signal. |
| "Can't reproduce, so I'll guess." | Compare environment, data, version, and timing; report what is missing. |
