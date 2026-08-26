---
name: rumo-review-fix-loop
description: Use only when the user explicitly asks for an iterative review + fix quality gate, such as reviewing uncommitted changes, a branch diff, a commit, or a custom target, then fixing every actionable P0/P1/P2 or blocking finding, verifying the fix, and repeating review cycles until there are no blocking findings or a clear stop condition is reached. Do not trigger for ordinary one-pass code reviews.
---

# Review Fix Loop

## Purpose

Use this skill to make review-driven cleanup systematic after a bug fix or feature change. The goal is not to hide reviewer output; the goal is to keep running a narrow review -> fix -> verify loop until no actionable P0/P1/P2 or blocking finding remains.

Treat this as a quality gate before commit or push. Do not commit or push unless the user explicitly asks.

Apply the review priorities, evidence standard, and finding severities from [`rumo-code-review`](../rumo-code-review/SKILL.md) on every pass. This skill adds the fix-and-repeat control loop; it does not define a second review policy. Use `rumo-code-review` alone for ordinary one-pass or read-only reviews.

## Script

Use `scripts/app_server_review.py` to launch `codex app-server --stdio`, create a temporary review thread, call `review/start`, wait for `exitedReviewMode.review`, and print the final review text. The script exits `2` when the review text appears to contain P0/P1/P2 or another blocking/critical finding, `0` when no blocking finding is detected, and `1` on protocol/runtime failure. If the app-server turn completes without `exitedReviewMode.review`, the script returns JSON with `error: "missingExitedReviewMode"` and diagnostics instead of a review conclusion.

The script defaults to `--sandbox workspace-write` because real review usually needs `git diff` and some shell wrappers create temporary files. Use `--sandbox read-only` only when you know the local Codex/Git wrapper works under read-only sandboxing.

Review passes can be long-running; 20-45 minutes is normal for large diffs or busy app-server sessions. The script's default overall `--timeout` is 2700 seconds, default active `thread/read` `--poll-interval` is 30 seconds, default no-progress `--idle-timeout` is 600 seconds, and default `--min-wait-before-idle` is 300 seconds. When invoking it through a shell/tool wrapper, set that wrapper's own timeout to at least the script timeout, or omit the wrapper timeout entirely if the environment permits. Do not treat a 10-15 minute wait as a review failure when heartbeat output shows target review item progress or polling state changes; if both the notification stream and active `thread/read` polling show no target review turn state change after the minimum wait window and for the idle timeout, let the script exit with diagnostics and use the retry/fallback rule below.

During `initialize`, the script asks app-server to opt out of unrelated status notifications such as MCP startup, model verification, account updates, and app-list changes. Use `--no-opt-out-noise` only when diagnosing raw notification traffic. Even when those notifications are present, they must not refresh the review idle timer.

The script intentionally does not create ephemeral threads by default because `thread/read(includeTurns=true)` cannot recover items from ephemeral app-server threads. Use `--ephemeral` only when you explicitly prefer no persisted temporary review thread and accept losing active polling recovery.

By default, the script archives the temporary non-ephemeral review thread before exit so active polling does not pollute the user's visible thread list. Use `--keep-review-thread` when you need to inspect the review thread after the run.

During long waits, the script prints progress heartbeat messages to stderr by default, including the review thread id, turn id, elapsed time, remaining timeout, notification count, item count, and last observed event/item type. Intermediate findings are not shown by default. The actual review result is only known after the final `exitedReviewMode.review` text arrives; before that, heartbeat output proves the app-server session is still active but does not prove whether blocking findings exist. Use `--progress-interval <seconds>` to change heartbeat frequency, or `--quiet-progress` only when a caller requires stderr silence.

Use `--show-intermediate` only when you need to inspect visible in-progress review messages while waiting. It prints non-reasoning, non-tool visible text items to stderr, capped by `--intermediate-max-chars`, but those snippets are provisional. Do not extract `must_fix`/`consider` buckets, edit code, or stop the loop from intermediate snippets; wait for the final `exitedReviewMode.review`.

Do not keep retrying app-server review indefinitely. If `app_server_review.py` exits `1` because it timed out or returned `missingExitedReviewMode`, clean up only the review app-server child processes you started and retry once with a long enough wrapper timeout. If the second attempt still has no valid `exitedReviewMode.review`, switch to the current-thread code-review fallback for that cycle, explicitly report that the app-server review backend failed, and continue the same fix -> verify loop from the fallback findings.

Resolve the script from the installed skill directory, not from a product repo. If the skill path is unclear, locate it from the loaded `SKILL.md` path.

Unix shell:

```bash
python3 <skill-dir>/scripts/app_server_review.py --cwd "$PWD" --target uncommittedChanges --json
```

Windows PowerShell:

```powershell
py -3 <skill-dir>\scripts\app_server_review.py --cwd "$PWD" --target uncommittedChanges --json
```

Target examples:

```bash
python3 <skill-dir>/scripts/app_server_review.py --cwd "$PWD" --target baseBranch --branch origin/main --json
python3 <skill-dir>/scripts/app_server_review.py --cwd "$PWD" --target commit --sha 1234567deadbeef --json
python3 <skill-dir>/scripts/app_server_review.py --cwd "$PWD" --target custom --instructions "Review this fix for auth bypass regressions" --json
```

Do not let the script apply fixes. The script is the review sensor; the current Codex instance remains responsible for code edits, tests, and the loop decision.

Script regression tests:

```bash
python3 <skill-dir>/scripts/test_app_server_review.py
```

## Inputs

Determine the review target before starting:

- `uncommittedChanges`: review the current worktree changes. Use this by default after a bug fix when the user says "review uncommitted changes", asks to review uncommitted work, or does not name a target.
- `baseBranch`: review the diff against a branch when the user names a base branch or asks for branch-diff review.
- `commit`: review a specific commit when the user gives a SHA.
- `custom`: use the user's free-form review instruction when they ask for a custom review, name a risk area, or ask for a scoped review.

Capture the current repo, branch, and worktree status at the start. If the user points to multiple repos, run the loop separately per repo and report each repo's result.

## Review Backends

Prefer the most direct available review surface:

1. Run `scripts/app_server_review.py` when `codex app-server` is available. This is the preferred automation path.
2. If running inside Codex with `/review` available and the script cannot run, or two app-server attempts fail without a valid `exitedReviewMode.review`, use the built-in review flow and choose the target above.
3. If using another App Server client, call `review/start` for the target. Stream `item/*` events and read the final `exitedReviewMode.review` text as the authoritative review output.
4. If no review surface is directly callable, ask Codex to perform a code-review pass in the current thread, but preserve the same severity filter and loop rules below.

App Server request shape:

```json
{
  "method": "review/start",
  "id": 40,
  "params": {
    "threadId": "<thread-id>",
    "delivery": "inline",
    "target": { "type": "uncommittedChanges" }
  }
}
```

For detached review, use `"delivery": "detached"` and follow `reviewThreadId` in the response. A detached review is useful when the main thread is already busy or when the client wants a separate review transcript.

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
