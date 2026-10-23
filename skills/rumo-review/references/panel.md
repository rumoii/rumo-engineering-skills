# Review Panel

Read before a review by other models: a multi-model panel, or a second opinion from one named CLI, which is a panel of one lane. The other models review the same target independently through installed agent CLIs; you review it too, then check every finding against the code and write one report. Independence comes from different models, not from assigned personas, and the panel never edits code.

## When To Run One

- **The user asks:** a multi-model review, several models, the configured reviewers, or a second opinion from a named CLI or model.
- **You propose one** for a change that `rumo-test` rated high risk, or a sizable change to authorization, money, durable data, concurrency, or a public interface. Do not propose one for small or low-risk changes. `auto_panel` from `agent_config.py lanes review` decides the next step: `ask` asks in one line, `allow` states the lanes and launches, and `off` means no proposal.

## Authorization

Never start another CLI on your own. Before launching, state in one line which lanes will run (CLI, model, effort), what leaves the machine (the diff, the named files, and the repository guidance, sent to each lane's provider), and that each lane spends its provider's quota. Then:

- A request that names the panel or the CLI, the review target, and the scope already supplies agreement; do not ask again for the same scope. So does `auto_panel: allow` for a panel you proposed.
- Otherwise run only after the user agrees to those lanes and that content. Agreement covers this target; ask again for a new target, other lanes, or extra content.
- For an adapter not yet verified, show the command and known limits first. Unverified status alone does not require repeated approval.

## Lanes

- Use the lanes the user names; otherwise run `agent_config.py lanes review`. It and `agent_run.py` live in `../rumo-agent-collaboration/scripts/`, resolved from this skill's directory. Exit 3 means none are configured: ask once which CLI to use and mention that `rumo-setup` saves the choice.
- Prefer providers other than your own; another run of your own model adds little independence.
- Run every lane through `agent_run.py` with `--access read-only`, which checks the CLI itself. If that skill is unavailable, run a CLI directly only after its `--help` confirms a non-interactive mode and a read-only setting; without a confirmed read-only setting, do not use that CLI. A disabled adapter cannot be used, directly or not.

## Run

1. **Target and intent.** Settle the target as SKILL.md describes, then write one paragraph stating what the change is meant to do, from the request, commit messages, and any pull request description. Ask when you cannot tell.
2. **Brief.** Write one brief for every lane, to a file outside the repository: the intent, the exact diff range and text, the What To Look For list and Report format from SKILL.md, and where the repository guidance lives. Tell the reviewer to judge how well the change achieves the intent without disputing the intent, to report only problems, never praise, and that "no findings" is a valid answer. Withhold the fix history, earlier findings, and your own conclusions. Tell reviewers to start from the diff and open other files only to confirm or rule out a specific suspected problem, not to survey the repository; you read the surrounding code yourself. Paste whole files only when the read-only sandbox blocks reading, and the diff text whenever it blocks Git.
3. **Launch** every lane at once: `agent_run.py start <cli> --cwd <repository> --prompt-file <brief> --access read-only`, plus the lane's `--model`, `--effort`, and `--executable`. Pass no `--timeout` unless the user names a deadline; never guess a duration. In a client that runs background commands and reports their exit, run each that way. Tell the user the lanes, their run IDs, and `agent_run.py watch <run-id>` for progress.
4. **Review it yourself** following SKILL.md while the lanes run, and save your findings to a file before reading any lane's output. In a client that cannot report background exits, launch with `--detach` instead, finish your own review, end your turn, and ask the user to tell you when the lanes finish; do not read their live output meanwhile.
5. **Collect.** A lane that fails, times out, returns nothing, or returns something that is not a review is a dropout: record why and continue with the rest. Never retry it on another model or substitute a close one, and never sign in, copy credentials, or change a CLI's configuration on the user's behalf. A dropout is not evidence that the change has no findings. When every lane drops out, say the result is a single-model review. If a CLI edited files despite the read-only setting, stop, report the changed paths, and leave them for the user.
6. **Judge.** Check every finding, yours included, against the code with [judging-findings.md](judging-findings.md). Merge findings that describe the same issue and keep the list of lanes that raised each. Record every run's decision with `agent_run.py record`.
7. **Do not hold the report for the slowest lane.** Once your own review is saved and judged, give the report with the lanes still running marked as pending, so the user can act on it. When a client reports background exits, judge each later lane as it finishes and send the additions. Stop a lane only when the user asks, with `agent_run.py cancel <run-id>`, and report it as a dropout stopped by the user.

## Report

Findings first, in the severity format of SKILL.md, each with the lanes that raised it, then:

- **Lanes:** each lane's CLI, model, effort, run ID, and its number of findings, or its dropout reason.
- **Dismissed:** each dismissed finding, the lanes that raised it, and the file, line, test, or documentation that settles it.
- **Agreement:** where lanes independently agreed, where they disagreed, and what that suggests.

In Loop mode, run a panel in a round only when the user asked for one.
