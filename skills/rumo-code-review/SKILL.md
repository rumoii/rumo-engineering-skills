---
name: rumo-code-review
description: Use for an ordinary one-pass review of uncommitted changes, a branch diff, a commit, or a user-defined scope in software or shared-skill repositories. Report correctness, security, lifecycle, compatibility, deployment, and test risks with file-and-line evidence; stay read-only unless the user separately asks for fixes. Do not use for the explicit iterative review-and-fix loop.
---

# Rumo Code Review

Review the requested change as a read-only engineering assessment. Lead with actionable findings, not a walkthrough of the diff.

## Establish The Review Target

1. Read the repository guidance and the nearest module instructions.
2. Identify one target: uncommitted changes, a diff against a verified base branch, a commit, or the user's custom scope.
3. Record the repository, branch, HEAD, worktree status, resolved base, and merge base when a branch comparison is involved.
4. Inspect committed, staged, unstaged, and untracked paths separately. A three-dot diff does not describe dirty layers.
5. For multiple repositories, review and report each repository independently. Do not infer that the same file name means the same implementation.

Do not guess a base branch from naming alone. Use the user request, repository guidance, upstream metadata, or current merge-request metadata. Stop and request the base only when no unique source can establish it.

## Review Priorities

Read enough surrounding code and current consumers to evaluate these areas in order:

1. **Correctness and required behavior:** wrong conditions, missing states, invalid assumptions, broken error paths, stale data, or behavior that contradicts the request.
2. **Security and data safety:** authorization, ownership scope, tenant or product isolation, secret exposure, injection, unsafe file/process handling, destructive migration, and rollback gaps.
3. **Lifecycle and concurrency:** publication races, duplicate work, cancellation, retry, timeout, resource ownership, disposal ordering, background-task settlement, and partial failure.
4. **Cross-layer contracts:** Vue request and response handling, Java DTO/controller/service behavior, database schema and queries, Redis/Kafka/RustFS state, terminal protocols, and generated or deployed artifacts.
5. **Compatibility and operations:** supported release branches, existing data, upgrade paths, configuration precedence, platform behavior, deployment topology, and observability.
6. **Verification quality:** tests must exercise the affected production route. A mock-only assertion, source compile, HTTP 200, or green coverage number does not prove the assembled or deployed behavior.

Apply `rumo-coding-guidelines` as the baseline. Use `rumo-bug-root-cause` when the task is primarily diagnosis of an observed runtime symptom. Use `rumo-review-fix-loop` only when the user explicitly requests repeated review and repair.

Apply `rumo-lifecycle-safety` to lifecycle-heavy changes, `rumo-interface-evolution` to producer-consumer changes, `rumo-test-evidence` when the evidence claim is unclear, and `rumo-repository-gates` when reviewing CI or static validation machinery.

## Evidence Standard

- Trace both sides of every changed interface and every current production consumer in scope.
- Distinguish source behavior, built artifact behavior, deployed environment state, and field acceptance.
- Treat tests and comments as evidence to evaluate, not authority that overrides production behavior.
- Report only issues the current change introduces or materially exposes. Do not turn unrelated technical debt into review findings.
- Confirm that a proposed fix direction is feasible, but do not edit code during a review-only request.

## Reporting

List findings first, ordered by severity:

- **P0:** immediate security, data-loss, or system-wide failure risk.
- **P1:** required behavior is broken or a likely production failure exists.
- **P2:** material correctness, compatibility, lifecycle, or verification gap.
- **P3:** non-blocking maintainability or clarity issue; include only when useful.

Each finding must name the repository, file and line, observable consequence, triggering condition, and supporting evidence. Then list open questions or assumptions, followed by a brief scope and verification summary.

If no actionable issue is found, say so directly and identify any untested runtime, platform, deployment, or field boundary that remains.
