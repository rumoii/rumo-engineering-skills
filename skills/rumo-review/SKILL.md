---
name: rumo-review
description: Use for a read-only code review of uncommitted changes, a branch diff, or a commit, or a named-scope audit of existing issues; for a multi-model review panel or a second opinion from another model through agent CLIs ("多模型评审"); for an explicitly requested review-fix-repeat loop until no blocking findings remain; for an explicitly requested simplification audit of removable complexity; or for addressing review feedback from someone else. Report correctness, security, lifecycle, compatibility, operations, and test risks with file-and-line evidence. Do not use to run pre-handoff checks; use rumo-verify instead.
---

# Rumo Review

Lead with actionable findings, not a tour of the diff.

## Modes

| Mode | Trigger | Edits code |
| --- | --- | --- |
| Review (default) | Any review request | No |
| Loop | The user explicitly asks to review, fix, and repeat; read [references/loop.md](references/loop.md) | Yes, must-fix items only |
| Panel | The user asks for several models or a second opinion from another one, or you propose it for a high-risk change; read [references/panel.md](references/panel.md) | No |
| Simplify | The user explicitly asks for simplification or removable-complexity findings; read [references/simplify.md](references/simplify.md) | No |
| Respond | The user hands over review comments from a person or a tool and asks to address them | Yes, accepted comments only |

Review (default), Panel, and Simplify modes never edit code; only Loop and Respond do, and only on an explicit request.

Nothing is sent to another model or CLI until the user agrees, as [references/panel.md](references/panel.md) describes.

## Settle The Target

1. Read the repository guidance and the nearest module instructions.
2. Pick one target: uncommitted changes, a diff against a confirmed base, a commit, or a named-scope audit of the current implementation. Use the user's stated target; ask only if it is materially ambiguous.
3. Record repository, branch, HEAD, worktree status, and, for branch comparisons, the base and merge base.
4. Inspect committed, staged, unstaged, and untracked changes separately; a three-dot diff hides dirty layers.
5. Review each repository on its own.

Do not guess the base from branch names. Use the request, repository guidance, upstream tracking, or merge-request metadata, and ask only when none of them settles it.

## What To Look For

Read enough surrounding code and current consumers to judge, in this order:

1. **Correctness:** wrong conditions, missing states, broken error paths, stale data, behavior that contradicts the request.
2. **Security and data safety:** authorization, ownership and tenant isolation, secret exposure, injection, unsafe file or process handling, destructive migrations, missing rollback.
3. **Lifecycle and concurrency:** races, duplicate work, cancellation, retry, timeout, resource ownership, disposal order, partial failure.
4. **Cross-layer contracts:** request and response shapes, DTOs, schema and queries, messages and cache state, generated or deployed artifacts.
5. **Compatibility and operations:** supported branches, existing data, upgrades, configuration precedence, platforms, topology, observability.
6. **Test quality:** tests must exercise the affected production route; a mock-only assertion, compile, HTTP 200, or coverage number is not proof.

When the target is a CI job, verifier, threshold, or other gate, also apply the gate rules in `rumo-verify` (still read-only).

## Evidence Standard

- Trace both sides of every changed interface and every production consumer in scope.
- Keep source behavior, built artifacts, deployed state, and field acceptance apart.
- Treat tests and comments as evidence to weigh, not authority over production behavior.
- For a diff, report only issues this change introduces or materially exposes; old debt is out of scope. For a named-scope audit, report existing actionable issues inside that scope, even on a clean HEAD. Do not expand either target into unrelated debt.
- When a caller-supplied value drives a state change (money moved, stock reserved, quota spent, a record read or written for someone), name the stored value that must bound it: balance, amount paid, stock, quota, owner, or tenant. If nothing in scope compares against it, report a finding that states the assumed invariant and which component might already enforce it. A guarantee you cannot see elsewhere is an open question attached to the finding, not a reason to withhold it.
- Check that a suggested fix direction is feasible, but do not edit code in review mode.

## Respond To Feedback

1. Check each comment against the code: is the problem real, and is it inside the reviewed change? Read [references/judging-findings.md](references/judging-findings.md) before dismissing or accepting comments from a person, bot, or another model.
2. Sort each one: fix; decline with evidence (file, line, test, or documentation); needs clarification; or out of scope, recorded but not fixed now. Order the fixes with the must-fix and consider buckets in [references/loop.md](references/loop.md).
3. Ask about unclear comments first; hold the edits that depend on them and continue with the rest.
4. Fix in severity order, add a regression test for behavior findings, and verify with `rumo-verify`.
5. Reply per comment with what changed or why it did not. Skip blanket thanks and agreement.
6. Do not post replies, resolve threads, or request another review on the hosting platform unless the user asks.

## Report

Findings first, by severity:

- **P0:** immediate security, data-loss, or system-wide failure risk.
- **P1:** required behavior broken or a likely production failure.
- **P2:** material correctness, compatibility, lifecycle, or test gap.
- **P3:** non-blocking clarity or maintainability; include only when useful.

Each finding names the repository, file and line, the consequence, the triggering condition, and the evidence. Then open questions and assumptions, then a short scope and verification note. If nothing actionable turned up, say so and name the runtime, platform, deployment, or field boundaries that remain untested.

A finding that can be acted on:

```text
P1 services/profile.py:54 - updating the email commits to the database but leaves the cached profile in place.
Trigger: a user changes their email and a password reset is requested within the 10-minute cache TTL.
Consequence: the reset link goes to the old address.
Evidence: line 54 commits the row; nothing deletes profile:{id}, which get_profile (line 21) reads before the database.
```

Not a finding: "Consider more error handling; the code could be cleaner; tests look fine." It names no location, trigger, or consequence, so nobody can verify or fix it.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "The tests pass, so it's fine." | Check whether the tests touch the changed route at all. |
| "I'll mention this old problem too." | Findings outside the change bury the ones that matter. |
| "Probably main is the base." | A wrong base reviews the wrong diff; confirm it. |
| "Quick fix while reviewing." | Review mode is read-only unless the user asked for the loop or for responding to feedback. |
