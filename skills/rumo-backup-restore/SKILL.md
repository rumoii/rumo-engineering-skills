---
name: rumo-backup-restore
description: Use when planning or performing Linux host configuration or service-data backups and restores. Define coverage, consistency, protected storage, and recovery evidence. Do not treat a backup file or provider snapshot as verified service recovery; use rumo-database-change-safety for database writes.
---

# Rumo Backup Restore

Make backup coverage and recovery results explicit. A successful archive command, integrity check, file restore, and working restored service establish different claims.

## Define The Backup

Read the workspace rules, local host record, existing backup configuration, and service documentation. Identify what must survive the loss of the service or host: configuration, persistent data, required version information, and a safe way to regain credentials. Do not assume a conventional home directory or volume contains everything.

Use a lightweight manifest in the existing task or service documentation. Record service/owner, source locations, included and excluded content, consistency method and downtime if needed, destination/access protection, backup identity/time/result, integrity checks, and recovery prerequisites/results. No fixed schema or separate inventory is required. Read [backup coverage and consistency](references/backup-coverage-and-consistency.md) before preparing a backup.

Record credential locations and recovery responsibilities without values. Secret-bearing backups require an explicitly authorized restricted destination and encryption when leaving the protected host; never place their contents in chat, Git, or ordinary task evidence. Keep client private keys in their existing custody. Ensure recovery credentials and decryption material remain available if the source host is lost.

Use the task's approved destination and retention policy first. Otherwise reuse an applicable authorized independent backup destination, then a workspace-designated local destination. If none is available, report the gap; a protected server-side rollback copy may still be useful, but does not establish host-loss recovery. Read-only queries do not require backups.

## Back Up And Verify

- Existing authorization may cover the backup steps required by a task. Establish destination, scope, privileges, and any downtime before execution; do not create backup schedules, buy storage, or stop services outside that scope.
- For SSH access use [Remote Ops Safety](../rumo-remote-ops-safety/SKILL.md), reusing verified session facts. For private automation parameters use [Project Profile](../rumo-project-profile/SKILL.md) only when needed; explicit documentation can supply the facts.
- Use the application's or database's supported consistency mechanism. Copying live database files alone does not establish a recoverable backup. Do not bypass denied reads, silently omit required data, or expose secrets to inspect a backup.
- Verify command results, coverage, relevant contents/metadata, and the available integrity checks. Distinguish structural checks from reading actual stored data, and both from a service restore.
- A backup kept only on the source host cannot cover host loss. State which failure the selected configuration copy, snapshot, or independent backup can address.
- Follow an explicitly authorized rotation policy without repeatedly requesting the same approval. For a latest-on-host/history-off-host policy, verify the new backup and its independent copy, and ensure each old version has a verified independent copy before removing it. Rotate only backups of the same scope; see the coverage reference for deletion boundaries.
- On failure, partial coverage, or an unverified replacement, retain the last usable backup and report the gap. Without an explicit rotation policy, backup permission does not authorize pruning; repository repair and live restore remain separate scopes.

## Restore Safely

Read [restore and verification](references/restore-and-verification.md) before any restore. Prefer an isolated directory or test environment for recovery verification, with enough separation to prevent writes to the live service, shared data, external integrations, or credentials.

Before overwriting an existing destination, establish the exact target and data scope, current-state protection, compatible version, credential availability, and explicit restore authorization. Recheck the destination immediately before writing. A request to verify a backup does not authorize replacing the running service.

Use [Database Change Safety](../rumo-database-change-safety/SKILL.md) for a database restore or other persistent database write and [Filesystem Safety](../rumo-filesystem-safety/SKILL.md) if cleanup/deletion is required. Restore authorization does not expand to unrelated paths or data.

Verify restored content, ownership/permissions, applicable application startup, and a real operation in the isolated environment. Record the time or recovery scope only when measured. A live service cutover is a separately scoped service change.

## Report And Maintain

Use `not tested`, `partially verified`, `passed`, or `failed` for each claim. Include backup identity and location, coverage/exclusions, consistency, integrity checks actually run, restored target, functional result, and missing evidence. Do not label the whole recovery passed from a file listing or checksum.

Update affected backup/recovery facts in the designated local host record with verification time and evidence source. Keep process evidence in its authorized task location; do not duplicate the inventory or export secret-bearing archives into it.
