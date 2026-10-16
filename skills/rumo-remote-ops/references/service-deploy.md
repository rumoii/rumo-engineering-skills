# Service Deployment

Deliver the requested service behavior through the existing supported deployment method. Installation or a successful start command alone is not acceptance.

## Discover And Bound The Change

- Read workspace rules, the local host record, and existing deployment scripts or runbooks. Discover the OS, service manager, installation owner, current version, configuration, data locations, account, and listeners relevant to the task.
- Follow the session and change rules in [SKILL.md](../SKILL.md) for SSH access and remote change protection; reuse established session facts rather than repeat preflight for each command.
- Establish the requested result and authorization, including any restart, port exposure, privilege change, migration, or data removal. Continue within that scope without repeated confirmation.
- Reuse a working installation and deployment method. Do not install Docker, introduce a public dashboard, or replace an existing deployment stack merely because a generic example does so. Read [deployment and acceptance](deployment-and-acceptance.md) for the selected runtime.

## Prepare Recovery Before Mutation

Identify the before-state and concrete recovery action. First installation may be recovered by stopping and removing only the new service resources while preserving data. Upgrades need a usable old version/configuration and a decision about persistent-data compatibility.

Read [upgrade, rollback, and removal](upgrade-rollback-and-removal.md) for an existing-service change, incompatible migration, failed deployment, or uninstall. Use [backup and restore](backup-restore.md) when recovery requires configuration or persistent-data backups, and [Database Change Safety](../../rumo-database-change-safety/SKILL.md) before database writes. Do not create ad hoc backup files beside application files.

## Execute And Accept

Use the applicable sequence: discovery, scoped plan and authorization, recovery preparation, installation/configuration, start, runtime checks, functional test, and affected-record update. Omit inapplicable steps; a bounded configuration fix does not require reprovisioning the machine.

Before installation, verify the source and intended version; check artifact integrity when distributing a release artifact. Inspect unfamiliar privileged installation scripts and identify side effects instead of executing an unreviewed download blindly.

Accept the service only with evidence for the applicable claims:

- configuration is valid and the effective user, groups, privileges, and secret-file permissions fit the intended access;
- the selected process/unit/container remains running, relevant logs show no unresolved startup failure, and an available health check succeeds;
- expected data paths or volumes are present with correct ownership and persistence;
- listening addresses, firewall/container publication, and external reachability match the requested exposure;
- one real operation succeeds from the intended client surface;
- required startup persistence, resource/log limits, and monitoring or alerting are checked, with missing controls reported.

An available health endpoint does not replace the real operation. Verify startup configuration when persistence is required; claim reboot survival only after an authorized reboot test. Reboot is not a mandatory deployment step.

## Failure And Handoff

Stop dependent mutations on failed validation, backup, installation, startup, or acceptance. Inspect partial effects before retrying. Execute rollback only when already authorized, applicable to current state, and safe for data created since deployment; otherwise preserve the state and present the required action.

Before recreating/replacing a container or switching its mounts, locate and preserve current data that could be lost or hidden. A missing mount alone does not prove the write location. If affected writes cannot be identified or preserved, stop that mutation; service-restart permission does not authorize discarding data. See the upgrade reference for this recovery order.

Report source/version, changed resources, actual checks, functional result, data and exposure boundaries, recovery readiness, and unverified behavior. Update affected facts in the designated local host record with time and evidence, without creating a duplicate inventory.

For uninstall, preserve configuration, persistent data, and credentials by default. Use [Filesystem Safety](../../rumo-filesystem-safety/SKILL.md) when deletion is explicitly in scope. Use [Project Profile](../../rumo-project-profile/SKILL.md) only when private automation parameters are needed; existing explicit documentation can supply the facts.
