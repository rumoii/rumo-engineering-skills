<div align="center">

# Rumo Engineering Skills

Engineering skills that make coding agents ask first, act carefully, and prove their work

[![Release](https://img.shields.io/github/v/release/rumoii/rumo-engineering-skills?label=release&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/releases/latest)
[![Stars](https://img.shields.io/github/stars/rumoii/rumo-engineering-skills?label=Stars&color=2a8f7b)](https://github.com/rumoii/rumo-engineering-skills/stargazers)
[![License](https://img.shields.io/github/license/rumoii/rumo-engineering-skills?label=license)](LICENSE)
![Clients](https://img.shields.io/badge/clients-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20SKILL.md-4b6b8a)

**[Quick Start](#quick-start)** · [Getting Started (Chinese)](GETTING_STARTED.md) · [Skills](#default-skills) · [Troubleshooting](#troubleshooting) · [简体中文](README.md)

</div>

A compact set of engineering skills for Claude Code, Codex, and other agents that load `SKILL.md` directories. The skills carry no company, product, host, or deployment specifics.

You do not need to learn engineering conventions first. Once installed, the agent pins down the request before coding, backs "done" with evidence, and stops to confirm before dropping data, deleting files, or changing a server.

I wrote these skills. Since June 2026, dozens of engineers in the R&D department at my company have used them daily. They run a customized edition with company-specific business content; this repository is the general edition without it.

## What Changes

| You say | Without the skills, agents often | With the skills |
| --- | --- | --- |
| "Add an export feature" | Guess a design and start coding | Ask the open questions in one round, each with a recommended answer (`rumo-clarify`) |
| "The page returns 500, take a look" | Edit code while guessing | Reproduce, localize, and prove the root cause; leave the code alone unless asked to fix (`rumo-debug`) |
| "Clear the old rows from the test database" | Run `DELETE` right away | Confirm the database and affected row count read-only, then write only after backup, rollback, and your explicit approval (`rumo-database-change-safety`) |
| "Is it done?" | Say "done" without running tests | List the commands actually run and their results, and say what was not run (`rumo-verify`) |

## Support

| Client | Install method | Verified |
| --- | --- | --- |
| Claude Code | Plugin or installer | Install, loading, trigger evals, behavior evals (including cross-skill cases) |
| Codex | Installer | Install, loading, trigger evals, behavior evals (including cases that run tests) |
| Other clients that read `~/.agents/skills` | Installer plus the shared directory | Install and loading only |

A successful call by name shows that the client loaded the skill, not that it will pick the skill from a plain-language request. [GETTING_STARTED.md](GETTING_STARTED.md#其他客户端) (Chinese) shows how to connect other clients.

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

## Usage

Then work as usual; skills fire from their descriptions. The everyday workflow:

```text
clarify -> plan -> test -> verify -> review -> git-commit
```

Each step is a skill. Use only the ones a task needs: a one-line fix goes straight to coding and verification, while a vague feature request starts with `rumo-clarify`. To pick a skill yourself, call it by name:

| When you want to | Codex | Claude Code |
| --- | --- | --- |
| Pin down a vague request | `$rumo-clarify` | `/rumo-clarify` |
| Break agreed work into verifiable tasks, then work them one by one | `$rumo-plan` | `/rumo-plan` |
| Implement test-first | `$rumo-test` | `/rumo-test` |
| Find the cause of a bug, read-only | `$rumo-debug` | `/rumo-debug` |
| Check the change before calling it done | `$rumo-verify` | `/rumo-verify` |
| Review a diff without editing | `$rumo-review` | `/rumo-review` |
| Commit, land, push, or open a pull request | `$rumo-git-commit` | `/rumo-git-commit` |

Skills marked manual only never fire on their own; call them by name. [Worked examples](GETTING_STARTED.md#完整案例) (Chinese) follow three requests from prompt to delivery.

### Troubleshooting

- Installer fails, skills do not appear, or every skill shows up twice: see the [troubleshooting section](GETTING_STARTED.md#6-遇到问题) of GETTING_STARTED.md (Chinese). Installer messages are in English, so you can search for the exact text.
- When the installer reports an error, rerun it with `-DryRun` (`--dry-run`) and keep the full output.
- Still stuck: [open an issue](https://github.com/rumoii/rumo-engineering-skills/issues/new/choose) with the `-DryRun` output, `git rev-parse HEAD`, and your client version. Issues are public; remove user names, company paths, and code first.

## Default Skills

Installed by default.

| Skill | Purpose |
| --- | --- |
| `rumo-clarify` | Group answerable questions with recommendations; follow up on newly exposed key decisions and never default critical ones |
| `rumo-plan` | Short spec and verifiable task breakdown, task-by-task execution of an agreed plan, or a durable engineering decision record |
| `rumo-coding-guidelines` | Baseline discipline: real code paths, only requested and necessary work, verified results |
| `rumo-test` | Evidence planning, test-first implementation, and high-assurance spec-and-evidence work |
| `rumo-debug` | Reproduce, localize, and prove a root cause; read-only unless the fix is requested |
| `rumo-verify` | Exact change scope and the smallest sufficient checks before claiming done; building repository gates |
| `rumo-review` | Read-only diff review or named-scope audit, an explicit review-fix loop, a simplification audit, or addressing review feedback |
| `rumo-git-commit` | Commits, branch landing, history cleanup, releases, pushes, and pull requests following repository conventions |
| `rumo-interface` | Compatible evolution of APIs, messages, configuration, and stored formats, with HTTP contract checks |
| `rumo-lifecycle-safety` | Ownership, retry, cancellation, timeout, shutdown, and cleanup for long-lived work |
| `rumo-database-change-safety` | Authorized, backed-up, bounded, and reversible database writes |
| `rumo-filesystem-safety` | Deletion and bulk cleanup scaled to the blast radius |
| `rumo-remote-ops` | Remote Linux queries and changes, service deployment, backup and restore, and artifact deployment |
| `rumo-prose` | Comments, errors, logs, UI strings, docs, and agent-facing files that keep every fact |
| `rumo-frontend` | Frontend page work and new interface design with accessibility checks, local dev-server troubleshooting, and requested browser evidence |
| `rumo-handoff` | A self-contained handoff document for another session or client (manual only) |
| `rumo-project-profile` | Resolve and validate private project profiles for other skills |

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

Clients load a skill only when its description matches the request, so a small edit can skip the baseline rules in `rumo-coding-guidelines`. The installer can keep a short index of those rules in the user-level instruction file of each detected client: `CLAUDE.md` in the Claude Code home and `AGENTS.md` in the Codex home.

```powershell
.\install.ps1 -NoPull -Baseline
.\install.ps1 -NoPull -RemoveBaseline
```

```bash
./install.sh --no-pull --baseline
./install.sh --no-pull --remove-baseline
```

The block sits between `rumo-engineering-skills:baseline` markers, and nothing outside them changes. Later runs without options keep the block current, and when it is absent they end with a one-line reminder. Plugin users and other clients can run the helper directly, for example `python3 skills/rumo-coding-guidelines/scripts/baseline_block.py --target ~/.claude/CLAUDE.md --install`, or paste the block from [agents-snippet.md](skills/rumo-coding-guidelines/references/agents-snippet.md) by hand.

## Update And Uninstall

The installer writes only these: the `rumo-*` links in client skill directories; the baseline block in `CLAUDE.md` and `AGENTS.md`, once you agree; and `~/.rumo-engineering-skills/config.json` when you pass `-ProfilesRepo`.

### Update

Installer: rerun it without `-NoPull` (`--no-pull`). It runs `git pull --ff-only` first, then relinks, keeping installed extras and the baseline block. Start a new session afterwards.

```powershell
.\install.ps1
```

```bash
./install.sh
```

Plugin: run `claude plugin marketplace update rumo-engineering-skills`, then `claude plugin update rumo-engineering-skills@rumo-engineering-skills`, and start a new session.

### Uninstall

Installer: add `-DryRun` (`--dry-run`) first to see what would go. Uninstall removes only the `rumo-*` links into this repository and the always-on baseline block, and leaves skills from other sources alone. It keeps the cloned repository, `~/.rumo-engineering-skills/config.json`, and project profiles; delete those by hand when you no longer need them.

```powershell
.\install.ps1 -Uninstall
```

```bash
./install.sh --uninstall
```

Do not delete `rumo-*` links in File Explorer or with `Remove-Item -Recurse`: those can follow the link and delete the skill files inside the repository.

Plugin: run `claude plugin uninstall rumo-engineering-skills@rumo-engineering-skills`, then start a new session.

## Project Profiles

Profiles are optional; the skills work without them. Repository names, component inventories, hosts, service names, install paths, and credentials belong in a local profile or a private profiles repository, never in this repository. [GETTING_STARTED.md](GETTING_STARTED.md#4-项目-profile可选) (Chinese) shows how to create and fill one.

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

<details>
<summary>Environment variables</summary>

- `RUMO_SKILLS_REPO`: stable checkout
- `RUMO_SKILLS_REMOTE`: clone URL
- `RUMO_SKILL_PROFILES_REPO`: private profiles checkout
- `RUMO_PROJECT_PROFILE`: explicit profile ID
- `CODEX_HOME`, `CLAUDE_HOME`, `AGENTS_HOME`: custom client homes

Pass `-ProfilesRepo <path>` or `--profiles-repo <path>` to persist a profiles checkout in `~/.rumo-engineering-skills/config.json`.

</details>

## Development

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing a skill or script.

<details>
<summary>Validation commands</summary>

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

On Windows without the `py` launcher, use `python`. The `install.sh` tests run only on Linux, macOS, or WSL and are skipped on Windows. The validator checks names, frontmatter, UI metadata, relative links, catalog inventories grouped into default skills and extras, default-skill size, stray license files, JSON syntax, likely secrets, and tracked credential files. To block private vocabulary, list terms in `~/.rumo-engineering-skills/forbidden-terms.txt` (or the file named by `RUMO_FORBIDDEN_TERMS_FILE`), one per line, with a `re:` prefix for regular expressions; keep that file out of the repository.

These commands check the repository, not an installation. [GETTING_STARTED.md](GETTING_STARTED.md#2-验证安装) (Chinese) shows how to check the installed state.

</details>

<details>
<summary>Eval coverage</summary>

Model-run evals cover automatic selection in Claude Code and the Codex CLI. Behavior evals cover single-skill cases, cross-skill `chain-*` cases, and Codex cases that run tests. Other clients are verified for install and loading only. For what each eval proves, see [CONTRIBUTING.md](CONTRIBUTING.md#trigger-evals).

</details>

## Documentation

- [Getting started](GETTING_STARTED.md) (Chinese)
- [Skill catalog](skills/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Release notes](https://github.com/rumoii/rumo-engineering-skills/releases/latest)

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
