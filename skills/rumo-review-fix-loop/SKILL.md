---
name: rumo-review-fix-loop
description: Use only when the user explicitly asks for an iterative review + fix quality gate, such as reviewing uncommitted changes, a branch diff, a commit, or a custom target, then fixing every actionable P0/P1/P2 or blocking finding, verifying the fix, and repeating review cycles until there are no blocking findings or a clear stop condition is reached. Do not trigger for ordinary one-pass code reviews.
---

# Review Fix Loop

## Purpose

Use this skill to make review-driven cleanup systematic after a bug fix or feature change. The goal is not to hide reviewer output; the goal is to keep running a narrow review -> fix -> verify loop until no actionable P0/P1/P2 or blocking finding remains.

Treat this as a quality gate before commit or push. Do not commit or push unless the user explicitly asks.

Apply the review priorities, evidence standard, and finding severities from [`rumo-code-review`](../rumo-code-review/SKILL.md) on every pass. This skill adds the fix-and-repeat control loop; it does not define a second review policy. Use `rumo-code-review` alone for ordinary one-pass or read-only reviews.

## Inputs

Determine the review target before starting:

- `uncommittedChanges`: review the current worktree changes. Use this by default after a bug fix when the user says "review uncommitted changes", asks to review uncommitted work, or does not name a target.
- `baseBranch`: review the diff against a branch when the user names a base branch or asks for branch-diff review.
- `commit`: review a specific commit when the user gives a SHA.
- `custom`: use the user's free-form review instruction when they ask for a custom review, name a risk area, or ask for a scoped review.

Capture the current repo, branch, and worktree status at the start. If the user points to multiple repos, run the loop separately per repo and report each repo's result.

## Review Backends

Prefer the most direct available review surface. Every backend feeds the same loop, severity filter, and stop conditions below.

1. When `codex app-server` is available, first read [references/codex-app-server.md](references/codex-app-server.md), then run `scripts/app_server_review.py`. It gives an independent review thread with a machine-readable exit code.
2. Otherwise, or after two app-server attempts fail without a valid `exitedReviewMode.review`, use the current client's built-in review command when one exists, such as `/review` in Codex or `/code-review` in Claude Code, and choose the target above.
3. If another App Server client is in use, call `review/start` for the target. Stream `item/*` events and read the final `exitedReviewMode.review` text as the authoritative review output.
4. If no review surface is directly callable, perform a code-review pass in the current session by following `rumo-code-review` for the selected target.

## Loop

Run this cycle:

1. Start a review for the selected target.
2. Extract findings into three buckets:
   - `must_fix`: P0, P1, P2, correctness bugs, data loss/security issues, build/test breakage, or reviewer findings that explicitly say they block acceptance.
   - `consider`: P3, style, maintainability suggestions, unclear risk, and non-blocking improvements.
   - `not_actionable`: false positives, findings already fixed by the current diff, or items missing enough evidence to act.
3. Fix only `must_fix` items by default. Keep edits surgical and inside the reviewed change boundary.
4. Add or update the smallest meaningful regression test when the finding is about behavior, data contract, permission, concurrency, or error handling.
5. Run targeted verification for the touched code. Prefer exact tests, compile/lint, and `git diff --check`; broaden only when the blast radius requires it.
6. Re-run the same review target.
7. Stop only when the latest review has no `must_fix` items, or when a stop condition below applies.

Do not claim success from "no P0/P1/P2" if the reviewer output contains a clearly blocking finding without a severity label. Conversely, do not keep looping on non-blocking P3/style comments unless the user explicitly asks for full polish.

## Stop Conditions

Stop and report instead of looping forever when any condition is true:

- The latest review has no `must_fix` items. Report remaining `consider` items separately if they exist.
- The same finding repeats after two fix attempts and the evidence is ambiguous. Report the attempted fixes and ask for direction.
- Fixing a finding requires a product decision, API contract change, data migration, remote deployment, credentials, or changing unrelated user work.
- Verification fails for a reason outside the current change and cannot be narrowed safely.
- The loop reaches 5 review cycles in one repo. Report the remaining findings and recommend the next action.

## Safety Rules

- Preserve user changes. Do not revert unrelated work.
- Re-read files before editing if the worktree changed during the loop.
- Keep each fix tied to a concrete reviewer finding; avoid broad refactors.
- If a review spans multiple repos, state exactly which repo was reviewed, fixed, and verified.
- If a reviewer finding is a false positive, record why with file/line or test evidence, then continue the loop.
- If the user asked for "until /review has no output", interpret that as "until no blocking review findings remain"; many review systems still emit summaries, informational text, or non-blocking suggestions.

## Reporting

Final response should include:

- Review target and number of review cycles.
- Fixed P0/P1/P2/blocking findings.
- Verification commands and results.
- Remaining non-blocking findings, if any.
- Explicit blocker if the loop stopped before a clean blocking-review pass.
