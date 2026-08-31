---
name: rumo-coding-guidelines
description: Use when writing, fixing, reviewing, or refactoring code in Rumo product repositories or shared skill repositories. This is a general baseline coding constraint that may be used alongside more specific Rumo skills; confirm real paths and success criteria, keep work requested and necessary, preserve proven consequences, and avoid overengineering, unrelated edits, and unverified conclusions.
license: MIT
---

# Rumo Coding Guidelines

Use this skill first when writing code in Rumo product repositories or shared skill repositories. Every change should be traceable to the user request, the real code path, and concrete verification evidence.

## Core Principles

### Confirm Real Paths First

- Read the current repo's `AGENTS.md`, `CLAUDE.md`, and nearby directory guidance before editing.
- Locate the real entry points, call chain, configuration, and existing patterns before designing changes.
- Do not guess implementation locations from screenshots, memory, error summaries, or file names.
- If the user names multiple repositories, state which repositories were inspected, modified, and verified.

### Make The Smallest Correct Change

- Implement only what the current task requires; do not add future-facing features.
- Do not add generic abstractions, plugin layers, configuration switches, or fallback frameworks for one-off use.
- Do not opportunistically reorder, reformat, rename, or refactor adjacent code.
- Match the existing code style even when you would personally choose a different style.
- Clean up only unused imports, variables, functions, or files created by this change.

### Apply The Stop Ladder

Before adding work that the user did not name, ask:

1. Did the user request it?
2. Is it necessary to complete the requested result?
3. What reachable code, data, deployment state, user decision, or acceptance proves that need?
4. Would omitting it fail the current task?

If the answer remains no, do not implement it. Report it only when it is useful to the user.
The smallest correct result is the goal, not the smallest diff: preserve callers, fixtures,
tests, accessibility, security, current-data migration, supported-platform compatibility, and
deployment work when reachable evidence requires them.

Do not turn internal risk controls into user-facing caveats. Add a disclaimer, limitation,
privacy notice, or safety warning only when the user requested it, a reachable decision requires
it, or omission would make the result false, unsafe, or non-compliant. Keep internal process out
of deliverables unless the user requests methodology or it materially changes how the result is
interpreted or used.

### Respect Task Authorization

- Treat `review`, `answer`, and `monitor` requests as read-only until the user explicitly authorizes a change.
- In `change` work, implement only the requested work and its necessary consequences.
- Do not add hashing, dependencies, migrations, compatibility layers, abstractions, or subagents merely because they might help later.
- When authorization, scope, or task mode changes, re-evaluate the active request instead of carrying forward assumptions from the previous mode.
- When the requested result has enough evidence, stop repeating searches, tests, or reviews.

### Prefer Current Requirements Over Obsolete Compatibility

- Do not preserve backward compatibility for obsolete paths unless the user explicitly requires it as part of the current contract.
- Remove obsolete routes, fields, branches, adapters, fallback paths, migrations, and compatibility layers instead of adding indirection that keeps dead behavior alive.
- Do not invent a deprecation period, dual-write path, feature flag, shim, or fallback to avoid making the required current-state change.
- Before deleting a path, verify its current callers, owners, generated outputs, and deployment references. Preserve only behavior that the current requirements or an identified supported consumer still require.

### Grow In Working Layers

- Start with the smallest version that works end to end through the real entry point, then add the next capability on top of that working baseline.
- Keep each layer independently understandable and verifiable. Do not trade a working product for unfinished orchestration, speculative abstractions, or a broad framework.
- Keep components modular and separate concerns at their ownership boundaries; do not hide unrelated responsibilities behind a convenient shared helper.

### Reuse Proven Dependencies And Patterns

- Check the dependencies already present in the project, their documentation, and their types before writing replacement code or adding a package.
- Prefer an established, maintained library when it materially reduces implementation and maintenance complexity or improves reliability.
- Do not assume an existing library lacks a capability without verifying its documented API and supported types.
- Study established products and repository patterns before designing a new mechanism. Adopt a proven convention when it satisfies the current requirements; document the concrete reason when departing from it.

### Make Durable Architectural Decisions

- Choose designs that remain correct and maintainable as the system grows. Do not accept a stopgap whose stated purpose is to be replaced later.
- Keep the simplest implementation that fully meets the current requirements; reject speculative configuration, indirection, extension points, and compatibility machinery.
- When a material choice affects module boundaries, interfaces, persistence, deployment, security, lifecycle, or rollback, record the rationale with `rumo-engineering-decision` rather than leaving it in chat or comments.

### Handle Assumptions Explicitly

- When multiple interpretations exist, state the tradeoff; clarify high-risk ambiguity before editing.
- Do not present guesses as facts or unverified symptoms as root causes.
- When unrelated issues appear, record or report them instead of expanding the change scope.
- Prefer the simpler sufficient solution and state why it is enough.

### Close With Verification

- Turn the task into a verifiable goal such as reproduce -> fix -> run targeted verification.
- Prefer targeted tests, builds, lint, script self-tests, `git diff --check`, or real API/page verification.
- If verification fails, state the failed command, the reason, and the remaining risk.
- If verification is impossible, say that explicitly; do not replace evidence with "should work."

## Working Method

For complex tasks, provide a short plan where each step has a verification method:

```text
1. Locate the real path and proven options -> verify: entry points, callers, dependencies, documentation, types, and established patterns inspected
2. Define the smallest current-state end-to-end layer -> verify: obsolete paths identified for removal and the first working slice is explicit
3. Implement in modular layers -> verify: each added layer works on top of the previous one and owns one concern
4. Run targeted verification -> verify: focused behavior, relevant integration, build/lint, and diff checks pass
```

Simple tasks can be executed directly, but changes must still stay surgical.

## Pre-Commit Self-Check

- Does every changed file belong to this task?
- Does every change map to the user request or a verification failure?
- Did the change remove obsolete paths instead of retaining compatibility, fallbacks, or migrations without a current requirement?
- Did the change introduce an unrequested abstraction, configuration option, or generic capability?
- Were existing dependencies, documentation, types, and established product patterns checked before adding custom code or a package?
- Does the implementation work end to end at its smallest layer, with later capabilities added modularly?
- Is any architectural choice a declared stopgap intended to be replaced later?
- Did it edit code that is not understood or unrelated?
- Does the final response distinguish changed, verified, and unverified or blocked work?

## Related Skills

- Use [`rumo-code-review`](../rumo-code-review/SKILL.md) for an evidence-backed one-pass review.
- Use [`rumo-change-verification`](../rumo-change-verification/SKILL.md) to match checks to an exact outgoing or requested diff.
- Use [`rumo-database-change-safety`](../rumo-database-change-safety/SKILL.md) for write-capable schema migrations, data repairs, cleanup, resets, and rollback.
- Use [`rumo-offline-delivery-audit`](../rumo-offline-delivery-audit/SKILL.md) for installable offline artifacts, dependency closure, provenance, and field-acceptance limits.
- Use [`rumo-prose-standard`](../rumo-prose-standard/SKILL.md) for comments, diagnostics, UI strings, and repository documentation.
- Use [`rumo-engineering-decision`](../rumo-engineering-decision/SKILL.md) only when a material cross-module obligation needs durable rationale.

## Provenance

The Stop Ladder and requested-or-necessary scope discipline adapt the
MIT-licensed `stop-that-shit` project. Preserve its [upstream license](LICENSE.stop-that-shit)
when maintaining or redistributing this adaptation.
