---
name: rumo-project-profile
description: Resolve and validate optional private project profiles for other Rumo skills. Use explicitly when a workflow needs project-specific repository, frontend, backend, runtime, data, document, or credential configuration.
---

# Project Profile

Use this infrastructure skill when a reusable skill needs project-specific facts that must not be embedded in the public capability instructions. A profile is optional and can be created before the project or its Git repository exists.

## Create a local profile

The public skill includes a generic template and an initializer. It creates a local profile under the user's home directory; it does not create a Git repository, inspect the current Git repository, or write credentials.

```powershell
py -3 <skill-dir>\scripts\init_profile.py --profile my-project
py -3 <skill-dir>\scripts\verify_profile.py --profiles-root "$env:USERPROFILE\.rumo-skill-profiles"
```

```bash
python3 <skill-dir>/scripts/init_profile.py --profile my-project
python3 <skill-dir>/scripts/verify_profile.py --profiles-root "$HOME/.rumo-skill-profiles"
```

The initializer creates `project.json`, the optional section templates, a `references/` directory, and a credentials example with empty values. Fill in repository paths, commands, runtime facts, and references only as they become known. Empty arrays and partially completed sections are valid.

Teams may place the same profile directory in a private checkout when they need to share it. That checkout is optional; individual users can keep profiles local.

## Resolution

Run `scripts/resolve_profile.py` from this skill directory. The resolver checks, in order:

1. `--profiles-root`.
2. `RUMO_SKILL_PROFILES_REPO`.
3. The profiles repository persisted by the installer in `$HOME/.rumo-engineering-skills/config.json`.
4. A sibling `rumo-skill-profiles` checkout next to the skills repository.
5. `$HOME/.rumo-skill-profiles`.

Select a profile with `--profile`, `RUMO_PROJECT_PROFILE`, or a unique match against the current Git repository name or remote URL. Never guess when multiple profiles match.

```powershell
py -3 <skill-dir>\scripts\resolve_profile.py --cwd <project-path> --section runtime
```

```bash
python3 <skill-dir>/scripts/resolve_profile.py --cwd <project-path> --section runtime
```

The command prints JSON metadata only. It never prints credential values. A missing profile is not an error for a generic workflow: continue from repository discovery and ask only for facts that cannot be established safely.

## Profile Contract

Each profile directory contains `project.json`, `frontend.json`, `backend.json`, `runtime.json`, and `data.json`. Their contents may remain empty until the corresponding project facts exist. `documents.json` is optional. Large project guidance belongs under `references/` and is referenced by relative path from those JSON files.

Credentials may exist only in a local ignored file or a private profiles checkout. Treat `credentials.md`, `credentials.env`, and equivalent files as secrets: load only when the requested operation needs them, never print them, and never copy them into the skills repository, logs, reports, tests, or generated evidence.
