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
| Break agreed work into verifiable tasks | `$rumo-plan` | `/rumo-plan` |
| Implement test-first | `$rumo-test` | `/rumo-test` |
| Find the cause of a bug, read-only | `$rumo-debug` | `/rumo-debug` |
| Check the change before calling it done | `$rumo-verify` | `/rumo-verify` |
| Review a diff without editing | `$rumo-review` | `/rumo-review` |
| Commit, land, or push | `$rumo-git-commit` | `/rumo-git-commit` |

Clients also pick skills automatically from their descriptions; naming one is optional except for manual-only skills.

## Default Skills

Installed by default.

| Skill | Purpose |
| --- | --- |
| `rumo-clarify` | One round of short questions with recommended answers when a request is unclear; critical decisions are never defaulted |
| `rumo-plan` | Short spec and verifiable task breakdown, or a durable engineering decision record |
| `rumo-coding-guidelines` | Baseline discipline: real code paths, only requested and necessary work, verified results |
| `rumo-test` | Evidence planning, test-first implementation, and high-assurance spec-and-evidence work |
| `rumo-debug` | Reproduce, localize, and prove a root cause; read-only unless the fix is requested |
| `rumo-verify` | Exact change scope and the smallest sufficient checks before claiming done; building repository gates |
| `rumo-review` | Read-only review, an explicit review-fix loop, or a simplification audit |
| `rumo-git-commit` | Commits, branch landing, history cleanup, releases, and pushes following repository conventions |
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

### Claude Code Plugin

Claude Code users can install the default skills as a plugin instead, without a clone. In a session (Claude Code 2.1.275 or later):

```text
/plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills
```

From a shell, use `claude plugin install rumo-engineering-skills --marketplace rumoii/rumo-engineering-skills`. Plugin skills carry a prefix, such as `rumo-engineering-skills:rumo-clarify`. The plugin covers Claude Code only and has no extras; other clients use the installer.

Choose one method per machine. If the installer already linked skills into `~/.claude/skills`, adding the plugin loads every skill twice. To update the plugin, run `claude plugin marketplace update rumo-engineering-skills`, then `claude plugin update rumo-engineering-skills@rumo-engineering-skills`, and start a new session.

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

## Security

- Never commit passwords, credential files, tokens, private keys, or certificates with private material.
- Never print secret values from installers, profile resolution, scripts, tests, or reports.
- By default, access only localhost or environments explicitly identified as development or test. Production needs exact authorization and stays read-only unless a change is separately approved.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules.

## License

MIT. See [LICENSE](LICENSE).
