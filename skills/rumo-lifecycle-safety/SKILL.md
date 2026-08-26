---
name: rumo-lifecycle-safety
description: Use when implementing, fixing, or reviewing asynchronous or long-lived Rumo behavior involving background tasks, thread pools, scheduled jobs, Kafka consumers, terminal sessions, subprocesses, retries, cancellation, timeouts, shutdown, or resource cleanup. Establish explicit ownership and state transitions, make retry and disposal safe, and verify failure and restart paths instead of only the successful call.
---

# Rumo Lifecycle Safety

Make every long-lived operation answer who owns it, when it becomes visible, how it stops, and what remains after failure. Apply `rumo-coding-guidelines` before changing code and use `rumo-code-review` for a review-only request.

## Establish Authority

Trace the production path from creation through publication, use, cancellation, completion, and disposal. Identify:

- the authoritative state and every derived cache, UI status, Redis key, database row, queue message, or in-memory registry;
- the component that creates the work and the component responsible for stopping and releasing it;
- the stable operation or task identity used across retries, reconnects, and process restarts;
- the thread, executor, scheduler, event loop, process, or remote service on which each transition occurs;
- the observable state that means ready, completed, failed, cancelled, timed out, or abandoned.

Do not infer readiness from service presence, object construction, a submitted future, an HTTP success status, or a process identifier alone. Use the event or state owned by the mechanism being awaited.

## Define The State Machine

Write down the allowed transitions before editing. Keep terminal outcomes distinct when callers or operators need different recovery:

```text
created -> starting -> running -> succeeded
                         |      -> failed
                         |      -> cancelled
                         |      -> timed_out
                         `------> interrupted
```

Reject or explicitly define duplicate starts, late completion after cancellation, restart from a terminal state, and events received before registration. Publish handles and correlation identifiers before work can emit events; remove them only after no producer can still address them.

Use one authority for each fact. Derived UI or cache state must converge from authoritative events or persisted state rather than competing writes from several callbacks.

## Make Failure And Retry Safe

- Define whether an operation is idempotent, deduplicated, resumable, compensating, or deliberately at-most-once.
- Bound retries by attempt count or deadline, classify retryable failures, and preserve the original operation identity.
- Separate a caller timeout from cancellation of underlying work. State whether timed-out work keeps running and how its eventual result is handled.
- Preserve the primary failure when cleanup also fails; record cleanup failure without replacing the causal error.
- Never swallow an exception merely to make a worker, migration, deployment, or terminal task appear successful.
- Avoid fixed sleeps as synchronization. Wait on an owned condition with a deadline and actionable timeout diagnostics.

For Kafka, Redis, RustFS, terminal tasks, Runner, or PSModel flows, trace durable side effects and replay behavior. A retry that repeats external writes without an idempotency rule is unsafe even when the local future completes once.

## Own Resources Explicitly

List every resource acquired by the operation: listeners, subscriptions, timers, executors, sockets, streams, files, locks, temporary directories, processes, database sessions, browser contexts, and remote task handles.

Release in dependency order. Stop new work first, detach producers, cancel or drain owned tasks, wait within a bounded deadline, then close the resources those tasks use. Make disposal safe after partial startup and safe when invoked more than once.

Do not close shared resources from a child operation. Do not leave background work retaining request, session, tenant, or UI objects after their owner is gone.

## Verify Lifecycle Paths

Cover the production mechanism, not only direct method calls:

- normal start, observable readiness, completion, and cleanup;
- failure before and after publication;
- cancellation before start and while running;
- timeout with both cooperative and uncooperative work;
- duplicate request, retry, reconnect, replay, and late event;
- partial initialization and repeated disposal;
- service shutdown, process restart, and persisted-work recovery;
- concurrent operations with distinct tenant, product, session, or task identity.

Assert eventual state, released resources, durable side effects, and absence of orphan work. Use deterministic barriers, latches, fake clocks, or owned events instead of timing-dependent sleeps.

Use `rumo-test-evidence` to choose the required evidence layers and `rumo-change-verification` before claiming the change ready. Record a material lifecycle policy with `rumo-engineering-decision`.

## Report

State the authoritative state, owner, transition table, retry and idempotency rule, timeout and cancellation semantics, disposal order, exact failure paths exercised, and any restart or field behavior still unverified.
