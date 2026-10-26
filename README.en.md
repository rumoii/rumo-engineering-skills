<div align="center">

# Rumo Engineering Skills

Engineering skills that make coding agents ask first, act carefully, and prove their work

[![Release](https://img.shields.io/github/v/release/rumoii/rumo-engineering-skills?label=release&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/releases/latest)
[![Stars](https://img.shields.io/github/stars/rumoii/rumo-engineering-skills?label=Stars&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/stargazers)
[![License](https://img.shields.io/github/license/rumoii/rumo-engineering-skills?label=license)](LICENSE)
![Clients](https://img.shields.io/badge/clients-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20SKILL.md-4b6b8a)

**[Quick Start](#quick-start)** · [Highlights](#highlights) · [Getting Started (Chinese)](GETTING_STARTED.md) · [Troubleshooting](#troubleshooting) · [简体中文](README.md)

<p align="center">
  <a href="https://github.com/paralcor">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/images/brand/paralcor-horizontal-dark.png">
      <img alt="PARALCOR" src="docs/images/brand/paralcor-horizontal-light.png" width="120">
    </picture>
  </a>
  <br>
  <sub>Rumo Engineering Skills is written and maintained by @rumoii and showcased under the PARALCOR brand.</sub>
</p>

</div>

A compact set of engineering skills for Claude Code, Codex, and other agents that load `SKILL.md` directories.

You do not need to learn engineering conventions first. Once installed, the agent pins down the request before coding, backs "done" with evidence, and stops to confirm before dropping data, deleting files, or changing a server.

## Highlights

- **Proven on a real team.** Since June 2026, dozens of engineers in the R&D department at my company have used these skills daily, in a customized edition with company-specific business content; this repository is the general edition without it. The skills carry no company, product, host, or deployment specifics; private facts live in a local [project profile](#advanced). Documentation is Chinese-first, with a complete English edition.
- **Evals, not claims.** Model-run evals in Claude Code and Codex check whether a plain-language request picks the right skill; in Claude Code they also check whether the agent then does the right thing. Adding, removing, or renaming a skill, or changing a description, is [accepted in a real client](CONTRIBUTING.md#acceptance-before-push) on the affected selection cases before push; how well the body rules work is judged from real development. The cases live in [`evals/`](evals/).
- **Brakes on risky operations.** Before dropping data, deleting files, changing a server, or touching production, the agent confirms the target and blast radius read-only and writes only after backup, rollback, and your explicit approval. These are rules for the agent, not an enforcement mechanism; use your client's own permission settings for hard limits.
- **Small tasks stay small.** A one-line copy change gets no plan and no review, just the most relevant check before handoff. Every skill description stays within 100 words, enforced by the validator, so the always-loaded context stays cheap.
- **Verify once, reuse every time.** A project verification recipe records how to start the application, what to click, and what proves success, and is run end to end once. The next agent follows it to check real features instead of rediscovering them.
- **Cross-client, and able to delegate.** The same skills install into Claude Code, Codex, and other clients that read `SKILL.md`. They can also hand a task to another local CLI or model, or have the models you configured review the same change independently; the agent reviews it too, checks every finding against the code, and merges them into one report that names which models raised each finding.

## What Changes

| You say | Without the skills, agents often | With the skills |
| --- | --- | --- |
| "Add an export feature" | Guess a design and start coding | Ask the open questions in one round, each with a recommended answer (`rumo-clarify`) |
| "The page returns 500, take a look" | Edit code while guessing | Reproduce, localize, and prove the root cause; leave the code alone unless asked to fix (`rumo-debug`) |
| "Clear the old rows from the test database" | Run `DELETE` right away | Confirm the database and affected row count read-only, then write only after backup, rollback, and your explicit approval (`rumo-database-change-safety`) |
| "Is it done?" | Say "done" without running tests | List the commands actually run and their results, and say what was not run (`rumo-verify`) |
| "I'm done, check that it really works" | Run unit tests and call it fine | Follow the project's verification recipe to start the app, drive the real feature, and keep the evidence; flag the recipe when it is out of date (`rumo-verify`) |

## How A Task Flows

Take "The orders page returns 500, fix it":

1. `rumo-debug` reproduces the error, follows the call chain to the cause, and proves it with logs, requests, or data instead of guessing.
2. `rumo-test` writes a test that reproduces the defect and confirms it fails before the fix.
3. The fix turns that test green, then the surrounding tests run.
4. When the project has a verification recipe, the agent follows it to start the app, open the orders page, confirm the real page works again, and keep the evidence.
5. `rumo-verify` lists the commands actually run and their results before handoff, and names any check that did not run instead of saying "should be fine".
6. Only when you ask does `rumo-git-commit` commit by the repository's conventions; pushing needs your explicit request too.

Small edits, features, refactors, performance problems, prototypes, pauses, and other tasks also have default routes, chosen by `rumo-coding-guidelines`; the full list is in [task-flows.md](skills/rumo-coding-guidelines/references/task-flows.md).

To pick a skill yourself, call it by name:

| When you want to | Codex | Claude Code |
| --- | --- | --- |
| Pin down a vague request | `$rumo-clarify` | `/rumo-clarify` |
| Break agreed work into verifiable tasks, then work them one by one | `$rumo-plan` | `/rumo-plan` |
| Implement test-first | `$rumo-test` | `/rumo-test` |
| Find the cause of a bug, read-only | `$rumo-debug` | `/rumo-debug` |
| Check the change before calling it done, or build a project verification recipe | `$rumo-verify` | `/rumo-verify` |
| Review a diff without editing | `$rumo-review` | `/rumo-review` |
| Commit, land, push, or open a pull request | `$rumo-git-commit` | `/rumo-git-commit` |

Skills marked manual only never fire on their own; call them by name. [Worked examples](GETTING_STARTED.md#完整案例) (Chinese) follow three requests from prompt to delivery.

## Quick Start

### Claude Code Plugin

The recommended route when you use only Claude Code; no clone needed. Run this in a session, then start a new session (Claude Code 2.1.275 or later):

```text
/plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills
```

From a shell (Claude Code 2.1.292 or later), use `claude plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills`. On older versions, add the marketplace first:

```bash
claude plugin marketplace add rumoii/rumo-engineering-skills
claude plugin install rumo-engineering-skills@rumo-engineering-skills
```

Plugin skills carry a prefix, such as `/rumo-engineering-skills:rumo-clarify`. The plugin covers Claude Code only and has no extras; other clients use the installer. Choose one method per machine: if the installer already linked skills into `~/.claude/skills`, adding the plugin loads every skill twice.

### Install With An Agent

For Codex or another client, give your agent this prompt. It previews the install, runs it, and tells you what changed:

```text
Install the skills from https://github.com/rumoii/rumo-engineering-skills by following its README.
1. Clone it if it is not present, run the installer with --dry-run (-DryRun on Windows), and show me what it would change.
2. Run the installer without --baseline and report which clients were linked.
3. Ask me before writing to my user-level CLAUDE.md or AGENTS.md. Only if I agree, rerun it with --baseline (-Baseline) and show me the block it added.
4. List the files that changed and remind me to start a new session.
5. Remind me to run rumo-setup in the new session to choose the agents, models, and reasoning effort for multi-model review and delegation.
```

An agent installing from this README without that prompt follows the same rule: it never adds `--baseline` or `-Baseline` without the user's explicit agreement, because that edits the user's own instruction files.

### Install With The Installer

You need Git and Python 3, but not administrator rights. `-ExecutionPolicy Bypass` applies to this one run and leaves system settings unchanged.

```powershell
git clone https://github.com/rumoii/rumo-engineering-skills.git
cd rumo-engineering-skills
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -NoPull
```

```bash
git clone https://github.com/rumoii/rumo-engineering-skills.git
cd rumo-engineering-skills
./install.sh --no-pull
```

The installer validates the repository, then links the default skills into every detected client (Codex, Claude Code, and the shared `~/.agents` directory). It manages only `rumo-*` links and leaves other skills alone. On success it prints one `<count> skills linked in <directory>` line per client and ends with a line starting `Next:`. Start a new session afterwards so the client reloads its skill list.

### Configure Agents The First Time (Optional)

The agent can call other AI coding tools installed on this machine to re-check a change independently or take over work. You do not need it: every skill works without it, and with a single AI tool on the machine there is nothing to configure. To use it, open a new session after installing and run `/rumo-setup` (`/rumo-engineering-skills:rumo-setup` with the plugin, `$rumo-setup` in Codex). It explains each setting, recommends a configuration with reasons, and writes `~/.rumo-engineering-skills/agents.json` only after each choice passes a probe. Another tool spends its quota only when it is called, and unless you name one, the agent asks you first. To change the configuration later, rerun it or just say "make review use grok at high".

The CLIs with a completed real run are codex, claude, grok, pi, and qwen; aider, cline, copilot, cursor, and goose are experimental, and gemini and opencode are disabled. [adapters.md](skills/rumo-agent-collaboration/references/adapters.md) explains why and how a CLI becomes supported.

### Troubleshooting

- Installer fails, skills do not appear, or every skill shows up twice: see the [troubleshooting section](GETTING_STARTED.md#6-遇到问题) of GETTING_STARTED.md (Chinese). Installer messages are in English, so you can search for the exact text.
- When the installer reports an error, rerun it with `-DryRun` (`--dry-run`) and keep the full output.
- Still stuck: [open an issue](https://github.com/rumoii/rumo-engineering-skills/issues/new/choose) with the `-DryRun` output, `git rev-parse HEAD`, and your client version. Issues are public; remove user names, company paths, and code first.

## Support

| Client | Install method | Verified |
| --- | --- | --- |
| Claude Code | Plugin or installer | Install, loading, trigger evals, behavior evals (including cross-skill cases) |
| Codex | Installer | Install, loading, trigger evals |
| Other clients that read `~/.agents/skills` | Installer plus the shared directory | Install and loading only |

A successful call by name shows that the client loaded the skill, not that it will pick the skill from a plain-language request. [GETTING_STARTED.md](GETTING_STARTED.md#其他客户端) (Chinese) shows how to connect other clients. External-agent `start` and `resume` currently require Windows or Linux/WSL. Other platforms, including macOS, can inspect existing run records only; installing the skills does not enable those external-run features.

## Default Skills

Installed by default.

| Skill | Purpose |
| --- | --- |
| `rumo-clarify` | Group answerable questions with recommendations; follow up on newly exposed key decisions and never default critical ones |
| `rumo-plan` | Short spec and verifiable task breakdown, task-by-task execution of an agreed plan, or a durable engineering decision record |
| `rumo-coding-guidelines` | Baseline discipline: real code paths, only requested and necessary work, a risk gate for high-risk changes, verified results |
| `rumo-test` | Evidence planning and test-first implementation |
| `rumo-debug` | Reproduce, localize, and prove a root cause; read-only unless the fix is requested |
| `rumo-verify` | Exact change scope and the smallest sufficient checks before claiming done; building repository gates; project verification recipes |
| `rumo-review` | Read-only diff review or named-scope audit, an explicit review-fix loop, a simplification audit, addressing review feedback, or, with your consent, a review panel of the models you configured, merged and checked |
| `rumo-git-commit` | Commits, branch landing, history cleanup, releases, pushes, pull requests, and following an open pull request's CI checks, per repository conventions |
| `rumo-interface` | Compatible evolution of APIs, messages, configuration, and stored formats, with HTTP contract checks |
| `rumo-lifecycle-safety` | Ownership, retry, cancellation, timeout, shutdown, and cleanup for long-lived work |
| `rumo-database-change-safety` | Authorized, backed-up, bounded, and reversible database writes |
| `rumo-filesystem-safety` | Deletion and bulk cleanup scaled to the blast radius |
| `rumo-remote-ops` | Remote Linux queries and changes, service deployment, backup and restore, and artifact deployment |
| `rumo-prose` | Comments, errors, logs, UI strings, docs, and agent-facing files that keep every fact |
| `rumo-frontend` | Frontend page work and new interface design with accessibility checks, local dev-server troubleshooting, and requested browser evidence |
| `rumo-handoff` | In a new session, asked for the current progress or the next step, condense this project's recent Claude Code, Codex, and Kimi Code sessions and check them against the repository; on request, write a self-contained handoff and link it into existing navigation so the recipient can discover it |
| `rumo-project-profile` | Resolve and validate private project profiles for other skills |
| `rumo-reflect` | Session retrospective: recurring mistakes and corrections, each fix discussed and applied only with your approval |
| `rumo-setup` | Choose, once or at any time, the CLI, model, and reasoning effort for multi-model review and default delegation; probes each lane read-only before saving |
| `rumo-agent-collaboration` | Delegate, transfer, or relay work to another agent CLI or model, or collaborate through Orca; a same-provider model runs as the client's own subagent, any other through its CLI, with the lane matched to the work. See [Configure Agents The First Time](#configure-agents-the-first-time-optional) for which CLIs are supported |

## Optional Extras

Not installed by default, and available only through the installer; the plugin has no extras.

| Skill | Purpose |
| --- | --- |
| `rumo-diagram` | Mermaid business flowcharts and confirmed engineering topology diagrams with preview and export |
| `rumo-document-writing` | Formal Word delivery documents |
| `rumo-offline-delivery-audit` | Offline package integrity, provenance, installation, rollback, and acceptance limits |
| `rumo-daily-report` | Incremental Chinese daily reports in a dated text file (manual only) |
| `rumo-linux-inspect` | Read-only Linux hardware inventory or memory inspection (manual only) |
| `rumo-imagegen` | One image through a user-configured OpenAI-compatible endpoint (manual only) |

```powershell
.\install.ps1 -NoPull -ListExtras
.\install.ps1 -NoPull -Extras rumo-diagram,rumo-document-writing
.\install.ps1 -NoPull -RemoveExtras rumo-document-writing
```

```bash
./install.sh --no-pull --list-extras
./install.sh --no-pull --extras rumo-diagram,rumo-document-writing
./install.sh --no-pull --remove-extras rumo-document-writing
```

Installed extras stay installed when you rerun the installer without options.

## Always-On Baseline

Clients load a skill only when its description matches the request, so a small edit can skip the baseline rules in `rumo-coding-guidelines`, and one skill may not bring in the next. The installer can keep the core rules, the risk gate, and a table of which skill fits which situation in the user-level instruction file of each detected client: `CLAUDE.md` in the Claude Code home and `AGENTS.md` in the Codex home. The block sits between `rumo-engineering-skills:baseline` markers, and nothing outside them changes.

<details>
<summary>Add, update, and remove</summary>

```powershell
.\install.ps1 -NoPull -Baseline
.\install.ps1 -NoPull -RemoveBaseline
```

```bash
./install.sh --no-pull --baseline
./install.sh --no-pull --remove-baseline
```

Later runs without options keep the block current, and when it is absent they end with a one-line reminder. Plugin users and other clients are offered the block the first time they run `rumo-setup`, which writes the current client's user-level instruction file without a clone and asks for that file's path in a client other than Claude Code or Codex. You can also run the helper directly, for example `python3 skills/rumo-coding-guidelines/scripts/baseline_block.py --target ~/.claude/CLAUDE.md --install`, or paste the block from [agents-snippet.md](skills/rumo-coding-guidelines/references/agents-snippet.md) by hand.

</details>

## Update And Uninstall

The installer writes only these: the `rumo-*` links in client skill directories; the baseline block in `CLAUDE.md` and `AGENTS.md`, once you agree; and `~/.rumo-engineering-skills/config.json` when you pass `-ProfilesRepo`.

**Update.** Installer: rerun `.\install.ps1` or `./install.sh` without `-NoPull` (`--no-pull`). It runs `git pull --ff-only` first, then relinks, keeping installed extras and the baseline block; start a new session afterwards. If the pull succeeds but a later validation or installation step fails, the installer also warns that existing links may already serve updated content; the repository has not been rolled back. Plugin: run `claude plugin marketplace update rumo-engineering-skills`, then `claude plugin update rumo-engineering-skills@rumo-engineering-skills`, and start a new session. An installed plugin updates only when a release raises its `version`; see [CHANGELOG.md](CHANGELOG.md) for what each version changed. The installer links to this checkout, so to stay on one version, check out a release tag such as `git checkout v0.9.0` in the checkout and rerun the installer with `-NoPull` (`--no-pull`); to return to the latest version, run `git checkout main` and rerun without `-NoPull`.

**Uninstall.** Installer: add `-DryRun` (`--dry-run`) first to see what would go, then run `.\install.ps1 -Uninstall` or `./install.sh --uninstall`. Uninstall removes only the `rumo-*` links into this repository and the always-on baseline block, and leaves skills from other sources alone. It keeps the cloned repository, `~/.rumo-engineering-skills/config.json`, and project profiles; delete those by hand when you no longer need them. Plugin: run `claude plugin uninstall rumo-engineering-skills@rumo-engineering-skills`, then start a new session.

Do not delete `rumo-*` links in File Explorer or with `Remove-Item -Recurse`: those can follow the link and delete the skill files inside the repository.

## Advanced

<details>
<summary>Project profiles and environment variables</summary>

Profiles are optional; the skills work without them. Repository names, component inventories, hosts, service names, install paths, and credentials belong in a local profile or a private profiles repository, never in this repository. [GETTING_STARTED.md](GETTING_STARTED.md#4-项目-profile可选) (Chinese) shows how to create, fill, and check one.

Environment variables:

- `RUMO_SKILLS_REPO`: stable checkout
- `RUMO_SKILLS_REMOTE`: clone URL
- `RUMO_SKILL_PROFILES_REPO`: private profiles checkout
- `RUMO_PROJECT_PROFILE`: explicit profile ID
- `RUMO_AGENTS_CONFIG`: a separate agent configuration, such as for a repository that should always use other lanes
- `CODEX_HOME`, `CLAUDE_HOME`, `AGENTS_HOME`: custom client homes

Pass `-ProfilesRepo <path>` or `--profiles-repo <path>` to persist a profiles checkout in `~/.rumo-engineering-skills/config.json`.

</details>

<details>
<summary>Development and validation</summary>

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing a skill or script.

```powershell
py -3 scripts\verify_skills.py
py -3 -m unittest discover -s scripts\tests -p "test_*.py"
py -3 scripts\run_auxiliary_tests.py
```

```bash
python3 scripts/verify_skills.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/run_auxiliary_tests.py
```

On Windows without the `py` launcher, use `python`. The `install.sh` tests run only on Linux, macOS, or WSL and are skipped on Windows. The validator checks names, frontmatter, UI metadata, relative links, catalog inventories grouped into default skills and extras, default-skill size, description length, script paths inside each skill, trigger-case coverage, stray license files, JSON syntax, likely secrets, and tracked credential files. To block private vocabulary, list terms in `~/.rumo-engineering-skills/forbidden-terms.txt` (or the file named by `RUMO_FORBIDDEN_TERMS_FILE`), one per line, with a `re:` prefix for regular expressions; keep that file out of the repository.

These commands check the repository, not an installation. [GETTING_STARTED.md](GETTING_STARTED.md#2-验证安装) (Chinese) shows how to check the installed state.

</details>

<details>
<summary>Eval coverage</summary>

Model-run evals cover automatic selection in Claude Code and the Codex CLI. Behavior evals run in Claude Code and cover single-skill cases and cross-skill `chain-*` cases. Other clients are verified for install and loading only. For what each eval proves, see [CONTRIBUTING.md](CONTRIBUTING.md#trigger-evals).

</details>

## Documentation

- [Getting started](GETTING_STARTED.md) (Chinese)
- [Skill catalog](skills/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md) (Chinese) · [Release notes](https://github.com/rumoii/rumo-engineering-skills/releases/latest)

## Security

- Never commit passwords, credential files, tokens, private keys, or certificates with private material.
- Installers, profile resolution, scripts, tests, and reports must never print secret values.
- Default access covers localhost or environments explicitly marked as development or test. Production requires exact authorization and stays read-only unless a change is separately approved.

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a public issue.

## Star History

<a href="https://star-history.com/#rumoii/rumo-engineering-skills&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=rumoii/rumo-engineering-skills&type=Date&theme=dark">
    <img alt="Star history" src="https://api.star-history.com/svg?repos=rumoii/rumo-engineering-skills&type=Date" width="600">
  </picture>
</a>

## License

MIT; see [LICENSE](LICENSE).
