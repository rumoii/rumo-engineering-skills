# Simplification Audit

Use only when the user explicitly asks to find simplifications, reduce complexity, or audit removable surface. The audit is read-only; implementing a candidate is a separate request handled with `rumo-coding-guidelines` and `rumo-verify`, one candidate per change.

## Strong Candidates

- Public methods, events, configuration fields, DTOs, routes, or extension points with no production consumer.
- Two representations, caches, or state machines mirroring the same fact.
- Production APIs used only by tests, demos, or dead scripts.
- Generic interfaces carrying policy that only one consumer needs.
- Compatibility branches for capabilities absent from production, data, deployment, and supported versions.
- Duplicate implementations in sibling modules with the same contract and lifecycle.
- Packages or modules that hold only support code yet add build, release, or dependency overhead.
- Hand-written infrastructure that a healthy dependency or platform feature would replace, deleting owned code and its tests.
- Speculative configuration or abstraction with no current owner.

A typo, one unused local, or "this looks complex" without call-site evidence is not a candidate.

## Guardrails

Before proposing removal, check whatever applies: sibling applications sharing the contract, active release branches and upgrade paths, stored data and migrations, routes and permissions and hidden feature switches, external clients and protocols, packaging and deployment scripts, and field configuration. A quiet source search does not prove a field capability is unused; source evidence and deployed-data evidence are separate.

## Per Candidate

State:

1. **Owner:** where the fact or behavior really lives.
2. **Consumers:** every known caller and data or protocol reader.
3. **Deletable cost:** code, tests, docs, configuration, packaging, and operations that disappear.
4. **Behavior change:** capability, compatibility, or failure handling that would be lost.
5. **Replacement:** dependency, existing owner, simpler representation, or direct call.
6. **Verification:** checks needed to prove removal is safe.
7. **Rollback:** how to restore it if an unknown consumer appears.

Reject candidates that only move complexity behind a wrapper, keep most of the bespoke behavior, or need a redesign larger than what they delete.

## Output

A short ranked list with exact paths and symbols, consumer evidence, deletable surface, affected products and versions, risk, verification plan, and confidence. Separate confirmed candidates from leads that need runtime, database, deployment, or owner confirmation.
