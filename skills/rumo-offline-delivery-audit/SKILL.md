---
name: rumo-offline-delivery-audit
description: Use when building, reviewing, or accepting an offline delivery package, deployment archive, image bundle, or field-installation kit. Verify artifact integrity, dependency closure, source provenance, installer and rollback behavior, embedded documentation, and the exact distinction between source checks, package checks, isolated installation, and real target acceptance. Do not use for bounded online deployment to an existing environment.
---

# Rumo Offline Delivery Audit

Treat the deliverable as the artifact the customer receives, not as a source directory that happened to build. Keep package evidence separate from field acceptance.

Do not deploy to a customer, shared environment, or remote host unless the user explicitly requests that write. Building or auditing a local artifact does not authorize external publication.

## Establish The Delivery Requirements

Before building or auditing, identify:

- Product, version, target operating system, CPU architecture, container runtime, and installation topology.
- Exact source repositories, revisions, submodules, vendored inputs, and whether any source tree is dirty.
- Expected archive format, package root, installation entry point, upgrade path, backup path, rollback path, and health check.
- Required third-party images, packages, runtimes, licenses, manuals, sample configuration, and database baselines.
- Which claims require native Windows, Docker Desktop, PowerShell, Runner, PSModel, hardware, customer data, or a field network.

Stop and request the missing value when the target platform, package entry point, or acceptance claim would materially change the artifact. Do not infer those facts from a previous package name.

## Build The Actual Artifact

Use the repository's maintained packaging entry point when one exists. Inspect it before execution and record every source or artifact it consumes. Do not replace a maintained packager with an ad hoc archive command merely to produce a file.

Place generated output in the repository's documented artifact directory or another explicit output directory. Confirm generated output is ignored when that is repository policy; do not change ignore rules solely to conceal release content.

Record at least:

- Artifact file name, byte size, creation time, and external SHA-256.
- Source repository path, commit id, branch, dirty state, and relevant build-tool versions.
- Exact packaging command and its exit status.
- Image names, immutable digests when available, and declared platforms.
- Any generated configuration or embedded secret placeholders. Never package real credentials.

If source is dirty, enumerate the included changes or build from a staged snapshot. Do not describe an artifact as reproducible from a commit when it also contains unrecorded working-tree content.

## Audit Archive Integrity

Inspect the completed archive, not only its staging directory:

- List every archive member and reject absolute paths, parent traversal, unsafe links, duplicate destinations, unexpected executables, and temporary build residue.
- Extract into a new temporary directory and verify the result without depending on files outside that directory.
- Verify an internal checksum manifest for package members and a separately stored checksum for the outer archive.
- Compare the packaged manuals, scripts, Compose files, configuration, migrations, and image inventory with the source inputs used for the build.
- Rebuild and re-audit after any packaged file or embedded manual changes. A checksum from an earlier build is stale.

Common checksum commands:

macOS/Linux/Git Bash/WSL:

```bash
sha256sum <artifact>        # Linux/Git Bash/WSL
shasum -a 256 <artifact>    # macOS
tar -tf <artifact.tar.gz>
unzip -l <artifact.zip>
```

Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 <artifact>
tar -tf <artifact.tar.gz>
tar -tf <artifact.zip>
```

Use the archive tool maintained by the product when these commands do not support the actual format.

## Prove Dependency Closure

An offline package must not require an undeclared network fetch during installation or startup.

- Enumerate container images and verify the saved bundle contains each required tag or digest for the target architecture.
- Render Compose configuration and reject active `build` entries, unresolved variables, undeclared bind-mount sources, and images absent from the bundle.
- Inspect installers and scripts for package-manager downloads, remote URLs, Git clones, image pulls, license lookups, or dynamic dependency resolution.
- Verify required binaries and runtimes exist inside the package or are explicitly classified as customer prerequisites.
- Separate package-provided components from customer-provided infrastructure and optional integrations.

If a networked build is required, that does not prove offline installation. Repeat the install proof in an isolated environment with pulling and external downloads disabled.

## Verify Installation, Upgrade, And Rollback

Execute the packaged entry point from the extracted artifact. Verify the operating system and shell syntax that the customer will use.

Check:

1. Prerequisite detection fails with an actionable message.
2. Fresh installation reaches documented health checks.
3. Re-running the installer is safe or explicitly rejected.
4. Upgrade preserves documented data and configuration.
5. Backup files are created before destructive replacement.
6. Rollback restores the previous usable state.
7. Cleanup affects only package-owned temporary and retired files.
8. Logs identify the failing phase without exposing credentials.

Package parsing, shell syntax checks, and Linux container tests do not prove native Windows behavior. Record whether PowerShell 5.1 or 7, Docker Desktop, filesystem permissions, services, reboots, antivirus controls, and actual field hardware were exercised.

## Keep Documentation Synchronized

The package's installation, upgrade, rollback, troubleshooting, and acceptance instructions must match the final artifact. Audit shared manuals and SOPs included by the packager, not only version-specific guides.

Require each documented file name, command, port, path, service, container, credential placeholder, scheduler, and health endpoint to exist in the final package or customer prerequisite list. Rebuild the package after documentation corrections and verify the rebuilt hashes.

## Report Evidence By Layer

Use these result classes:

| Layer | What qualifies |
| --- | --- |
| Source | Static inspection, unit tests, build results, source configuration, and revision evidence |
| Package | Final archive listing, extraction, hashes, embedded assets, platform metadata, and packaged entry-point checks |
| Isolated install | Installation and startup from the final archive with external downloads disabled |
| Field | Native target operating system, real runtime, hardware, customer topology, integrations, and business acceptance |

For each acceptance claim, report `passed`, `failed`, `blocked`, or `not run`, followed by the command or artifact that supports it. Never promote source or package evidence to field acceptance.

Close with the final artifact path, external checksum, source revisions, target platform, packaging command, checks actually run, installation result, rollback result, unresolved risks, and the exact remaining field checks.

## Related Skills

- Use [`rumo-change-verification`](../rumo-change-verification/SKILL.md) to verify the source and packaging-code change scope before release.
- Use [`rumo-database-change-safety`](../rumo-database-change-safety/SKILL.md) when the package installs, migrates, repairs, resets, or rolls back an existing database.
- Use [`rumo-incremental-deploy`](../rumo-incremental-deploy/SKILL.md) for bounded online deployment to an existing development or test environment; it does not establish offline-package acceptance.
