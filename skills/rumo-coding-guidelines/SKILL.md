---
name: rumo-coding-guidelines
description: Use when writing, fixing, reviewing, or refactoring code in software repositories or shared skill repositories. This is a general baseline coding constraint that may be used alongside more specific Rumo skills; confirm real code paths and success criteria first, keep changes minimal, and avoid overengineering, unrelated edits, and unverified conclusions.
license: MIT
---

# Rumo Coding Guidelines

Use this skill first when writing code in software repositories or shared skill repositories. Every change should be traceable to the user request, the real code path, and concrete verification evidence.

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
1. Locate the real code path -> verify: entry points, call chain, and existing tests found
2. Make the smallest change -> verify: diff only touches task-related files
3. Run targeted verification -> verify: targeted tests/build/lint/diff-check pass
```

Simple tasks can be executed directly, but changes must still stay surgical.

## Pre-Commit Self-Check

- Does every changed file belong to this task?
- Does every change map to the user request or a verification failure?
- Did the change introduce an unrequested abstraction, configuration option, or generic capability?
- Did it edit code that is not understood or unrelated?
- Does the final response distinguish changed, verified, and unverified or blocked work?

## Related Skills

- Use [`rumo-code-review`](../rumo-code-review/SKILL.md) for an evidence-backed one-pass review.
- Use [`rumo-change-verification`](../rumo-change-verification/SKILL.md) to match checks to an exact outgoing or requested diff.
- Use [`rumo-database-change-safety`](../rumo-database-change-safety/SKILL.md) for write-capable schema migrations, data repairs, cleanup, resets, and rollback.
- Use [`rumo-offline-delivery-audit`](../rumo-offline-delivery-audit/SKILL.md) for installable offline artifacts, dependency closure, provenance, and field-acceptance limits.
- Use [`rumo-prose-standard`](../rumo-prose-standard/SKILL.md) for comments, diagnostics, UI strings, and repository documentation.
- Use [`rumo-engineering-decision`](../rumo-engineering-decision/SKILL.md) only when a material cross-module obligation needs durable rationale.
