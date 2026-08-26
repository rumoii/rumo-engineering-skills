---
name: rumo-find-simplifications
description: Use only when explicitly asked to find simplifications, reduce engineering complexity, audit technical debt for removable surface, or propose a simplification plan in software or shared-skill repositories. Require consumer and compatibility evidence, protect deployed behavior and shared contracts, and prefer a few high-confidence deletion or consolidation candidates over speculative refactoring.
---

# Rumo Find Simplifications

Find code, configuration, tests, packages, or workflow surface whose maintenance cost exceeds its current value. An audit is read-only unless the user separately asks to implement candidates.

## Strong Candidates

Look for:

- public methods, events, configuration fields, DTOs, routes, or extension points with no production consumer;
- two representations, caches, or status machines that mirror the same authoritative fact;
- production APIs used only by tests, demos, or obsolete scripts;
- generic interfaces carrying policy needed by only one consumer;
- compatibility branches for a capability that is absent from production, data, deployment, and supported versions;
- duplicate implementations across sibling modules that have the same contract and lifecycle;
- packages or modules containing only support code while adding build, release, or dependency overhead;
- hand-written infrastructure covered by a healthy dependency or platform primitive that would delete owned implementation and dedicated tests;
- speculative configuration and abstraction with no current product owner.

A typo, one unused local variable, or "this looks complex" without call-site proof is not a simplification candidate for this skill.

## Rumo Guardrails

Before proposing removal or consolidation, inspect the applicable evidence:

- sibling applications or parallel implementations when the contract may be shared;
- active release branches and upgrade paths;
- existing database rows, schemas, migrations, and rollback behavior;
- frontend routes, permissions, product modes, licenses, and hidden feature gates;
- terminal clients, task protocols, Runner, PSModel, MCP, middleware, and third-party consumers;
- packaging profiles, generated artifacts, deployment scripts, and field configuration.

Absence from one environment, source search, or test suite does not prove that a field capability is unused. Do not remove backward compatibility solely because the repository is quiet. Treat deployment and persisted-data evidence as separate from source evidence.

## Evaluate Each Candidate

For every candidate, establish:

1. **Authority:** where the relevant fact or behavior is actually owned.
2. **Consumers:** all known production callers and data or protocol readers.
3. **Owned cost:** code, tests, docs, configuration, packaging, release, and operational burden that would disappear.
4. **Behavior change:** what capability, compatibility, or failure handling would be lost.
5. **Replacement:** dependency, existing owner, simpler representation, or direct call path.
6. **Verification:** focused tests, builds, artifact checks, migration checks, or field evidence needed to prove removal.
7. **Rollback:** how to restore behavior if an unknown consumer appears.

Reject a candidate when it moves complexity behind a wrapper, preserves most bespoke semantics, or requires a wider redesign than the deleted surface justifies.

## Output

Report a short ranked list. For each candidate include exact paths and symbols, consumer evidence, deletable surface, affected products and versions, risk, verification plan, and confidence. Separate confirmed candidates from leads requiring runtime, database, deployment, or owner confirmation.

Do not modify code during a simplification audit. When implementation is requested, apply `rumo-coding-guidelines`, make one candidate a bounded change, and verify it through `rumo-change-verification`.
