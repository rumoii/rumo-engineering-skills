# Following Pull Request Checks

Read when the user asks you to watch, follow, or fix the CI checks of an open pull request.

- A request to watch only reports results: no reruns, edits, commits, or pushes.
- A request to fix covers reruns, local edits, and local verification. Commit and push the fixes only when the user also asked for that, or explicitly authorized pushes to this branch earlier in the task; otherwise stop after local verification and report what is ready to push.
- None of these authorizes merging, marking the pull request ready, or approving it.

## Confirm The Target

Record the repository, pull request number, head branch, head commit, and whether the branch is yours alone or shared. Re-read the head commit before each push; when someone else pushed meanwhile, stop and report instead of overwriting.

## Wait Without Polling

Each status check through the model costs a call, so wait with one blocking command instead of a loop. These steps use the GitHub CLI (`gh`) as the example; use the hosting platform's equivalent elsewhere.

1. In a client that runs background commands and notifies when they finish (client-specific: for example a background shell task), run a blocking watch such as `gh pr checks <number> --watch` in the background and act when it exits.
2. Otherwise, run the same blocking command once in the foreground with a timeout longer than the expected CI time. A tool timeout ends the wait, not the checks; report the state and ask whether to keep waiting.
3. When neither works, or no platform CLI is available, report the checks page and stop.

## When A Check Fails

1. Read the failed job's log (`gh run view <run-id> --log-failed`) before changing anything.
2. Classify the failure:
   - **Caused by the change:** the failure points at code or tests the pull request touched. Fix it at the cause.
   - **Suspected flake:** the failing test is unrelated to the change and has a history of intermittent failure. Rerun that job once; a second failure makes it a real failure.
   - **Infrastructure:** runner, network, quota, or a third-party service. Report it; do not change code for it.
   - **Pre-existing:** the same check fails on the target branch. Report it and do not fix it inside this pull request unless the user asks.
3. Fix, and run the relevant checks locally through `rumo-verify`. When committing and pushing are authorized, follow SKILL.md for both and wait again; otherwise stop here and report the verified local fix.

Never edit an assertion only to make it pass, skip hooks, mark a required check optional, or disable a test to get green. Rewriting history or force-pushing a shared branch requires a preview and explicit confirmation, as in SKILL.md.

Review comments that arrive while you wait follow `rumo-review` in Respond mode.

## Stop

Stop and report when:

- every required check passes;
- a fix is verified locally and pushing it is not authorized;
- a fix needs a product decision, a contract change, credentials, or work outside the pull request;
- the same failure returns with no new information after a fix; try a different evidence-backed approach or report what is missing instead of stacking patches;
- the user's budget is spent or they ask to stop.

Report each check's final state, each failure's classification, reruns made, every commit pushed with its SHA or the local fixes waiting for push approval, and what is still failing.
