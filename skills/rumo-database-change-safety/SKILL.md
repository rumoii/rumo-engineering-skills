---
name: rumo-database-change-safety
description: Use when planning, reviewing, generating, testing, or executing a write-capable database change for applications, including schema migrations, backfills, data repairs, cleanup, resets, destructive SQL, and rollback. Start with read-only discovery, identify the exact database and owning application versions, require explicit authorization before changing any existing or persistent database, and prove backup, compatibility, bounded effects, post-change behavior, and rollback readiness. Use rumo-bug-root-cause instead for purely read-only database diagnosis.
---

# Rumo Database Change Safety

Control database changes as data-lifecycle operations, not as isolated SQL statements. A syntactically successful migration is incomplete until existing data, application compatibility, recovery, and business behavior are verified.

## Preserve The Write Boundary

Start read-only. Writing migration code, reviewing SQL, fixing an application bug, or investigating an environment does not authorize changing an existing database.

Treat these as database writes: migration runners, `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`, `ALTER`, `CREATE`, `DROP`, data-import tools, repair jobs, reset scripts, and application endpoints or scheduled jobs that mutate persisted data.

A task-owned disposable database created inside an isolated test run may be mutated when its ownership and cleanup are concrete. Before changing any existing local, shared, remote, staging, production, or customer database, require either the user's direct instruction to execute against that exact target or a separate explicit approval after presenting the plan.

Do not infer the target from a familiar hostname, previous deployment, environment variable, screenshot, or package name. Stop when database identity, write authorization, or recovery ownership is ambiguous.

## Establish Authority And Scope

Identify the current source of truth before designing SQL:

1. Read repository guidance, migration tooling, build profiles, deployment scripts, and database documentation.
2. Locate the owning schema definitions, migration history, entity mappings, mapper SQL, and application code that reads or writes each affected field.
3. Record product, repository, branch, source revision, application version, environment, host, port, database, schema, and database-engine version.
4. Identify every service, worker, scheduler, terminal process, report, export, integration, and sibling product that consumes the affected data.
5. Inspect the actual deployed application and schema versions when the change targets an existing environment. Source checkout state alone is not deployment evidence.

For software repositories, inspect the repository's authoritative schema definitions when present, then confirm them against migration files and database catalog metadata. Do not assume separate applications or environments have identical deployed schemas merely because they share source modules.

## Classify The Change

Assign the highest applicable risk class:

| Class | Examples | Required posture |
| --- | --- | --- |
| Additive | nullable column, unused table, compatible index | prove old and new application compatibility |
| Transformative | backfill, normalization, key rewrite, deduplication | bound affected rows and preserve restartability |
| Restrictive | non-null or unique constraint, type narrowing | prove all existing rows satisfy the new invariant |
| Destructive | delete, truncate, drop, reset, irreversible rewrite | require verified recovery and explicit destructive scope |
| Coordinated | schema change coupled to service, package, or multi-product rollout | define version order, mixed-version behavior, and rollback order |

Use expand-migrate-contract for changes that cannot safely support mixed application versions: add compatible storage, deploy compatible readers/writers, migrate and verify data, then remove the old representation in a later independently reversible change.

## Run Read-Only Preflight

Collect evidence without mutation:

- Current schema objects, migration/version table, constraints, indexes, triggers, functions, ownership, and extensions.
- Row counts and bounded checks for nulls, duplicates, invalid references, out-of-range values, encoding, and values the new schema cannot represent.
- Representative aggregates or pseudonymized samples; do not copy credentials, personal data, tokens, or unrestricted business rows into logs or reports.
- Table size, index size, active sessions, long transactions, locks, replication state, disk capacity, and expected maintenance window when operational risk warrants them.
- Current application processes, scheduled writers, queue consumers, and background jobs that may race with the change.
- Existing backup mechanism, last verified restore evidence, recovery owner, retention location, and available capacity.

Use narrowly scoped queries with timeouts where possible. A nominally read-only query can still overload a large live database; explain and constrain expensive scans before running them.

## Design Executable Preconditions

Make the change reject an unsafe target before its first write:

- Assert database and schema identity, engine version, expected migration version, and required application state.
- Assert expected tables, columns, types, constraints, indexes, and prerequisite migration records.
- Set lower and upper bounds for matched and changed rows. Treat unexpected zero rows and excessive rows as failures unless the plan explicitly permits them.
- Define duplicate, null, orphan, and invalid-domain checks that must return zero before restrictive or destructive operations.
- Decide whether writes must stop, services must drain, schedulers must pause, or workers must reach zero active tasks.
- Define lock and statement timeouts, transaction scope, batch size, resumability, and idempotency from the actual database engine and migration tool.

Do not claim transactional rollback for DDL unless the target engine and commands support it. Do not make a failed migration appear successful through broad exception handling or unconditional migration-version updates.

## Prove Application Compatibility

Trace the change through producers and consumers:

- Old application against the expanded schema.
- New application before and after data migration.
- ORM/entity types, DTOs, mapper SQL, reports, exports, caches, queues, and terminal protocols.
- Default values, null handling, serialization, enum/domain interpretation, and timezone or precision changes.
- Rolling deployment, mixed-version traffic, delayed jobs, retries, and replayed messages.

When backward compatibility is impossible, require an explicit maintenance window and deployment order. Rollback must include the compatible application and database state; replacing a JAR alone does not recover an incompatible schema transition.

## Verify Backup And Restore Readiness

Before a restrictive, destructive, coordinated, or otherwise high-impact write:

1. Select a backup that covers the affected schema and data dependencies.
2. Store it outside the data or installation location being replaced or cleaned.
3. Record target identity, source version, start/end times, command, exit status, size, and checksum when the format supports it.
4. Validate backup completeness and readability.
5. Rehearse restore in an isolated target when failure impact justifies it.
6. Record recovery time, application version requirements, and data created after the recovery point that would be lost.

The existence of a dump, snapshot, or backup directory is not restore evidence. If recovery cannot be verified, report that limit before requesting write authorization.

## Present The Authorization Checkpoint

Before writing an existing database, state:

- Exact target environment, host, database, schema, and application version.
- Migration or SQL artifact and its source revision or checksum.
- Risk class, affected objects, expected row range, lock or downtime expectation, and services to pause.
- Preconditions and the command that will execute the change.
- Backup location and verification result.
- Success checks, rollback triggers, rollback command or procedure, and recovery owner.
- Evidence still unavailable.

If the user has not already authorized that exact write, wait. Approval for code changes, package creation, SSH access, deployment, or read-only inspection is not database-write approval.

## Execute Fail-Closed

After authorization:

1. Reconfirm target identity and preconditions immediately before the first write.
2. Capture a start timestamp and the deployed application state.
3. Use the repository-owned migration entry point or reviewed SQL artifact. Do not reconstruct production SQL from chat text when an owned artifact exists.
4. Configure the client or migration runner to stop on the first error.
5. Execute only the approved statements and target. Do not expand a cleanup to Redis, Kafka, RustFS, container volumes, other schemas, or sibling products.
6. Record statement status, migration version, and affected-row counts without printing secrets or sensitive row contents.
7. Stop on failed preconditions, unexpected row counts, timeout, lock contention, partial execution, or migration drift. Do not improvise a repair against the live target.

Never automatically run a destructive rollback merely because verification failed. First preserve evidence, determine whether rollback is safer than forward repair, and obtain any additional authorization required by the approved plan.

## Verify The Result

Verify each layer that the change claims to complete:

1. **Schema:** expected objects, types, constraints, indexes, ownership, and migration version.
2. **Data:** affected-row counts, invariants, referential integrity, duplicates, nulls, and reconciliation totals.
3. **Runtime:** service health, startup and migration logs, lock release, scheduled jobs, queues, and replication when applicable.
4. **Function:** affected API, UI, report, import/export, worker, or terminal workflow.
5. **Compatibility:** required old/new or mixed-version behavior.
6. **Recovery:** backup retained, rollback still executable, and recovery point recorded.

Compare expected and actual outcomes explicitly. Report missing evidence rather than treating a successful SQL exit code as business acceptance.

## Handle Special Cases

### Cleanup And Reset

Name the exact database objects and data classes to remove. Preserve unrelated schemas, databases, object storage, queues, caches, volumes, configuration, and audit records unless the user explicitly includes them. Provide a read-only preview with counts before destructive execution.

### Backfills And Large Tables

Prefer bounded batches with deterministic ordering, checkpoints, retry behavior, and reconciliation. Assess write amplification, replication lag, lock duration, vacuum/maintenance impact, and concurrent writers. Do not place an unbounded table rewrite inside a long transaction without evidence that the operational impact is acceptable.

### Applied Migrations

Do not edit a migration already applied to a shared or released environment unless the migration framework and rollout policy explicitly require that model. Add a corrective migration and preserve the historical checksum or version chain.

### Partial Failure

Record which statements committed, which did not run, the current migration version, active locks, service state, and data reconciliation before choosing rollback or forward repair. Never rerun an unknown partial migration blindly.

## Report

Report target identity, source and deployed versions, risk class, read-only preflight, affected objects and row bounds, backup/restore evidence, authorization received, exact execution command, actual changes, verification results, rollback status, and remaining field limits.

For plan-only work, label every command as proposed and state that no database writes were performed.

## Related Skills

- Use [`rumo-bug-root-cause`](../rumo-bug-root-cause/SKILL.md) for read-only database investigation and root-cause tracing.
- Use [`rumo-change-verification`](../rumo-change-verification/SKILL.md) to select source, migration, compatibility, and service checks for a database-code change.
- Use [`rumo-engineering-decision`](../rumo-engineering-decision/SKILL.md) when the schema transition or compatibility strategy needs a durable decision record.
- Use [`rumo-offline-delivery-audit`](../rumo-offline-delivery-audit/SKILL.md) when migration and rollback assets are embedded in an offline package.
