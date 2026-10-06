# Backup Coverage And Consistency

## A Lightweight Manifest

Use the current task or service documentation to answer these questions; do not create a parallel host-state database.

| Item | Record |
| --- | --- |
| Service and owner | Actual installation, service identity, and configuration/data owner |
| Sources and coverage | Exact directories, files, database exports, named volumes, bind mounts, and required metadata |
| Exclusions | Regenerable caches/artifacts and deliberately omitted data, with consequences |
| Consistency | Supported online backup/export, application quiescing, or authorized downtime |
| Storage and custody | Destination, access controls, encryption for secret-bearing off-host data, and recovery-key responsibility |
| Backup evidence | Snapshot/archive identity, completion time, result, and applicable checks |
| Recovery | Required versions/credentials, restore target/method, and test state for each claim |

Never insert passwords, tokens, private keys, or configuration secret values in the manifest. A path or responsibility can describe credential recovery without disclosing the credential.

## Discover Coverage From The Service

Inspect existing service declarations, configuration ownership, backup rules, and declared storage. Account for bind mounts outside the installation tree, external volumes, configuration overrides, and state created under the runtime account. Do not assume backing up a Compose file includes its volume data.

Classify each item as needing backup, safely rebuildable, or deliberately excluded. Git can preserve non-secret deployment definitions; it is not a complete backup of sessions, databases, secret files, or volume contents. A local configuration copy, provider snapshot, and independent backup can be complementary; document their consistency and failure coverage rather than treating one as universal.

Establish the requested recovery point and acceptable downtime when they affect method selection. For scheduled backups, determine retention, failure visibility, and checks for a backup job that stops running. These choices do not authorize creating schedules or external alert channels on their own.

## Consistent Collection

Use the database's native backup/export mechanism or another documented consistency method. For multi-file or multi-service state, identify which writes need quiescing and how the capture stays consistent across dependent data. Filesystem snapshots alone do not establish application consistency.

If stopping a service is necessary, ensure it is authorized and define how to resume it after success or failure. When permission or a required tool is unavailable, report the limitation; do not create an incomplete backup and label it complete.

## Protection And Checks

Resolve the destination and its access controls before writing. Use an existing authorized backup tool and avoid outputting contents for inspection. Server-side SSH configuration backups can contain host private keys and must remain in restricted custody. Exporting secret-bearing data requires explicit destination authorization and encryption; store recovery keys separately from the failure domain they unlock.

Choose a backup format or tool that preserves required Linux ownership, permissions, symlinks, and any required ACLs or extended attributes. Do not unpack onto an ordinary Windows directory and assume those restore attributes survive. Encrypt sensitive payloads before they leave the protected host, and keep decryption material out of archives, command arguments, logs, and ordinary task records.

Check exit status and partial-failure indications, selected source coverage, backup contents through safe metadata, permissions, and the tool's integrity verification. A checksum confirms bytes relative to a known expected checksum; it does not show the source set was complete or consistent.

For restic, the default `check` validates repository structure, while `--read-data` or supported subsets read stored data. Select the required check with its time/bandwidth cost in view. Neither proves application recovery; preserve that separate test state.

## Authorized Rotation

Read the workspace's fixed destination, backup scopes, naming convention, and authorized retention policy. Reuse an applicable existing independent backup method unless the task or workspace explicitly selects another. Do not impose a personal path or retention count through this shared skill.

For a policy that retains the latest version on the source host and historical versions locally:

1. Create a distinct new version using the supported consistency method; preserve the previous version while work is in progress.
2. Verify creation, coverage, and the tool's applicable integrity checks. Transfer the protected payload to the approved independent destination and verify the transferred backup's integrity/readability and the availability of its decryption material. Record exactly what was checked; this does not require a full service restore on every backup.
3. Before removing an old source-host version, verify that its corresponding independent copy is also available and usable. If it was never exported, preserve it independently first. A new backup does not recreate an old historical version.
4. Remove only the superseded versions of that same backup scope under the authorized root. Identify exact absolute paths, confirm their ownership and contents, and inspect symlinks/mount boundaries immediately before deletion. Use [Filesystem Safety](../../rumo-filesystem-safety/SKILL.md); do not sweep a parent directory, other scopes, or legacy backups outside the policy.
5. Record new identities/locations, checks, removed versions, and any remaining state in existing task or host documentation. The retention count describes a successfully completed rotation, not a reason to delete the last usable backup after a failure.

Failure to create, encrypt, transfer, or verify either required independent copy stops old-version deletion. A failed or partial deletion is reported without retrying against a broader path. This policy does not authorize deleting local history, repository repair, or restoring over live data. Without an explicit rotation policy, obtain deletion authorization separately.

## Sources

- [restic backup coverage](https://restic.readthedocs.io/en/stable/040_backup.html): exclusions, results, and snapshot creation.
- [restic repository checks](https://restic.readthedocs.io/en/stable/045_working_with_repos.html#checking-integrity-and-consistency): structural checks and stored-data reads.
