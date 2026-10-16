# Database Change Procedure

Detailed steps behind SKILL.md. Read the relevant section before preflight, before writing preconditions, before the backup step, and before execution.

## Source Of Truth

1. Read repository guidance, migration tooling, build profiles, deployment scripts, and database docs.
2. Find the schema definitions, migration history, entity mappings, query code, and application code that read or write each affected field.
3. Record product, repository, branch, revision, application version, environment, host, port, database, schema, and engine version.
4. List every service, worker, scheduler, client process, report, export, integration, and sibling product that uses the data.
5. For an existing environment, check the deployed application and schema versions; a source checkout is not deployment evidence. Do not assume two environments share a schema because they share source modules.

## Read-Only Preflight

- Schema objects, migration or version table, constraints, indexes, triggers, functions, ownership, extensions.
- Row counts and bounded checks for nulls, duplicates, broken references, out-of-range values, encoding, and values the new schema cannot hold.
- Aggregates or pseudonymized samples only; never copy credentials, personal data, tokens, or raw business rows into logs or reports.
- Table and index size, active sessions, long transactions, locks, replication, disk space, and maintenance window when the risk warrants.
- Running processes, schedulers, consumers, and background jobs that could race with the change.
- Existing backup mechanism, last verified restore, recovery owner, retention location, and free capacity.

Even a read can overload a large live database; scope it, add timeouts, and explain expensive scans before running them.

## Executable Preconditions

Make the change refuse an unsafe target before its first write:

- assert database and schema identity, engine version, expected migration version, and required application state;
- assert expected tables, columns, types, constraints, indexes, and prerequisite migrations;
- set lower and upper bounds on matched and changed rows; unexpected zero and excessive counts fail unless the plan allows them;
- require zero duplicates, nulls, orphans, or invalid values before restrictive or destructive steps;
- decide whether writes stop, services drain, schedulers pause, or workers reach zero active tasks;
- set lock and statement timeouts, transaction scope, batch size, restartability, and idempotency for the actual engine and tool.

Do not claim transactional rollback for DDL unless the engine supports it. Never hide a failed migration behind broad exception handling or an unconditional version bump.

## Application Compatibility

Trace old application against expanded schema, new application before and after data migration, entity types, DTOs, queries, reports, exports, caches, queues, client protocols, defaults, null handling, serialization, enum meaning, timezone and precision, rolling deploys, delayed jobs, retries, and replayed messages. When backward compatibility is impossible, require a maintenance window and a deployment order; rolling back a binary alone does not undo an incompatible schema.

## Backup And Restore Readiness

Before a restrictive, destructive, coordinated, or high-impact write:

1. Choose a backup covering the affected schema and its dependencies.
2. Store it outside the location being changed or cleaned.
3. Record target identity, source version, start and end time, command, exit status, size, and checksum where the format allows.
4. Check that the backup is complete and readable.
5. Rehearse a restore in an isolated target when the impact justifies it.
6. Record recovery time, required application version, and data written after the recovery point that would be lost.

A dump file or snapshot existing is not restore evidence. If recovery cannot be verified, say so before asking for write approval.

## Execution

1. Re-check target identity and preconditions immediately before the first write.
2. Record a start time and the deployed application state.
3. Use the repository's migration entry point or the reviewed SQL artifact; never retype production SQL from chat when an owned artifact exists.
4. Configure the client or runner to stop on the first error.
5. Run only the approved statements against the approved target; do not extend cleanup to caches, queues, object storage, volumes, other schemas, or sibling products.
6. Record statement status, migration version, and affected-row counts without printing secrets or row contents.
7. Stop on failed preconditions, unexpected counts, timeouts, lock contention, partial execution, or migration drift. Do not improvise a repair on the live target.

Never run a destructive rollback automatically because verification failed. Preserve evidence, decide whether rollback or forward repair is safer, and get any further approval the plan requires.

## Verification Layers

1. **Schema:** objects, types, constraints, indexes, ownership, migration version.
2. **Data:** affected counts, invariants, referential integrity, duplicates, nulls, reconciliation totals.
3. **Runtime:** service health, startup and migration logs, released locks, schedulers, queues, replication.
4. **Function:** the affected API, UI, report, import or export, worker, or client workflow.
5. **Compatibility:** the old/new or mixed-version behavior the plan requires.
6. **Recovery:** backup retained, rollback still executable, recovery point recorded.

## Special Cases

- **Cleanup and reset:** name the exact objects and data classes; keep unrelated schemas, databases, storage, queues, caches, volumes, configuration, and audit records unless explicitly included; preview counts read-only before deleting.
- **Backfills and large tables:** deterministic ordered batches with checkpoints, retries, and reconciliation; weigh write amplification, replication lag, lock time, maintenance impact, and concurrent writers; avoid one long transaction rewriting a whole table without evidence it is acceptable.
- **Already-applied migrations:** do not edit a migration that ran in a shared or released environment unless the framework requires that model; add a corrective migration and keep the checksum or version chain.
- **Partial failure:** record which statements committed, which did not run, the current migration version, active locks, service state, and data reconciliation before choosing rollback or forward repair. Never blindly rerun an unknown partial migration.
