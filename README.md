# Rumo Engineering Skills

English | [简体中文](README.zh-CN.md)

Reusable Codex, Claude Code, and agent skills that are independent of a specific company, product, repository layout, host, or deployment environment.

This is the public upstream repository for the `rumo-*` skill namespace. The
skills are suitable for individual, team, and enterprise engineering workflows,
but they do not contain organization-specific operating knowledge.

Project-specific repository names, component inventories, hosts, service names, install roots, and credentials belong in a local profile or an optional private profiles checkout. Use the bundled `rumo-project-profile` initializer to create a local profile; set `RUMO_SKILL_PROFILES_REPO` only when using a shared private checkout.

```powershell
py -3 skills\rumo-project-profile\scripts\init_profile.py --profile my-project
```

```bash
python3 skills/rumo-project-profile/scripts/init_profile.py --profile my-project
```

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

- `rumo-project-profile`: resolves and validates private project configuration for other skills.
- `rumo-bug-root-cause`: evidence-led defect diagnosis across source, runtime, data, middleware, deployment, and clients.
- `rumo-coding-guidelines`: baseline constraints for minimal, path-grounded, verified code changes.
- `rumo-http-api`: compatible, secure, retry-safe, bounded, and operable HTTP/JSON API design and review.
- `rumo-code-review`: one-pass read-only engineering review.
- `rumo-review-fix-loop`: explicit iterative review, repair, verification, and re-review.
- `rumo-change-verification`: exact change-scope inspection and smallest sufficient checks.
- `rumo-test-evidence`: risk-based test and acceptance evidence planning.
- `rumo-lifecycle-safety`: safe ownership, retry, cancellation, timeout, shutdown, and cleanup.
- `rumo-interface-evolution`: compatible API, message, configuration, and persisted-format evolution.
- `rumo-database-change-safety`: bounded database change planning, authorization, backup, verification, and rollback.
- `rumo-repository-gates`: deterministic repository-owned CI and static checks.
- `rumo-engineering-decision`: durable records for material engineering decisions.
- `rumo-find-simplifications`: evidence-led discovery of removable engineering complexity.
- `rumo-prose-standard`: prose quality for code, diagnostics, logs, repository docs, prompts, and UI strings.
- `rumo-daily-report`: cross-session incremental Chinese daily reports in a date-based TXT file.
- `rumo-git-commit`: commit, branch landing, history cleanup, release, and push workflow following repository conventions.
- `rumo-frontend-dev`: local frontend startup, proxy, port, certificate, and runtime troubleshooting.
- `rumo-frontend-ui`: page development, component reuse, layout consistency, and browser QA.
- `rumo-browser-evidence`: traceable screenshots, DOM evidence, state sequences, and optional GIFs.
- `rumo-incremental-deploy`: profile-driven bounded deployment planning and guidance with backup, verification, and rollback.
- `rumo-offline-delivery-audit`: offline artifact integrity, provenance, install, rollback, and acceptance limits.
- `rumo-old-coder`: evidence-first high-assurance development through an approved specification and reproducible gauntlet.
- `rumo-remote-memory-inspection`: read-only remote Linux memory and performance evidence.
- `rumo-linux-hardware-inventory`: read-only Linux hardware inventory and concise handoff.
- `rumo-document-writing`: formal Word-document authoring and quality control.
- `rumo-engineering-topology-diagram`: architecture and topology fact models, preview, export, and validation.
- `rumo-mermaid-diagram`: Mermaid business flowcharts with preview and image export.
- `rumo-imagegen`: one-image generation through a configured OpenAI-compatible endpoint.
- `rumo-insight`: evidence-backed local Codex work analysis.

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

The validator checks naming, frontmatter, UI metadata, relative links, JSON syntax, catalog inventories, forbidden project-specific terms, and tracked credential files.

## Install

Run the installer from a stable checkout. It validates before replacing links and manages only `rumo-*` entries, preserving unrelated skills.

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

Default remote: `https://github.com/rumoii/rumo-engineering-skills.git`.

The PowerShell installer creates junctions on native Windows. The shell installer creates symbolic links on macOS, Linux, and WSL. Re-run the installer after adding, removing, or renaming skills.

## Security

- Never commit `pwd.md`, credential `.env` files, tokens, private keys, or certificates containing private material.
- Never print secret values from installers, profile resolution, evidence scripts, tests, or reports.
- Keep project-specific profiles private and verify remote visibility before every push.
- Access only localhost or explicitly identified development/test environments by default. Production requires exact authorization and remains read-only unless the user separately authorizes a mutation.

See [SECURITY.md](SECURITY.md) for private vulnerability and disclosure
reporting. Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
