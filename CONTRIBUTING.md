# Contributing

欢迎用中文提 issue 和 PR，规则与下文相同。

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
  not trigger, and the skill to use instead, in at most 100 words: clients keep
  every description in context for the whole session.
- Backticked `scripts/...` paths resolve from the skill's own directory, since
  that is where installed skills find their bundled scripts.
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

### Acceptance before push

These checks prove the files are well formed, not that a client still picks
the skill. When a change adds, removes, merges, or renames a skill, or alters a
skill's `description`, run the affected trigger cases (see
[Trigger evals](#trigger-evals)) once against a snapshot of the candidate in
one real client: Claude through `claude plugin eval`, or Codex through
`scripts/run_codex_trigger.py`. Wording, typo, and link fixes do not need it,
and neither every client nor the full suite is required.

Rules in a skill body are judged in real development: the maintainer's
feedback and `rumo-reflect` sessions show where a rule misfires. The Claude
behavior cases (see [Behavior evals](#behavior-evals)) are optional; run them
when the maintainer asks.

For each run, record the candidate commit, client and version, model, cases,
results, and evidence directory, keeping the evidence outside the checkout.
Any later edit to a description needs a fresh run. These cases call a model,
so when this session has no approval for model calls, ask once with the exact
cases. Never report such a change ready to push without this run; when it did
not happen, report it as a gap.

## Trigger evals

`evals/` holds trigger cases for `claude plugin eval`: each case is a
realistic request plus graders asserting which skill fires and which
look-alike does not. The unit tests check only the suite's structure; running
it calls a model and costs money, so it stays out of CI. Run it after changing
a `description` (Claude Code 2.1.269 or later).

For a full run, create a disposable copy of the candidate outside the checkout
and copy the model-invoked extras from `extras/` into that copy's `skills/`.
The released plugin still excludes extras; this snapshot only makes every
skill under test available to the client. A default-only case can run directly
against the checkout:

```bash
claude plugin eval <snapshot-root> --runs 1 --ablation none --no-publish
claude plugin eval . --case debug-readonly --runs 1 --ablation none --no-publish
```

Use `--case <name>` for one case and `--runs 3` before trusting a borderline
result. Results land in `evals/results/` under the evaluated root. Add a case
when a request picks the wrong skill. Every default or optional skill that the model
may select on its own needs at least one trigger case whose `uses-*` grader
names it. `coding-baseline` is expected to fail: on a
small edit the client does not load `rumo-coding-guidelines`, which is why the
always-on snippet in its `references/` exists. A pass there means a
description change altered how the baseline loads.

Without `--runs`, each case runs three times per arm, and without
`--ablation none` it runs a second arm without the plugin, so a full run
costs about six agent runs per case. `llm` graders add judge calls; pass
`--judge-model sonnet` when a small default judge looks unreliable. These
evals exercise Claude models only. When the eval tool is unavailable, run the
same prompts by hand in fresh sessions and compare the skills they pick.

### Codex trigger checks

`scripts/run_codex_trigger.py` sends the same trigger prompts to the Codex CLI
without naming a skill. Each run seeds a sample repository with a snapshot's
skills in `.agents/skills`, runs read-only, and counts a skill as chosen only
when Codex read that sample copy of its `SKILL.md`. The `uses-*` and `skips-*`
graders supply the expectations. For a full run or an extra case, include the
model-invoked extras in the snapshot's `skills/` as above. It calls a model,
so it is opt-in and stays out of CI:

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
script and grades only from the transcript, never with a judge model:

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
task proportionate and honest but not whether tests ran. Regex graders
compile as JavaScript: pass flags such as `i` in the grader's `flags` field,
never as a leading `(?i)`.

## Keep cases blind

A model that can tell it is being graded behaves differently from one doing
real work. Keep evaluation words and case names out of everything the model
sees: prompts, the git identity and commit messages in scaffold scripts, and
the path it works in. `scripts/tests/test_trigger_evals.py` checks prompts and
scaffold git metadata. The Codex trigger runner seeds each working copy at
`<output-dir>/w/<random>/project`, away from the case's logs, and refuses an
output directory whose path contains evaluation words, the words `candidate`
or `baseline`, or a case name. Decide whether a step happened from the
transcript or event stream, never from the agent's own account of it.

## Releases

Claude Code plugin users receive an update only when `version` in
`.claude-plugin/plugin.json` changes. For each release, raise that version,
move the `CHANGELOG.md` entries under the new version's heading, and tag the
final commit `v<version>`. `scripts/verify_skills.py` fails when the plugin
version has no matching `## <version>` section in `CHANGELOG.md`.

## Issues and pull requests

- Open issues through the [issue forms](https://github.com/rumoii/rumo-engineering-skills/issues/new/choose):
  a skill that should have fired and did not (or the reverse), a skill that
  fired but was not followed, or a proposal. Include the client, its version,
  the model, and the skills revision. Issues are public, so remove company
  names, internal hosts, paths, code, and credentials first.
- Report leaked credentials or private infrastructure privately as described in
  [SECURITY.md](SECURITY.md).
- Discuss a new skill or a large rewrite in an issue before opening a pull
  request.
- Keep one change per pull request. Unrelated fixes bundled together will be
  asked to split.
- Fill in the pull request template: the user scenario, the changed behavior,
  the checks actually run, any environment or acceptance boundary that was not
  exercised, and the AI disclosure.

## AI disclosure

AI help is welcome, and most changes here are tested with agents anyway. State
it honestly:

- Say whether you used AI. If you did, name the exact tool and model version
  rather than just "AI", and say what it did: finding the problem, drafting
  skill text, writing scripts, or writing tests.
- Read every changed line yourself and run the checks above before opening the
  pull request.
- Confirm an AI-reported misfire or misbehavior in a fresh session before
  filing it, or mark it unconfirmed.
- Undisclosed or unverified automated pull requests will be closed.

## Not accepted

- Skills or rules that only make sense for one company, product, repository,
  host, or agent client without a client-neutral alternative.
- Text copied from other skill collections, prompts, or documentation.
- Private project facts, credentials, or customer data, even as examples.

## License

By contributing, you agree that your contribution is released under the
repository's [MIT License](LICENSE).
