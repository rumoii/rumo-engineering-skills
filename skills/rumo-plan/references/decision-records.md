# Decision Records

A decision record explains why a material choice exists, which alternatives lost, and what future maintainers must keep true. It complements current code and operational docs; it does not replace them.

## Default Layout

Use only when the repository has no convention and the user agrees:

```text
docs/decisions/proposed/yyyy-mm-dd-topic.md
docs/decisions/implemented/yyyy-mm-dd-topic.md
docs/decisions/rejected/yyyy-mm-dd-topic.md
```

Write the prose in the language the repository uses; keep identifiers and protocol terms as they are.

## Status

- `proposed`: under review or partly implemented.
- `implemented`: shipped and verified to the level the record states.
- `rejected - <reason>`: considered and declined; the reason sits on the status line.

Move the same file between lifecycle directories when its status changes; never keep two copies. Do not add subcategories, indexes, archives, or bilingual copies until the number of records justifies the upkeep.

## Structure

```markdown
# Decision: <title>

Status: proposed | implemented | rejected - <reason>

## Problem
## Decision          (use "Proposal" while proposed or rejected)
## Alternatives considered
## Consequences      (use "Risks" while proposed or rejected)
## Verification
## Rollback
```

- **Problem:** the constraint, described without presupposing the answer.
- **Decision:** current obligations, owners, failure behavior, compatibility, rollout scope.
- **Alternatives considered:** real options only, and why each lost.
- **Consequences:** benefits and costs, including capabilities given up.
- **Verification:** source and unit evidence, built artifact, deployed environment, and field evidence, each stated separately.
- **Rollback:** data, schema, protocol, configuration, package, and service-order requirements.

Add sections for wire fields, schema transitions, authorization matrices, or topology only when they carry required detail.

## Maintenance

- Ground claims in current code, configuration, schema, tests, artifacts, or deployment evidence, or label them as proposal.
- Keep secrets, personal paths, chat or review references, and temporary task numbers out.
- Link to the current authority instead of copying long API or runbook text.
- Update an implemented record when its paths, names, defaults, or mechanisms move; write a new record when the rationale or obligation changes.
- Keep a rejected record only while it prevents a plausible repeat mistake.
- Update affected README, API, migration, deployment, and rollback docs alongside the record.

## Validation

For the default layout, run the bundled validator from the installed skill directory:

```bash
python3 <skill-dir>/scripts/verify_decisions.py --root <repository>
```

```powershell
py -3 <skill-dir>\scripts\verify_decisions.py --root <repository>
```

To make it a permanent repository gate, copy the validator into the repository and wire it into the existing top-level check; CI must not depend on anyone's personal skill installation.
