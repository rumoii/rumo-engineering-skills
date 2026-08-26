---
name: rumo-test-evidence
description: Use when planning, writing, reviewing, or assessing tests for a change, especially when deciding between unit, integration, browser, snapshot, artifact, deployment, terminal, Windows, or field evidence. Convert behavioral claims and risks into the smallest sufficient evidence set, exercise production paths and failure cases, and state clearly what each test layer does not prove.
---

# Rumo Test Evidence

Design evidence around claims, risks, and real execution paths. A large suite, high coverage percentage, HTTP success, screenshot, or source build is not evidence for behavior it never exercised.

## Define The Claim

Write each claim as an observable outcome under a condition, for example: "after a duplicate terminal result is received, one persisted result remains and the task converges to completed." Identify the production entry point, state authority, external dependencies, failure mode, and supported platforms or versions involved.

Reject vague claims such as "works correctly" or "tests pass." Split source, artifact, deployment, and field claims because they require different evidence.

## Select Evidence Layers

Use the lowest layer that can falsify the claim, then add layers only for behavior introduced by assembly or environment:

| Layer | Proves | Does not prove |
| --- | --- | --- |
| Static checks | types, syntax, declared rules, dependency or formatting invariants | runtime behavior |
| Unit test | isolated decisions, transformations, state transitions, invalid inputs | framework wiring or external services |
| Module integration | real framework configuration and cooperating components | packaged or deployed topology |
| Assembled application | routes, dependency injection, serialization, permissions, proxy and persistence path | release artifact or target environment |
| Browser or terminal workflow | visible end-to-end behavior through the exercised backend | other roles, platforms, modes, or customer topology |
| Built artifact inspection | packaged files, images, dependencies, entry points, generated output | successful deployment or business behavior |
| Deployed environment | service startup, configuration, health, API and log behavior on that target | customer field acceptance |
| Field acceptance | named customer hardware, software, data, and workflow | untested environments |

Snapshots are useful for stable model-visible, protocol, document, or UI output when semantic review is possible. Do not normalize away the changed behavior merely to keep a snapshot green.

## Cover Risk, Not Implementation Lines

For the affected behavior, consider:

- successful and invalid input;
- empty, minimum, maximum, duplicate, stale, and out-of-order values;
- permission, tenant, product, license, and ownership separation;
- timeout, cancellation, retry, partial failure, cleanup, and restart;
- old/new API, schema, configuration, message, and persisted-data compatibility;
- locale, timezone, encoding, precision, filesystem, architecture, Windows/Linux, and offline differences;
- packaging, generated files, migrations, defaults, and deployment order.

Coverage finds unexecuted code; it does not establish useful assertions. Add assertions for authoritative state, durable side effects, emitted protocol values, user-visible output, cleanup, and absence of forbidden behavior.

## Keep Tests Trustworthy

- Exercise the same parser, route, dependency injection, serializer, migration, or launcher used in production when the claim depends on it.
- Prefer deterministic clocks, barriers, fixtures, containers, or recorded inputs over sleeps and unconstrained external services.
- Keep fixtures portable and representative. Do not hide platform defects in broad path, timestamp, ordering, or text normalizers.
- Make expected skips explicit and narrow. A self-skipping real-environment test is not evidence that the environment passed.
- Keep secrets and unrestricted customer data out of fixtures, snapshots, logs, and reports.
- Verify that a negative test reaches the intended rejection rather than failing earlier for an unrelated reason.

## Build The Smallest Sufficient Plan

For every planned command or scenario, name the claim and risk it covers. Remove redundant checks only when another check exercises the same production mechanism with equal or stronger assertions. Add a broader build or workflow when module assembly, generated output, packaging, or environment configuration creates additional behavior.

Do not default to the whole repository suite. Do not omit a focused test because CI will eventually run broadly. Use `rumo-change-verification` after implementation to map the exact diff back to this plan.

Apply `rumo-lifecycle-safety` for async or resource behavior, `rumo-interface-evolution` for compatibility matrices, and `rumo-browser-evidence` when persistent visual evidence is requested.

## Report

List each claim, evidence layer, exact command or scenario, result, and remaining boundary. Distinguish tests written from tests run, local from CI, fake from real integration, package inspection from deployment, and deployed verification from field acceptance.
