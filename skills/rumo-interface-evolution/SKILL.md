---
name: rumo-interface-evolution
description: Use when adding, changing, deprecating, or reviewing a Rumo API, DTO, event, Kafka message, terminal protocol, configuration field, database representation, persisted file, export, or other producer-consumer format. Trace every reader and writer, define old/new compatibility and rollout order, reject ambiguous defaults, and verify migration and rollback behavior.
---

# Rumo Interface Evolution

Treat every value crossing a process, persistence, deployment-version, module, or product boundary as an interface. Apply `rumo-coding-guidelines`; use `rumo-database-change-safety` before writing an existing database.

## Inventory The Interface

Identify before editing:

- the authority that defines field names, types, units, nullability, defaults, enum values, identifiers, ordering, and error semantics;
- all production producers and consumers across frontend, backend, terminal, middleware, reports, imports, exports, scripts, sibling products, and supported branches;
- generated clients, schemas, mappers, fixtures, examples, deployment configuration, and documentation derived from that authority;
- persisted or queued instances that can outlive one process version;
- the actual rollout topology: atomic replacement, rolling deployment, offline upgrade, delayed worker, customer package, or mixed-version field environment.

Search is discovery, not proof of absence. Check dynamic deserialization, reflection, SQL, templates, external integrations, and deployed configuration where they can consume the interface.

## Classify Compatibility

For each producer-consumer pair, state whether the change is:

- additive and safely ignored by old readers;
- additive but required by new readers;
- a semantic change to an existing field;
- restrictive, renamed, removed, reordered, or type-changing;
- durable and therefore subject to old stored or queued values;
- intentionally incompatible and limited to a declared maintenance window.

Do not call a change backward compatible merely because JSON parsers ignore unknown fields. Required values, enums, defaults, validation, UI assumptions, SQL projections, signatures, and side effects can still break old consumers.

## Design The Transition

Prefer an explicit expand-migrate-contract sequence when versions can overlap:

1. Make readers accept the old and new representations without changing meaning.
2. Deploy or release compatible readers before new writers.
3. Change writers and migrate durable data with bounded, observable progress.
4. Prove old producers, queued messages, files, and supported clients are drained or upgraded.
5. Remove compatibility code only when its supported lifetime and reintroduction risk are resolved.

Resolve defaults at the owning parser or configuration layer, not as scattered `null` fallbacks inside business execution. Fail loudly at load or the earliest resolvable point when a required referent, field, enum value, unit, or version is invalid.

Use stable opaque identifiers rather than display names or positional indexes. Preserve unknown values only when forwarding is an explicit requirement; otherwise reject them with a diagnostic that names the invalid field without exposing sensitive payloads.

Version a durable format when structural interpretation can change across releases. Define who increments the version, which versions each reader accepts, and whether unsupported versions fail, migrate, or remain read-only. Never silently reinterpret old data under new semantics.

## Specify Failure And Rollback

Define status codes or error categories, partial-success behavior, retry safety, duplicate handling, and whether malformed input is rejected before side effects. State which component owns validation and avoid contradictory checks that drift across producer and consumer.

Rollback is a compatibility matrix, not only a previous binary. Identify whether the old application can read data written by the new version, whether messages can be replayed, whether a down-migration loses information, and the latest point at which rollback remains safe.

## Verify The Matrix

Exercise the pairs that the rollout can create:

| Producer | Consumer | Required evidence |
| --- | --- | --- |
| Old | Old | Existing behavior remains pinned |
| Old | New | Defaults, migration, and old stored values work |
| New | New | New semantics and invalid cases work |
| New | Old | Either compatible behavior or an explicit rollout prohibition |

Include invalid type, missing required value, unknown enum, boundary values, duplicate delivery, serialization round-trip, persisted-data reload, and rollback cases that apply. Verify the assembled route or artifact when generation, packaging, proxying, or deployment can differ from source tests.

Use `rumo-test-evidence` to plan coverage, `rumo-change-verification` to validate the final diff, and `rumo-engineering-decision` when the compatibility or versioning policy is material.

## Report

Name the authority, producers, consumers, compatibility classification, rollout order, migration owner, failure behavior, rollback cutoff, exact evidence obtained, and any external or field consumer still unverified.
