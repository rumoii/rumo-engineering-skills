# Decision Records

A decision record explains why a material choice exists, which alternatives lost, and what future maintainers must keep true. It complements current code and operational docs; it does not replace them.

## Default Layout

Use only when the repository has no convention and the user agrees:

```text
docs/decisions/proposed/yyyy-mm-dd-topic.md
docs/decisions/implemented/yyyy-mm-dd-topic.md
docs/decisions/rejected/yyyy-mm-dd-topic.md
docs/decisions/superseded/yyyy-mm-dd-topic.md
```

Write the prose in the language the repository uses; keep identifiers and protocol terms as they are.

## Status

- `proposed`: under review or partly implemented.
- `implemented`: shipped and verified to the level the record states.
- `rejected - <reason>`: considered and declined; the reason sits on the status line.
- `superseded - [<title>](<relative path>)`: once implemented, now replaced. The status line is exactly one Markdown link, relative to the record, to the record that replaced it. That record may itself be superseded, as long as the chain ends at a proposed or implemented record. It keeps the implemented sections. When a replacing record moves between directories, update the links that point to it.

Move the same file between lifecycle directories when its status changes; never keep two copies. Do not add subcategories, indexes, archives, or bilingual copies until the number of records justifies the upkeep.

## Structure

```markdown
# Decision: <title>

Status: proposed | implemented | rejected - <reason> | superseded - [<title>](<relative path>)

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
- Update an implemented record when its paths, names, defaults, or mechanisms move; write a new record when the rationale or obligation changes, following Superseding A Decision below.
- Keep a rejected record only while it prevents a plausible repeat mistake.
- Update affected README, API, migration, deployment, and rollback docs alongside the record.

## Superseding A Decision

Use when the user overturns a decision, whether or not a record exists for it. The goal is that nothing still carries out the old decision without a stated reason.

1. Write down the old obligation, the new one, and the constraints the old decision protected that still apply.
2. Inventory read-only, working outward from the owner of the decision: callers and contracts; stored data and default configuration; generated outputs, tests, and fixtures; documentation, instructions, examples, and status cards; repository checks that encode the old rule, such as a copied decision validator that must be upgraded before it accepts a `superseded` record; places you cannot reach, such as external consumers or another client's memory. For each, record where it is, how it carries the old decision, and the proposed disposition: replace, partly replace, keep for a compatibility period with an exit condition, keep as history, or unreachable.
3. Show the inventory and stop. Change only the scope the user approves. Contracts follow `rumo-interface`, stored data follows `rumo-database-change-safety`, and each instruction or memory file needs its own approval.
4. Verify from the new behavior, then search for the old names, synonyms, defaults, and examples. No remaining match proves only that the old wording is gone. Never change an old test's expectation just to make it pass; change it only where the new decision changes the behavior it checks.
5. Keep history and update the present. An overturned `implemented` record becomes `superseded` in the repository's convention; the default layout moves it to `superseded/`. A `proposed` record becomes `rejected - <reason>` with a link to the new record; when part of it already shipped, say what shipped in that reason and put the shipped part in the inventory. When a replacing proposal is itself rejected, point the records it superseded at whatever now replaces them, or move the old record back to `implemented` when its decision is in force again. Plan entries get a new line; status cards, code, and current documentation are updated in place.

Report separately every partly replaced item, every item kept for compatibility, every item the user did not approve that still carries the old decision, and every place you could not reach, so nobody reads the result as complete.

## Drift Check

Run it when the user asks whether records still match the code, and for the one record you are updating after its mechanism changed.

1. Scope: the records the user names; otherwise every `proposed` and `implemented` record. Skip rejected and superseded records.
2. From each record, list the obligations a reader can check: named files, symbols, fields, defaults, failure behavior, and rollout scope. Take them from Decision or Proposal, Verification, and Rollback; Problem describes the situation before the decision and is context, not an obligation.
3. Find each one in the current code. When the record names no path, search for it and suggest adding the path to the record.
4. Sort each mismatch into one kind: the code departs from the record; the record is stale because a path, name, or default moved; or code inside the record's scope does something the record does not mention. For a `proposed` record, missing code is expected; report only code that contradicts it.
5. Report only mismatches, each with the record's line and the code's `file:line`, and one "no drift" line for each clean record. List claims the repository cannot settle, such as test counts, timings, or figures from outside reports, separately as unverifiable; they count as neither drift nor no drift. Do not edit the record or the code; the user decides which side changes, and the record is then updated as Maintenance says.

### Against A Goal

Records, tests, and code can agree with each other and still miss what the project set out to do. When the user asks whether a project has drifted from its goal, check against the goal, not the records:

1. Rebuild the current goal from the original request, the specification the user confirmed, and changes approved since, citing each source. When the goal cannot be found, or the sources conflict with no later decision, stop and ask the user which one holds.
2. From goal to current state, find obligations that are missing, reversed, or unproven. From current state to goal, find behavior or rules with no basis in the goal. A feature with no approval on record is a question for the user, not proof of drift.
3. Put each item in one kind: missing or departing, beyond the goal, documentation or baseline out of date, awaiting the user's answer, or evidence too weak to tell. Say whether its evidence is read from code or observed in a run.
4. Report the list and stop; the audit changes nothing. Say "no drift found" only when the list is empty; items awaiting the user's answer or too weak to tell count as neither drift nor no drift.

## Validation

For the default layout, run the bundled validator from the installed skill directory:

```bash
python3 <skill-dir>/scripts/verify_decisions.py --root <repository>
```

```powershell
py -3 <skill-dir>\scripts\verify_decisions.py --root <repository>
```

To make it a permanent repository gate, copy the validator into the repository and wire it into the existing top-level check; CI must not depend on anyone's personal skill installation.
