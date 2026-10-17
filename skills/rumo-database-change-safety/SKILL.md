---
name: rumo-database-change-safety
description: Use when planning, reviewing, generating, testing, or executing any write to an application database, including schema migrations, new columns, backfills, data repairs, cleanup, resets, destructive SQL, restores, and rollback. Start read-only, identify the exact database and application versions, require explicit authorization before changing any existing or persistent database, and prove backup, compatibility, bounded effects, and rollback readiness. Use rumo-debug instead for purely read-only database diagnosis.
---

# Rumo Database Change Safety

A database change is a data-lifecycle operation, not a SQL statement. A migration that exits successfully is not done until existing data, application compatibility, recovery, and business behavior are checked.

## The Write Boundary

- Start read-only. Writing migration code, reviewing SQL, fixing an application bug, or investigating an environment does not authorize changing an existing database.
- Writes include migration runners, `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`, `ALTER`, `CREATE`, `DROP`, import tools, repair jobs, reset scripts, and application endpoints or jobs that mutate stored data.
- A disposable database created and owned by an isolated test run may be changed freely.
- Any existing local, shared, remote, staging, production, or customer database needs either the user's direct instruction to run against that exact target, or explicit approval after seeing the plan.
- Never infer the target from a familiar hostname, earlier deployment, environment variable, screenshot, or package name. Stop when the database identity, write authorization, or recovery owner is unclear.
- Approval for code changes, packaging, SSH access, deployment, or read-only inspection is not database-write approval.

## Classify The Change

| Class | Examples | Required posture |
| --- | --- | --- |
| Additive | nullable column, unused table, compatible index | prove old and new application compatibility |
| Transformative | backfill, normalization, key rewrite, deduplication | bound affected rows, keep it restartable |
| Restrictive | not-null or unique constraint, type narrowing | prove every existing row satisfies the new rule |
| Destructive | delete, truncate, drop, reset, irreversible rewrite | verified recovery and explicit destructive scope |
| Coordinated | schema change tied to a service, package, or multi-product rollout | version order, mixed-version behavior, rollback order |

When mixed application versions cannot share one schema, expand first, deploy compatible code, migrate and verify data, and remove the old shape in a later, separately reversible change.

## Workflow

Read [references/procedure.md](references/procedure.md) for the details of each step.

1. **Source of truth:** schema definitions, migration history, every reader and writer, and the deployed versions.
2. **Read-only preflight:** schema state, row counts and dirty data, locks and capacity, concurrent writers, and existing backup and restore evidence.
3. **Preconditions in the artifact:** identity and version assertions, row-count bounds, zero-violation checks, timeouts, batching.
4. **Compatibility:** old and new application against old and new schema.
5. **Backup readiness:** for restrictive, destructive, coordinated, or high-impact writes, a verified, separately stored backup with restore evidence.
6. **Authorization checkpoint** (below).
7. **Execute fail-closed**, then **verify** schema, data, runtime, function, compatibility, and recovery.

## Authorization Checkpoint

Before writing an existing database, present: target environment, host, database, schema, and application version; the migration or SQL artifact with revision or checksum; risk class, affected objects, expected row range, lock or downtime expectation, services to pause; preconditions and the exact command; backup location and verification result; success checks, rollback triggers, rollback procedure, and recovery owner; and evidence still missing. If the user has not already authorized that exact write, wait.

A checkpoint for adding a required `currency` column to a large table:

```text
Target: test environment, host db-test-02, database shop, schema public, app 4.12.0.
Artifact: migrations/0087_orders_currency.sql, sha256 3f9c...e1.
Class: restrictive (NOT NULL); orders, about 8.2M rows; batched backfill of 5k rows,
then NOT NULL; expected lock under 2 s per batch; pause the nightly import job.
Preconditions: 0 rows with NULL currency after backfill; app 4.12 already writes currency.
Backup: snapshot snap-0087 taken 10:05, restored to a scratch instance and row-counted.
Success: constraint present, 0 NULLs, order create and list tests pass on 4.12.
Rollback: drop the constraint, keep the column; owner: the user.
Missing: lock timing on the full table; measured only on a 1M-row copy.
```

Not a checkpoint: "It's just adding a column, I'll run the migration." It names no target, no row count, no backup, and no way back.

## Stop Conditions

Stop and report, without improvising a live repair, on failed preconditions, unexpected row counts, timeouts, lock contention, partial execution, or migration drift. Never run a destructive rollback automatically because verification failed; preserve evidence and decide with the user whether rollback or forward repair is safer.

## Report

Target identity, source and deployed versions, risk class, preflight results, affected objects and row bounds, backup and restore evidence, authorization received, exact command, actual changes, verification results, rollback status, and remaining field limits. For plan-only work, label every command as proposed and state that no database was written.

Related: read-only diagnosis in `rumo-debug`; test evidence and the high-assurance risk gate, which migrations enter directly, in `rumo-test`; check selection in `rumo-verify`; durable schema or compatibility decisions in `rumo-plan`; file and directory deletion in `rumo-filesystem-safety`; offline packages that embed migrations in the optional `rumo-offline-delivery-audit` extra, when installed.
