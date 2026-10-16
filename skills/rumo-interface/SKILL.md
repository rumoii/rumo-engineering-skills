---
name: rumo-interface
description: Use when adding, changing, deprecating, or reviewing anything another process, version, or product reads or writes, such as an HTTP/JSON endpoint or OpenAPI contract, DTO, event or queue message, protocol, configuration field, database representation, persisted file, or export. Trace every producer and consumer, define old/new compatibility and rollout order, and for HTTP routes also cover authentication, authorization, idempotency, rate limits, pagination, and response cost. Do not use for purely internal refactors with no external reader.
---

# Rumo Interface

Anything that crosses a process, storage, deployment-version, module, or product boundary is an interface. Change it as a contract, not as local code. Database writes themselves go through `rumo-database-change-safety`.

## 1. Inventory

Before editing, identify:

- the authority for names, types, units, nullability, defaults, enum values, identifiers, ordering, and error semantics;
- every production producer and consumer: frontends, services, clients, middleware, reports, imports and exports, scripts, sibling products, supported branches;
- everything derived from the authority: generated clients, schemas, mappers, fixtures, examples, deployment configuration, docs;
- instances that outlive one process version: stored rows, queued messages, files, caches;
- how it rolls out: atomic replacement, rolling deploy, offline upgrade, delayed workers, customer packages, mixed versions in the field.

A search is discovery, not proof of absence. Check reflection, dynamic deserialization, SQL, templates, external integrations, and deployed configuration.

## 2. Classify

For each producer and consumer pair, the change is one of: additive and ignored by old readers; additive but required by new readers; a meaning change to an existing field; restrictive, renamed, removed, reordered, or retyped; durable, so old stored values persist; or intentionally incompatible within a declared window. "JSON ignores unknown fields" is not compatibility: required values, enums, defaults, validation, UI assumptions, SQL projections, signatures, and side effects can still break old consumers.

## 3. Plan The Transition

When versions overlap, expand, migrate, then contract:

1. Make readers accept both old and new shapes without changing meaning.
2. Ship compatible readers before new writers.
3. Switch writers and migrate stored data with bounded, observable progress.
4. Confirm old producers, queued messages, files, and supported clients are drained or upgraded.
5. Remove the compatibility code only once its supported lifetime is over.

To deprecate a route, field, message, or format, and only when removal is authorized: ship and document the replacement, find and notify consumers, expose the established deprecation or sunset signal, measure usage per consumer, rehearse migration and rollback, and remove only when the agreed support window and usage criteria are both met. Age alone never proves something is safe to remove; consumers you cannot observe stay recorded as unverified.

Resolve defaults in the owning parser or config layer, not in scattered null checks. Fail early and loudly on invalid referents, fields, enum values, units, or versions. Use opaque stable identifiers. Version durable formats whose interpretation can change, say which versions each reader accepts, and never reinterpret old data silently.

## 4. Failure And Rollback

Define error categories, partial success, retry safety, duplicate handling, and whether bad input is rejected before side effects. Put validation in one owner. Treat rollback as a matrix: can the old version read what the new one wrote, can messages be replayed, does a down-migration lose data, and when is the last safe rollback point.

## 5. HTTP Routes

For HTTP/JSON surfaces, read [references/http.md](references/http.md) and work through its checklist: convention, contract, compatibility with existing callers, authentication, authorization and isolation, retries and idempotency, cost and incident control, collections, response cost, errors, and leaked internals.

## 6. Verify The Matrix

| Producer | Consumer | Evidence |
| --- | --- | --- |
| old | old | existing behavior still pinned |
| old | new | defaults, migration, and old stored values work |
| new | new | new meaning and invalid cases work |
| new | old | compatible, or the rollout explicitly forbids this pair |

Add invalid types, missing required values, unknown enums, boundaries, duplicate delivery, serialization round trips, reload of stored data, and rollback where they apply. Check the assembled route or artifact when generation, packaging, proxies, or deployment can differ from source tests. Plan coverage with `rumo-test`; check the final diff with `rumo-verify`; record a material compatibility or versioning policy with `rumo-plan`.

## Report

The authority, producers, consumers, classification, rollout order, migration owner, failure behavior, rollback cutoff, evidence obtained, and any external or field consumer still unverified.
