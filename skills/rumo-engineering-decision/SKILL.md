---
name: rumo-engineering-decision
description: Use when creating, updating, reviewing, superseding, implementing, or rejecting a durable engineering decision for a material change, such as a cross-module contract, database or wire format, permission model, lifecycle rule, deployment topology, migration, security policy, or rollback strategy. Do not create a decision record for mechanical edits, local bug fixes, or choices already owned by a current record.
---

# Rumo Engineering Decision

Record why a material engineering choice exists, which alternatives lost, and what future maintainers must preserve. A decision record complements current code and operational documentation; it does not replace them.

## Find The Owner

1. Read repository guidance and search for ADRs, design records, architecture documents, and records covering the same mechanism.
2. Update the existing owner when the decision is unchanged and only facts, paths, or verification moved.
3. Create a new record when the decision itself changes. Cross-link a partially superseded record rather than rewriting it into the opposite choice.
4. Use the repository's existing location, naming, numbering, and language convention. If no convention exists, propose `docs/decisions/{lifecycle}/yyyy-mm-dd-topic.md` and use Simplified Chinese prose while preserving code identifiers and protocol terms.

Do not introduce a decision directory or broad policy during a review-only request. Ask before creating a new repository convention when the requested change does not already imply one.

## Lifecycle

Use one status that matches reality:

- `proposed`: the choice is under review or only partly implemented;
- `implemented`: the described choice is shipped and verified;
- `rejected - <reason>`: the proposal was considered and declined.

When the repository uses the default layout, move the same file name between `proposed/`, `implemented/`, and `rejected/` as its status changes. Do not retain two lifecycle copies. Do not add classification subdirectories, bilingual counterparts, sidecars, an archive tree, or a generated index until the repository has enough decisions to justify that machinery.

Do not mark a record implemented because code was drafted or unit tests passed. State the exact source, artifact, deployment, migration, or field evidence that exists.

## Required Content

Use this compact implemented structure unless the repository already has a stronger template:

```markdown
# Decision: <title>

Status: proposed | implemented | rejected - <reason>

## Problem
## Decision
## Alternatives considered
## Consequences
## Verification
## Rollback
```

For `proposed` and `rejected`, use `## Proposal` and `## Risks` instead of `## Decision` and `## Consequences`. A rejected status must include its reason on the status line.

- **Problem:** describe the constraint without assuming the chosen solution.
- **Decision:** state current obligations, owners, failure behavior, compatibility, and rollout scope.
- **Alternatives considered:** record only real alternatives and why they lost.
- **Consequences:** state both benefits and costs, including capabilities intentionally given up.
- **Verification:** separate source/unit, built artifact, deployed environment, and field evidence.
- **Rollback:** name data, schema, protocol, configuration, package, and service-order requirements.

Add bespoke sections for wire fields, schema transitions, authorization matrices, or deployment topology only when they carry required details.

## Evidence And Maintenance

- Ground claims in current code, configuration, schema, tests, artifacts, deployment evidence, or an explicitly identified proposal.
- Keep secrets, credentials, personal local paths, transcript references, review discussion, and temporary task numbering out of the record.
- Link to current authority instead of duplicating long API or operational instructions.
- Update an implemented record when its owned paths, names, defaults, or mechanisms change; create a new record when the rationale or obligation changes.
- Retain a rejected record only while it prevents a plausible mistake. Do not build an archive mechanism until the repository has enough records to justify its maintenance cost.

## Close The Change

Update affected README, API, migration, deployment, and rollback documentation alongside the record. Run document and change verification appropriate to the touched repository, then report the decision status, owner path, superseded records, and evidence boundaries.

When the repository uses the default layout, validate it with the bundled script. Resolve the installed skill directory rather than assuming a checkout path.

macOS/Linux/Git Bash/WSL:

```bash
python3 <skill-dir>/scripts/verify_decisions.py --root <repository>
```

Windows PowerShell:

```powershell
py -3 <skill-dir>\scripts\verify_decisions.py --root <repository>
```

For a permanent repository gate, copy the validator into the repository's existing orchestration or scripts directory and make that copy repository-owned. CI must not depend on a developer's global skill installation. Add the gate to an existing top-level verification entry point; do not infer that nested application CI files validate the aggregate repository.

Use [`rumo-database-change-safety`](../rumo-database-change-safety/SKILL.md) to plan or execute the database operation itself. A decision record does not authorize database writes or prove backup and rollback readiness.
