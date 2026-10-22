---
name: rumo-verify
description: Use before claiming work is done, marking it ready, committing for handoff, or pushing, and when asked to verify a change; establish the exact change scope, run the smallest sufficient checks, and report only commands actually run. Also use to add, review, or diagnose a repository CI check, static verifier, pre-commit rule, or aggregate test entry point, and to create or maintain a project's verification recipe for launching, driving, and proving its real features. Never commits, pushes, or deploys; not for test planning (rumo-test) or semantic review (rumo-review). For failing checks on an open pull request, use rumo-git-commit instead.
---

# Rumo Verify

No claim of "done", "fixed", or "passing" without fresh evidence from this state of the code.

## Modes

| Mode | Use when |
| --- | --- |
| Verify a change (default) | Before handoff, commit, push, or when asked to check work |
| Build or review a gate | Adding, changing, or reviewing a CI job, verifier, threshold, hook, or aggregate check; read [references/gates.md](references/gates.md) first. A review stays read-only. |
| Project verification recipe | Creating, checking, or repairing a project's recipe for launching the application, driving its features as a user would, and keeping the proof; read [references/recipe.md](references/recipe.md) first. |

## Verify A Change

### 1. Fix The Scope

1. Read repository and module instructions, CI configuration, build files, and nearby tests.
2. Record repository root, branch, HEAD, upstream, worktree status, and the base being compared against.
3. Look at committed changes from the merge base, and at staged, unstaged, and untracked files separately.
4. Decide which paths belong to this task. Never stage, stash, reset, clean, or rewrite unrelated work to make verification easier.
5. When a file mixes task and unrelated edits, verify the intended staged content; if tools cannot read the index, check it out into a temporary worktree without touching the user's index or files.
6. Handle each repository in a multi-repository change separately.
7. When the change touches user-visible behavior, look for the project's verification recipe: a `verify-<app>` skill in the client's project or user skill directory, or a recipe path named in `AGENTS.md`. Use its launch, health check, and drive steps for the affected features, under the stop conditions below. When the recipe no longer matches the application, report the drift instead of following stale steps.

### 2. Choose Checks

Pick the narrowest command that would fail for the regression, then widen only for a real dependency or shared contract. Match the evidence to the risk: a file copy or documentation change is confirmed with a file list and a diff, not a custom verification harness, unless the user asks for one or `rumo-test` rates the change high. Read [references/surfaces.md](references/surfaces.md) for the minimum evidence per changed surface. Use `rumo-test` when the behavioral claims themselves are unclear.

### 3. Run And Read

Run the checks and read the output; an exit code alone is not the whole story. Do not rerun a passing check unless a later edit invalidated it.

### 4. Report

List the verified scope, each command with its actual result, skipped or unavailable checks and why, evidence boundaries (source versus artifact versus deployment versus field), and whether later edits invalidated earlier results. When the same commands ran in more than one directory or copy, say where each result comes from.

"Not run" lists checks and evidence boundaries only. Controlled actions you did not take, such as commits, pushes, or publication, are not verification gaps; mention them in one line, and only when the user could assume they happened.

```text
Scope: branch fix/report-local-date vs main, 2 commits, no uncommitted files.
- pytest tests/reports/test_daily.py: 7 passed
- ruff check services/reports.py: no issues
- git diff --check: clean
Not run: report export against the test environment (needs a deployment the user has not approved).
```

A report that says "all tests pass, should be good to merge" names no scope, no commands, and no gaps; it is not evidence.

## Stop Conditions

- A required check cannot run because credentials, software, platform, or access is missing: report the missing boundary; never mark it passed.
- Getting evidence would require deploying, restarting services, changing data, or pushing: stop and ask; those are separate authorizations.
- Verification fails for a reason outside this change and cannot be isolated: report it with the failing output.

## Related

- Passing commands do not replace a semantic review; use `rumo-review` for that.
- Running a migration, repair, cleanup, or rollback against an existing database goes through `rumo-database-change-safety` first.
- Compatibility and rollout questions go to `rumo-interface`; retry, cancellation, timeout, and shutdown behavior to `rumo-lifecycle-safety`.
- Commit, tag, or push afterwards with `rumo-git-commit` when the user asks.

## Red Flags

- "Should pass", "probably fine", or "looks good" in the final message.
- A full-suite run presented as proof for a change nobody traced.
- A summary that mentions checks without commands or results.
- Satisfaction expressed before the checks finished.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "I ran it earlier." | Earlier is not this state of the code. |
| "Focused tests passed, so everything passes." | Say exactly what passed; do not extrapolate. |
| "It builds, so it works." | A build proves compilation, not behavior. |
| "CI will catch it." | CI has not run; report what you actually ran. |
| "The check is unavailable here, I'll skip it quietly." | An unavailable check is a reported gap, not a pass. |
