# Restore And Verification

## Establish The Target Before Writing

Identify the source backup, its creation time, coverage, consistency, and applicable version. Resolve the destination host/environment and absolute path, volume, or database. Inspect symlinks, mounts, existing contents, and service ownership that could redirect or widen the write.

Prefer a fresh isolated target for a restore test. Check that it is not a shared live volume or database and that test startup cannot send real messages, run production jobs, or modify external systems. Use supported disabled/test integrations and appropriate test credentials; do not copy live secrets merely to make a smoke test easier.

For a live overwrite, state what will be replaced, what post-backup writes may be lost, and how current state is protected. Require explicit authorization for that scope before writing. Existing install or backup authorization does not silently include replacing newer data. A provider snapshot restore can replace the whole machine; inspect its effect on all services and access paths.

If required data, a compatible runtime, a trustworthy backup, access rights, or decryption material is unavailable, stop the restore mutation and report the missing prerequisite. Do not attempt credential recovery or bypass controls.

## Restore In The Appropriate Layer

Follow the selected backup tool and application procedure. Recheck target resolution just before writing, restore the agreed content, and establish the required ownership and permissions without broad recursive permission changes over unrelated paths.

When returning an independent backup to a host, receive it in an approved temporary recovery location and verify identity, integrity, decryption, and metadata before placing selected content at the live destination. Upload permission alone does not authorize extraction over existing files, database imports, or service cutover.

Use [Database Change Safety](../../rumo-database-change-safety/SKILL.md) before importing or restoring a persistent database, including one on a test host. Use [Remote Ops Safety](../../rumo-remote-ops-safety/SKILL.md) for access changes or uncertain remote execution, and [Linux Service Deploy](../../rumo-linux-service-deploy/SKILL.md) when activating the restored service is in scope.

Stop dependent steps after an error. Inspect what was written; do not retry against a broader directory or another database. Preserve source backups and the protected current state until acceptance. Any cleanup remains bounded to authorized targets.

## Evidence Layers

| Claim | Evidence | Still unproven |
| --- | --- | --- |
| Required data was captured | Manifest reconciled with safe backup contents/metadata | Consistency, complete readability, or service recovery |
| Backup storage passed integrity checks | Actual tool check, with its coverage recorded | Correct source selection and a usable application |
| Selected files/data were restored | Restore command result, expected contents, ownership/permissions, appropriate data checks | Startup and real function |
| Restored service works | Compatible runtime, startup/log checks, and a real operation using restored state | Untested data, integrations, or live cutover |
| Recovery time meets the requirement | Timed execution of the agreed recovery scope | Other hosts or larger datasets |

Use `not tested`, `partially verified`, `passed`, or `failed` per claim. If only configuration files were restored, report configuration recovery, not full service recovery. Integrity success with an untested restore remains an untested restore.

Record the source backup and target identity, time, actual commands/results, tested function, and remaining gaps without secret content. Update the existing host/service record, not a duplicate inventory. Cut over to a live restored service only within an explicitly authorized service-change task.

## Source

- [restic restoring from backup](https://restic.readthedocs.io/en/stable/050_restore.html): explicit restore targets and selecting snapshot contents.
