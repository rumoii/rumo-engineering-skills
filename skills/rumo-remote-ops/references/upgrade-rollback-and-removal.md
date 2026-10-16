# Upgrade, Rollback, And Removal

## Establish The Recovery Point

Before changing an existing service, record the current usable version/image, selected configuration and overrides, persistent data locations, and a scoped recovery method. Retain the actual old artifact or ensure its verified source remains available. A tag called `previous` or a Git parent is not automatically the deployed version.

Identify whether the change affects only binaries/configuration or also writes durable state. Back up replaced configuration in a designated restricted location when needed. Coordinate database backups and compatibility with [Database Change Safety](../../rumo-database-change-safety/SKILL.md), and backup coverage with [backup and restore](backup-restore.md).

For a first deployment, describe how to stop and remove newly introduced runtime resources while preserving persistent state and unrelated dependencies. An empty pre-install backup is not proof that the entire installation can be undone.

## Upgrade

Use the existing deployment owner and application's supported upgrade sequence. Check runtime/configuration compatibility, migration requirements, dependencies, required downtime, and restart authorization. Configuration and data migration order comes from the application contract, not a generic command list.

Inspect the service before and after each consequential step. If the step fails or its result is uncertain, reconcile state before retrying or continuing. Do not move on to acceptance while a migration is incomplete.

## Failed Deployment And Rollback

Stop dependent mutations and capture bounded, non-secret evidence of what changed and what remains running. Determine whether the prepared recovery still applies.

For a missing or incorrect container mount, inspect actual application paths, mounts, and post-change writes first. Data may be in a writable layer, another volume, or an external store; do not turn one possibility into a fact. Before recreating/removing the current container or switching mounts, preserve any data those operations could destroy or hide with an appropriate consistency method. Locate and protect the writes, resolve any required data-disposition authorization, then repair/recreate and verify. If preservation is unavailable or uncertain, leave the relevant container/state intact and report the prerequisite. Restart authorization alone does not authorize losing the current data copy.

- For a compatible binary/configuration rollback, use the recorded deployed version and the selected configuration baseline, then verify runtime and real function.
- For incompatible data changes, restoring an old image alone may fail or corrupt data. Establish the required data recovery and its authorization first.
- Restoring a backup can lose writes made since that backup. Preserve current state and obtain a scoped decision when those writes would be overwritten; deployment authorization alone does not silently authorize their loss.
- Use an already authorized recovery action only if its effect still matches the agreed scope. Otherwise present the exact required action and affected data without executing it.

Leave a partially applied service accurately recorded when safe rollback cannot proceed. Never weaken health checks or fabricate successful data to finish acceptance.

## Uninstall

Inventory resources actually owned by the service: package/binary, unit/container, account, configuration, data, volumes, credentials, scheduled jobs, and network rules. Shared packages, networks, accounts, and external volumes are not automatically owned by the service.

Stop and remove the requested runtime components. Preserve configuration, persistent data, and credentials by default. Purge only explicitly named and authorized data; use [Filesystem Safety](../../rumo-filesystem-safety/SKILL.md) for deletion and Database Change Safety for database changes. Removal from an application package manager does not authorize deleting its parent directory or pruning all container resources.

Verify intended listeners/processes are gone, unrelated services remain usable, and retained state has not moved or lost access. Update the existing host record with removed and retained resources and the available reinstall/recovery path.

## Source

- [Docker storage](https://docs.docker.com/engine/storage/): container writable-layer data does not survive destruction of the container.
