# Rumo Engineering Skills

English | [简体中文](README.zh-CN.md)

Reusable Codex, Claude Code, and agent skills that are independent of a specific company, product, repository layout, host, or deployment environment.

This is the public upstream repository for the `rumo-*` skill namespace. The
skills are suitable for individual, team, and enterprise engineering workflows,
but they do not contain organization-specific operating knowledge.

## Start by scenario

Use the matching instruction in your agent session after installation.

| Scenario | Goal | Codex | Claude Code |
| --- | --- | --- | --- |
| Debug | Trace the current issue to an evidence-backed cause through read-only investigation. | `$rumo-debug Investigate the current issue read-only and report the cause with evidence.` | `/rumo-debug Investigate the current issue read-only and report the cause with evidence.` |
| Review | Review the current uncommitted changes once without editing files. | `$rumo-code-review Review the current uncommitted changes without editing files.` | `/rumo-code-review Review the current uncommitted changes without editing files.` |
| Implement | Implement the requested feature with minimal changes and focused verification. | `$rumo-coding-guidelines Implement the requested feature with minimal changes and focused verification.` | `/rumo-coding-guidelines Implement the requested feature with minimal changes and focused verification.` |
| Verify | Check the exact current change and report the checks actually run. | `$rumo-change-verification Verify the current change and report the checks actually run.` | `/rumo-change-verification Verify the current change and report the checks actually run.` |
| Deploy | Plan bounded artifact deployment to an existing development or test environment using the selected profile. | `$rumo-incremental-deploy Use the selected profile to plan artifact deployment to the existing development or test environment without executing it.` | `/rumo-incremental-deploy Use the selected profile to plan artifact deployment to the existing development or test environment without executing it.` |

## Getting started

If you have just cloned this repository, read [GETTING_STARTED.md](GETTING_STARTED.md).
It covers installation, validation, direct skill invocation, optional local Profiles,
and credential boundaries.

Clone the public repository first:

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

If a client already has a same-name `rumo-*` link from another checkout, the
installer stops before changing any client. Use `-ReplaceForeignLinks` or
`--replace-foreign-links` only when you intentionally want to switch that
client to this public checkout.

The installers manage only `rumo-*` links and preserve skills from other
namespaces and sources. Start a new agent session after installation so the
skill catalog is reloaded.

## Skill catalog

- `rumo-project-profile`: resolves and validates private project configuration for other skills (manual only).
- `rumo-clarify`: lightweight requirement clarification: one round of questions with recommended answers, critical decisions never defaulted.
- `rumo-debug`: evidence-led defect diagnosis across source, runtime, data, middleware, deployment, and clients.
- `rumo-coding-guidelines`: baseline constraints for minimal, path-grounded, verified code changes.
- `rumo-http-api`: compatible, secure, retry-safe, bounded, and operable HTTP/JSON API design and review.
- `rumo-code-review`: one-pass read-only engineering review.
- `rumo-review-fix-loop`: explicit iterative review, repair, verification, and re-review.
- `rumo-change-verification`: exact change-scope inspection and smallest sufficient checks.
- `rumo-test`: risk-based test and acceptance evidence planning.
- `rumo-lifecycle-safety`: safe ownership, retry, cancellation, timeout, shutdown, and cleanup.
- `rumo-interface-evolution`: compatible API, message, configuration, and persisted-format evolution.
- `rumo-database-change-safety`: bounded database change planning, authorization, backup, verification, and rollback.
- `rumo-filesystem-safety`: tiered file and directory deletion with boundary checks and no ad hoc backups.
- `rumo-repository-gates`: deterministic repository-owned CI and static checks.
- `rumo-plan`: durable records for material engineering decisions.
- `rumo-find-simplifications`: evidence-led discovery of removable engineering complexity.
- `rumo-prose`: prose quality for code, diagnostics, logs, repository docs, prompts, and UI strings.
- `rumo-daily-report`: cross-session incremental Chinese daily reports in a date-based TXT file (manual only).
- `rumo-git-commit`: commit, branch landing, history cleanup, release, and push workflow following repository conventions.
- `rumo-frontend`: page development, local dev-server troubleshooting, and requested browser evidence (optional extra).
- `rumo-incremental-deploy`: profile-driven bounded deployment planning and guidance with backup, verification, and rollback.
- `rumo-remote-ops-safety`: lightweight remote Linux queries and bounded SSH changes with access protection and execution reconciliation.
- `rumo-linux-service-deploy`: Linux service installation, upgrade, and removal with recovery preparation and functional acceptance.
- `rumo-backup-restore`: explicit backup coverage, consistency, protected storage, and layered recovery verification.
- `rumo-offline-delivery-audit`: offline artifact integrity, provenance, install, rollback, and acceptance limits.
- `rumo-linux-inspect`: read-only Linux hardware inventory or memory inspection (optional extra, manual only).
- `rumo-document-writing`: formal Word-document authoring and quality control.
- `rumo-diagram`: Mermaid business flowcharts and confirmed topology diagrams with preview and export (optional extra).
- `rumo-imagegen`: one-image generation through a configured OpenAI-compatible endpoint (manual only).
- `rumo-insight`: evidence-backed work analysis of local Codex session history (Codex data only; manual only).

## Validate

```powershell
py -3 scripts\verify_skills.py
py -3 -m unittest discover -s scripts\tests -p "test_*.py"
```

```bash
python3 scripts/verify_skills.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

Run the focused helper-script suite before contributing or releasing:

```powershell
py -3 scripts\run_auxiliary_tests.py
```

```bash
python3 scripts/run_auxiliary_tests.py
```

On Windows without the `py` launcher, replace `py -3` with `python`.

The validator checks naming, frontmatter (including the common Agent Skills length limits), UI metadata, relative links, JSON syntax, catalog inventories, likely secrets, and tracked credential files. To block private project vocabulary, list terms in `~/.rumo-engineering-skills/forbidden-terms.txt` (or the file named by `RUMO_FORBIDDEN_TERMS_FILE`), one per line, with a `re:` prefix for regular expressions. Keep that file out of the repository; a match reports only the file path, never the term.

Clients select skills from `SKILL.md` `name` and `description` only. `agents/openai.yaml` is optional Codex UI metadata that other clients ignore.

## Install

Run the installer from a stable checkout. It validates before replacing links and manages only `rumo-*` entries, preserving unrelated skills. It syncs only detected clients (Codex, Claude Code, and the shared `~/.agents` directory); see [GETTING_STARTED.md](GETTING_STARTED.md) for detection rules. If no client is detected, it fails without changing anything.

```powershell
.\install.ps1 -NoPull
```

```bash
./install.sh --no-pull
```

Optional environment variables:

- `RUMO_SKILLS_REPO`: stable local checkout of this repository.
- `RUMO_SKILLS_REMOTE`: clone URL override.
- `RUMO_SKILL_PROFILES_REPO`: private project profiles checkout.
- `RUMO_PROJECT_PROFILE`: explicit profile ID when automatic matching is ambiguous.
- `CODEX_HOME`, `CLAUDE_HOME`, `AGENTS_HOME`: custom client homes.

To persist a private Profiles checkout for future resolver calls, pass
`-ProfilesRepo <path>` to the PowerShell installer or
`--profiles-repo <path>` to the shell installer. The path is stored in the
user-level Rumo configuration file; credentials remain outside this repository.
The configuration file is `~/.rumo-engineering-skills/config.json`.

Default remote: `https://github.com/rumoii/rumo-engineering-skills.git`.

The PowerShell installer creates junctions on native Windows. The shell installer creates symbolic links on macOS, Linux, and WSL. Re-run the installer after adding, removing, or renaming skills.

## Optional project profiles

Profiles are optional; use them when a task needs private project configuration.

Project-specific repository names, component inventories, hosts, service names, install roots, and credentials belong in a local profile or an optional private profiles checkout. Use the bundled `rumo-project-profile` initializer to create a local profile; set `RUMO_SKILL_PROFILES_REPO` only when using a shared private checkout.

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

## Security

- Never commit `pwd.md`, credential `.env` files, tokens, private keys, or certificates containing private material.
- Never print secret values from installers, profile resolution, evidence scripts, tests, or reports.
- Keep project-specific profiles private and verify remote visibility before every push.
- Access only localhost or explicitly identified development/test environments by default. Production requires exact authorization and remains read-only unless the user separately authorizes a mutation.

See [SECURITY.md](SECURITY.md) for private vulnerability and disclosure
reporting. Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
