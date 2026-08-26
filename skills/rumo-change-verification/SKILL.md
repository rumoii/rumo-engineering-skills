---
name: rumo-change-verification
description: Use before pushing, marking work ready, claiming checks pass, or when explicitly asked to verify a change. Establish the exact committed and dirty change scope, preserve unrelated work, select the smallest sufficient tests and builds for the affected source and artifact paths, and report only commands actually run. This skill never commits, tags, pushes, deploys, or mutates remote systems.
---

# Rumo Change Verification

Match verification evidence to the exact outgoing or requested change. Do not use a full repository suite as a substitute for impact analysis.

## Establish Scope

1. Read repository and module instructions, CI configuration, build files, and nearby tests.
2. Record the repository root, branch, HEAD, upstream, worktree status, and the verified target base when relevant.
3. Inspect committed paths from the merge base to HEAD and inspect staged, unstaged, and untracked paths separately.
4. Identify which paths belong to the user's task. Preserve unrelated changes and never stage, stash, reset, clean, or rewrite them merely to simplify verification.
5. For a multi-repository change, build a separate scope and evidence set for each repository.

When a file mixes task and unrelated edits, verify the intended staged snapshot rather than treating the whole working file as the candidate. Inspect `git diff --cached` and, when build or test tools cannot consume the index directly, materialize the staged tree in a temporary detached worktree without changing the user's index or working tree.

## Select Evidence

Choose the narrowest command that would fail for the affected regression, then broaden only for a real dependency or shared contract.

| Changed surface | Minimum evidence to consider |
| --- | --- |
| Vue component or page logic | focused tests or lint, affected frontend build, and browser verification for visible behavior |
| Shared frontend component or runtime config | all known consumers, generated config validation, and the affected application build |
| Java service implementation | target module compile and focused tests; include callers when an interface changed |
| DTO, API, serialization, or permission contract | both producer and consumer paths, failure cases, and compatibility with existing data |
| SQL, schema, or migration | query or migration validation, existing-data behavior, transaction/rollback path, and affected service tests |
| Kafka, Redis, task, or terminal lifecycle | producer/consumer route, retry or duplicate handling, persisted side effects, and convergence after failure |
| Packaging or deployment script | built artifact contents, selected profile, plan or dry run, target paths, backup/rollback, and post-action verification |
| Shared skill | frontmatter validation, referenced-file existence, helper-script tests, cross-platform command review, and `git diff --check` |
| Documentation or generated artifact | source-owner check, render/build when applicable, forbidden-path scan, and visual inspection |

Source checks do not prove built or deployed artifacts. Package checks do not prove a real Windows, terminal, Runner, PSModel, or customer environment unless that environment was actually exercised.

## Avoid False Evidence

- Do not rerun a passing command unless a later edit invalidated what it covered.
- Do not claim repository-wide success from focused checks.
- Do not claim an external or field boundary from fake, unit, source-only, or package-only evidence.
- Do not silently skip a required check because credentials, software, platform, or environment access is unavailable; report the missing boundary.
- Do not deploy, restart services, alter data, or push merely to obtain verification unless the user separately authorizes that action.

## Integrations

- Use `rumo-code-review` for semantic review; verification commands cannot replace it.
- Use `rumo-test-evidence` to turn behavioral claims into the required evidence layers before selecting commands.
- Use `rumo-lifecycle-safety` for background work, retry, cancellation, timeout, shutdown, or cleanup behavior.
- Use `rumo-interface-evolution` for API, message, configuration, or persisted-format compatibility and rollout matrices.
- Use `rumo-repository-gates` when the change adds or modifies a verifier, aggregate command, quality threshold, or CI job.
- Use `rumo-database-change-safety` before executing a migration, repair, cleanup, reset, or rollback against an existing database.
- Use `rumo-review-fix-loop` only for an explicitly requested iterative review gate.
- Use `rumo-git-commit` after verification when the user asks to commit, tag, land, or push.
- Use `rumo-browser-evidence` when the required output is a persistent screenshot or interaction artifact.

## Report

Report the verified scope, exact commands and results, evidence boundaries, skipped or unavailable checks, and whether later edits invalidated any earlier result. Never summarize unrun checks as passed.
