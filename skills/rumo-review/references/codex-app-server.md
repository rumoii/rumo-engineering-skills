# Codex App Server

This file applies only to environments where `codex app-server` is available. Otherwise, use the client-neutral [review backends](loop.md#review-backends) in the loop reference.

## Codex App Server Script

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

Do not let the script apply fixes. The script is the review sensor; the calling agent remains responsible for code edits, tests, and the loop decision.

Script regression tests:

```bash
python3 <skill-dir>/scripts/test_app_server_review.py
```

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
