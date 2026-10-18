# Contributing

Contributions should keep every skill independent of a specific company,
product, repository layout, host, or deployment environment.

## Requirements

- Use the `rumo-` namespace and lowercase hyphen-case for skill directories.
- Keep each `SKILL.md` activation description concrete and discriminating.
- Keep private project facts in a local Profile, never in this repository.
- Do not commit credentials, private keys, certificates, customer data, or
  internal infrastructure details.
- Add or update focused tests when changing scripts or deterministic rules.
- When a skill gains a rule whose loss would let an agent overstep its
  authority or overclaim a result, pin it in `scripts/tests/test_skill_rules.py`:
  in `RULES` when it lives in `SKILL.md`, in `REFERENCE_RULES` when it lives in
  a file under `references/`.
- Preserve unrelated files and avoid generated dependencies such as
  `node_modules`.

## Skill structure

Follow [skills/rumo-prose/references/agent-docs.md](skills/rumo-prose/references/agent-docs.md).
In short:

- The `description` names the triggering situations, the look-alikes that must
  not trigger, and the skill to use instead.
- The body runs: purpose, modes (if any), workflow with checkpoints, stop
  conditions, evidence and output. Red flags and shortcut rebuttals are
  optional and belong only where agents tend to skip steps.
- Aim for about 80 lines in a default skill's `SKILL.md`; move detail into
  `references/` and state when each reference must be read. Authorization
  rules and stop conditions stay in the body.
- Write every skill in your own words. Do not copy text from other projects.

## Default skills and extras

- `skills/` holds the default set that the installers always link.
- `extras/` holds optional skills that users install with `-Extras` or
  `--extras`. A default skill must not link to an extra; mention it by name and
  say what to do when it is not installed.
- A skill belongs in the default set when most engineering tasks pass through
  it, or when it guards against irreversible damage even if it is rarely
  needed. It belongs in extras when it produces a specific deliverable format,
  serves a narrow domain, needs an external service or runtime, or is a
  personal manual-only workflow.

## Validate changes

Windows:

```powershell
py -3 scripts\verify_skills.py
py -3 -m unittest discover -s scripts\tests -p "test_*.py"
py -3 scripts\run_auxiliary_tests.py
git diff --check
```

Linux and macOS:

```bash
python3 scripts/verify_skills.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/run_auxiliary_tests.py
git diff --check
```

## Trigger evals

`evals/` holds trigger cases for `claude plugin eval`: each case is a
realistic request plus graders asserting which skill fires and which
look-alike does not. The unit tests check only the suite's structure; running
it calls a model and costs money, so it stays out of CI. Run it after changing
a `description` (Claude Code 2.1.269 or later):

```bash
claude plugin eval . --runs 1 --ablation none --no-publish
```

Use `--case <name>` for one case and `--runs 3` before trusting a borderline
result. Results land in the ignored `evals/results/`. Add a case when a
request picks the wrong skill. `coding-baseline` is expected to fail: on a
small edit the client does not load `rumo-coding-guidelines`, which is why the
always-on snippet in its `references/` exists. A pass there means a
description change altered how the baseline loads.

Without `--runs`, each case runs three times per arm, and without
`--ablation none` it runs a second arm without the plugin, so a full default
run costs about six agent runs per case. `llm` graders add judge calls; pass
`--judge-model sonnet` when a small default judge looks unreliable. These
evals exercise Claude models only. When the eval tool is unavailable, run the
same prompts by hand in fresh sessions and compare the skills they pick.

### Codex trigger checks

`scripts/run_codex_trigger.py` sends the same trigger prompts to the Codex CLI
without naming a skill. Each run seeds a sample repository with a snapshot's
skills in `.agents/skills`, runs read-only, and counts a skill as chosen only
when Codex read that sample copy of its `SKILL.md`. The `uses-*` and `skips-*`
graders supply the expectations. It calls a model, so it is opt-in and stays
out of CI:

```powershell
python scripts/run_codex_trigger.py --snapshot <snapshot-root> --output-dir <task-evidence-dir> [--case debug-readonly] [--runs 3]
```

A run that errors, times out, or hits a usage limit is invalid, not a failure,
and stops the batch. Codex loads `rumo-coding-guidelines` on a small edit, so
`coding-baseline` can pass there; the runner flags that instead of failing.
Results describe only the recorded Codex CLI version and model settings.
Other clients remain untested, and neither client's result stands in for the
other's.

## Behavior evals

Cases tagged `behavior` check what an agent does once a skill fires, such as
not editing code during a review or not running a DELETE before the target
database is confirmed. Each one seeds a small git repository with a scaffold
script and grades only from the transcript, never with a judge model. Run
them before and after merging, rewriting, or substantially trimming a skill:

```bash
claude plugin eval . --tag behavior --scaffold --allow-tools Edit Write Bash --runs 1
```

`--scaffold` runs each case's script as you, outside the agent's sandbox, so
pass it only for this repository's own cases. Granting `Bash` needs Claude
Code's sandbox: on Windows run the suite under WSL2, and on Linux install
`bubblewrap` and `socat`. `review-readonly` needs only `Edit Write` and runs
anywhere.

The `chain-*` cases cover requests that cross skills: a small edit that must
stay light, a fully specified interface change, an authorization change, and
diagnosis followed by a fix. They need only `Edit Write` and grade the
resulting files and the final reply, so they show whether the skills keep a
task proportionate and honest but not whether tests ran. The Codex
`auth-change-verify` and `debug-then-fix` checks below cover execution for the
same scenarios. Regex graders compile as JavaScript: pass flags such as `i` in
the grader's `flags` field, never as a leading `(?i)`.

### Codex behavior checks

`scripts/run_codex_behavior.py` runs the local cases in
`scripts/codex_behavior_cases.py` through the existing Codex CLI. It calls a
model, so it is opt-in and stays out of CI. Unit tests for its evidence
parser and fixtures run in the ordinary test suite without model calls.

Create a snapshot containing `skills/`, then run in a new evidence directory
outside the checkout:

```powershell
python scripts/run_codex_behavior.py --snapshot <snapshot-root> --output-dir <task-evidence-dir>
```

Use `--case verify-honest` for one case. Compare old and new skill snapshots
with the same fixtures, model, reasoning settings, and grader version. Add
`--without-skills` for a baseline arm with no skills in the sample or the
prompt; its `no_rumo_skill_read` check must hold for the run to count. Keep
both snapshots and their source revisions with the evidence. The runner
disables installed Rumo copies for its child process only and explicitly
loads each sample's snapshot paths; it reuses existing authentication and
provider settings. On Windows it uses the unelevated workspace-write sandbox.
It never falls back to unsandboxed execution. Runtime or skill-read failure
invalidates the run; inspect it before spending another model call.

Results separate mechanical checks from a pending review verdict. Inspect the
JSONL commands, completed outputs, final replies, and changed files against
each saved acceptance criterion before assigning a verdict, and state whether
the reviewer was a person or an agent. A known failed
test must have a completed command, exit code 1, and the expected assertion;
reading a file, mentioning a command, or merely avoiding readiness phrases
does not prove it ran. Claude's `tool_used` grader checks a test attempt only;
its failure-report phrase graders do not establish arbitrary semantic truth.
Neither client result establishes behavior in the other client.

The timeout bounds one case's runtime across turns; it is not a debugging
attempt limit. Preserve partial evidence on timeout, terminate only the
runner-owned process tree, and report the case as unverified. Fresh paired
runs are scenario evidence, not a statistical claim of overall improvement.

`scripts/run_pi_behavior.py` runs the same read-only cases through the pi CLI
with any model pi can reach, to screen skill changes without spending the
Codex budget. pi has no sandbox, so the runner allows only `read`, `grep`,
`find`, and `ls`, refuses cases that edit files, and turns off installed
skills, extensions, and prompt templates. Its arguments, `--without-skills`
arm, and result layout match the Codex runner. A result from another model
only screens a change; confirm it with Codex or Claude before reporting it.
`--manifest <file>` adds replay cases from local repositories: each names a
repository, a commit, an optional `dirty_commit` whose changes become
uncommitted edits, the turns, the skills, and the acceptance criterion. Keep
manifests and their evidence outside this checkout when the repositories are
private.

`scripts/run_regression.py` reruns `REGRESSION` in
`scripts/codex_behavior_cases.py`: the cases where skills measurably changed
the outcome, each with the outcome already observed. It runs both arms of
every case `--reps` times through one runner (`codex` by default, or `pi`,
which skips cases that edit files), compares the candidate snapshot against
`--baseline` (another snapshot, or `without`), and writes `summary.md` with
validity counts, mechanical checks, and each final reply for grading. Options after `--` go to the runner. Run it
before and after any change that removes or rewrites skill text.

Pull requests should explain the user scenario, changed behavior, verification
performed, and any environment or acceptance boundary that was not exercised.
