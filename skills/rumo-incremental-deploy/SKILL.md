---
name: rumo-incremental-deploy
description: Use when planning or performing a bounded deployment of selected application artifacts to an existing development or test environment. Resolve build, artifact, destination, service, backup, restart, verification, and rollback commands from an explicit project profile.
---

# Incremental Deploy

Incremental deployment is profile-driven. Do not infer build commands, artifact layout, remote roots, service names, or default hosts from repository names.

Use [`rumo-project-profile`](../rumo-project-profile/SKILL.md) and require a `backend.json` or `runtime.json` section that identifies:

- the build command and working directory;
- source artifacts and their owning modules;
- target environment purpose and host;
- remote destination and backup rule;
- restart or reload command;
- health, log, API, or functional verification;
- rollback command and latest safe rollback point.

## Safety Boundary

- Operate only on an environment explicitly identified as development or test unless the user authorizes a precise production action.
- Produce and review a dry-run plan before copying artifacts or restarting services.
- Build from the exact intended commit and verify artifact hashes.
- Back up every replaced artifact with a collision-safe name.
- Restart only the services that consume the changed artifact.
- Stop on ambiguous module ownership, target paths, service names, failed backup, failed copy, failed restart, or failed health verification.

Run `scripts/incremental_deploy_plan.py --profile <profile-dir> --artifact <file> --host <host> --destination <path> --service <name>` to generate a non-executing plan. The script never connects to a remote host or changes files.

Report source commit, build command, artifact hashes, destination, backup, restarted services, verification, rollback readiness, and any field behavior not exercised.
