---
name: rumo-verify
description: Use before claiming work is done, marking it ready, committing for handoff, or pushing, and when asked to verify a change; establish the exact committed and dirty change scope, run the smallest sufficient checks, and report only commands actually run. Also use when adding, changing, reviewing, or diagnosing a repository-owned CI check, static verifier, generated-file check, pre-commit rule, or aggregate test entry point. Never commits, pushes, deploys, or changes remote systems; do not use for test planning before implementation.
---

# Rumo Verify

No claim of "done", "fixed", or "passing" without fresh evidence from this state of the code.

## Modes

| Mode | Use when |
| --- | --- |
| Verify a change (default) | Before handoff, commit, push, or when asked to check work |
| Build or review a gate | Adding, changing, or reviewing a CI job, verifier, threshold, hook, or aggregate check; read [references/gates.md](references/gates.md) first. A review stays read-only. |

## Verify A Change

### 1. Fix The Scope

1. Read repository and module instructions, CI configuration, build files, and nearby tests.
2. Record repository root, branch, HEAD, upstream, worktree status, and the base being compared against.
3. Look at committed changes from the merge base, and at staged, unstaged, and untracked files separately.
4. Decide which paths belong to this task. Never stage, stash, reset, clean, or rewrite unrelated work to make verification easier.
5. When a file mixes task and unrelated edits, verify the intended staged content; if tools cannot read the index, check it out into a temporary worktree without touching the user's index or files.
6. Handle each repository in a multi-repository change separately.

### 2. Choose Checks

Pick the narrowest command that would fail for the regression, then widen only for a real dependency or shared contract. Read [references/surfaces.md](references/surfaces.md) for the minimum evidence per changed surface. Use `rumo-test` when the behavioral claims themselves are unclear.

### 3. Run And Read

Run the checks and read the output; an exit code alone is not the whole story. Do not rerun a passing check unless a later edit invalidated it.

### 4. Report

List the verified scope, each command with its actual result, skipped or unavailable checks and why, evidence boundaries (source versus artifact versus deployment versus field), and whether later edits invalidated earlier results.

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
