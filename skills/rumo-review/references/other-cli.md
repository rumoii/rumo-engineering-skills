# Review Through Another CLI

Read when the user asks for a second opinion from a different model or provider, or before offering one. It works in any client that can run shell commands: the current agent calls another installed agent CLI in its non-interactive mode, so no subagent or orchestration feature is needed. A client that cannot run shell commands cannot use this route.

## Authorization

Never start another CLI on your own. Before running anything, tell the user:

- which CLI and, when known, which model will review;
- what leaves the machine: the diff, the named files, and the repository guidance you will pass, sent to that CLI's provider;
- that the run spends the user's quota on that provider.

Run only after the user agrees to that CLI and that content. Agreement covers this review target; ask again for a new target or a different CLI.

A request naming the CLI, review target, and scope already supplies that agreement; do not ask again for the same scope. State the content and quota use above, then run. For an adapter not yet verified, show the command and known limits first. Unverified status alone does not require repeated approval. Extra content, a different route, or greater access needs separate agreement.

## Choose And Check The CLI

1. Prefer a provider different from the current client's model; a second run of the same model adds little independence.
2. Only when running the CLI directly, without `rumo-agent-collaboration` (whose `start` checks an adapter's CLI itself): confirm the CLI is installed, then read its `--help` (or the help of its non-interactive subcommand) and find two things: a non-interactive mode that takes a prompt and exits, and a read-only mode, sandbox, or permission setting that prevents file edits and command side effects. Without a read-only setting you have confirmed, do not use that CLI.
3. Examples, to be checked against the installed version's help before use: `codex exec --sandbox read-only` and `claude -p --permission-mode plan`.

## Run

- Use `rumo-agent-collaboration` for CLI execution and records with `--access read-only`; this review skill owns the review standard and assessment. Every rule in this file still applies. If the collaboration skill is unavailable, run the CLI directly as described here. A disabled adapter cannot be used; do not bypass that decision by launching its CLI directly.
- Pass only the target (the exact `git diff` range or files), the review standard from SKILL.md, and the repository guidance. Withhold the fix history, earlier findings, and your own conclusions.
- When the read-only sandbox blocks the CLI from running Git, include the diff text in the prompt instead.
- Capture the output to a file outside the repository.
- Wait as step 4 of `rumo-agent-collaboration` describes: in a client that runs background commands and notifies when they finish, run the command in the background; otherwise launch it with `--detach`, end your turn, and give the user the `watch` command and what to tell you when the review finishes. Do not read the CLI's live output while it runs. Only when you run the CLI directly because the collaboration skill is unavailable, run it once in the foreground with a timeout long enough for a large review.

## Stop Conditions

- The CLI is missing, not signed in, or fails authentication: report it and fall back to the next review backend. Never sign in, copy credentials, or change the CLI's configuration on the user's behalf.
- The output is empty, cut off, or not a review: report the failure. It is not evidence that the change has no findings.
- The CLI edited files despite the read-only setting: stop, report the changed paths, and leave them for the user to inspect.

## Use The Result

Check every finding against the code with [judging-findings.md](judging-findings.md) before acting on it. In the report, name the CLI, its version, and the model that produced the review.
