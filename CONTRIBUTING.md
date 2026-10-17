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
  authority or overclaim a result, pin it in `scripts/tests/test_skill_rules.py`.
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
evals exercise Claude models only; triggering in other clients and models is
untested. When the eval tool is unavailable, run the same prompts by hand in
fresh sessions and compare the skills they pick.

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

Pull requests should explain the user scenario, changed behavior, verification
performed, and any environment or acceptance boundary that was not exercised.
