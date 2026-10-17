# Rumo Engineering Skills

English | [简体中文](README.zh-CN.md)

A compact set of engineering skills for Codex, Claude Code, and other agents that load `SKILL.md` directories. The skills carry no company, product, host, or deployment specifics; private project facts live in optional local profiles.

## The Workflow

```text
clarify -> plan -> test -> verify -> review -> git-commit
```

Each step is a skill. Use only the ones a task needs: a one-line fix goes straight to coding and verification, while a vague feature request starts with `rumo-clarify`.

| When you want to | Codex | Claude Code |
| --- | --- | --- |
| Pin down a vague request | `$rumo-clarify` | `/rumo-clarify` |
| Break agreed work into verifiable tasks, then work them one by one | `$rumo-plan` | `/rumo-plan` |
| Implement test-first | `$rumo-test` | `/rumo-test` |
| Find the cause of a bug, read-only | `$rumo-debug` | `/rumo-debug` |
| Check the change before calling it done | `$rumo-verify` | `/rumo-verify` |
| Review a diff without editing | `$rumo-review` | `/rumo-review` |
| Commit, land, push, or open a pull request | `$rumo-git-commit` | `/rumo-git-commit` |

Clients also pick skills automatically from their descriptions; naming one is optional except for manual-only skills. [Worked examples](GETTING_STARTED.md#完整案例) follow three requests from prompt to delivery.

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

Not installed by default. Add them with `-Extras` (PowerShell) or `--extras` (shell).

| Skill | Purpose |
| --- | --- |
| `rumo-diagram` | Mermaid business flowcharts and confirmed engineering topology diagrams with preview and export |
| `rumo-document-writing` | Formal Word delivery documents |
| `rumo-offline-delivery-audit` | Offline package integrity, provenance, installation, rollback, and acceptance limits |
| `rumo-daily-report` | Incremental Chinese daily reports in a dated text file (manual only) |
| `rumo-linux-inspect` | Read-only Linux hardware inventory or memory inspection (manual only) |
| `rumo-imagegen` | One image through a user-configured OpenAI-compatible endpoint (manual only) |

## Install

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

The installer validates the repository, then links the default skills into every detected client (Codex, Claude Code, and the shared `~/.agents` directory). It manages only `rumo-*` links and leaves other skills alone. Start a new agent session afterwards so the client reloads its skill list. [GETTING_STARTED.md](GETTING_STARTED.md) covers client detection and profiles.

Manage extras:

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

Optional environment variables: `RUMO_SKILLS_REPO` (stable checkout), `RUMO_SKILLS_REMOTE` (clone URL), `RUMO_SKILL_PROFILES_REPO` (private profiles checkout), `RUMO_PROJECT_PROFILE` (explicit profile ID), and `CODEX_HOME`, `CLAUDE_HOME`, `AGENTS_HOME` (custom client homes). Pass `-ProfilesRepo <path>` or `--profiles-repo <path>` to persist a profiles checkout in `~/.rumo-engineering-skills/config.json`.

### Install With An Agent

To have an agent install the skills, give it this prompt:

```text
Install the skills from https://github.com/rumoii/rumo-engineering-skills by following its README.
1. Clone it if it is not present, run the installer with --dry-run (-DryRun on Windows), and show me what it would change.
2. Run the installer without --baseline and report which clients were linked.
3. Ask me before writing to my user-level CLAUDE.md or AGENTS.md. Only if I agree, rerun it with --baseline (-Baseline) and show me the block it added.
4. List the files that changed and remind me to start a new session.
```

An agent installing from this README without that prompt follows the same rule: it never adds `--baseline` or `-Baseline` without the user's explicit agreement, because that edits the user's own instruction files.

### Claude Code Plugin

Claude Code users can install the default skills as a plugin instead, without a clone. In a session (Claude Code 2.1.275 or later):

```text
/plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills
```

From a shell (Claude Code 2.1.292 or later), use `claude plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills`. On older versions, add the marketplace first:

```bash
claude plugin marketplace add rumoii/rumo-engineering-skills
claude plugin install rumo-engineering-skills@rumo-engineering-skills
```

Plugin skills carry a prefix, such as `rumo-engineering-skills:rumo-clarify`. The plugin covers Claude Code only and has no extras; other clients use the installer.

Choose one method per machine. If the installer already linked skills into `~/.claude/skills`, adding the plugin loads every skill twice. To update the plugin, run `claude plugin marketplace update rumo-engineering-skills`, then `claude plugin update rumo-engineering-skills@rumo-engineering-skills`, and start a new session.

### Always-On Baseline

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

## Project Profiles

Profiles are optional. Repository names, component inventories, hosts, service names, install roots, and credentials belong in a local profile or a private profiles checkout, never in this repository.

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

## Validate

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

These commands check the repository, not an installation. After installing, check the links (`ls -l ~/.claude/skills`) or `claude plugin list`, then start a new session and invoke a skill by name, such as `/rumo-verify` or, for the plugin, `/rumo-engineering-skills:rumo-verify`. A successful explicit call shows that the client loaded the skill; it does not show that the client will choose it automatically.

## Security

- Never commit passwords, credential files, tokens, private keys, or certificates with private material.
- Never print secret values from installers, profile resolution, scripts, tests, or reports.
- By default, access only localhost or environments explicitly identified as development or test. Production needs exact authorization and stays read-only unless a change is separately approved.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules.

## License

MIT. See [LICENSE](LICENSE).
