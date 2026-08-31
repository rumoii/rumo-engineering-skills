---
name: rumo-old-coder
description: Use for evidence-first, high-assurance implementation when the user explicitly asks for TDD, an executable specification, proof that a change works, or confidence without line-by-line code review, and for changes whose failure could affect money, authentication, authorization, durable data, concurrency, migrations, or public interfaces. Do not invoke this full workflow for ordinary low-risk changes that only need focused tests and normal verification.
license: MIT
---

# Old Coder

Move trust from informal code inspection to two durable artifacts: an executable SPEC approved before implementation and an EVIDENCE report backed by one reproducible final gauntlet run. The gauntlet demonstrates only the constraints it exercises; it does not prove that the SPEC is complete or that every checker is sound.

Apply `rumo-coding-guidelines` for scope and implementation discipline, `rumo-test-evidence` for claim-to-evidence selection, and `rumo-change-verification` before declaring the final change ready. Add domain skills such as `rumo-http-api`, `rumo-interface-evolution`, `rumo-lifecycle-safety`, or `rumo-database-change-safety` when their surfaces apply. This skill owns the assurance loop; those skills own their domain constraints.

Do not manufacture this workflow for review-only requests, prose-only edits, routine refactors, or ordinary bug fixes where the user has not requested high assurance and the failure model is not high stakes. Use the repository's normal focused tests and verification instead.

## Assurance Loop

```text
SPEC -> approval -> RED -> GREEN -> REFACTOR -> GAUNTLET -> EVIDENCE
                       ^___________________________|
```

### 1. Write And Approve The SPEC

Before editing implementation files:

1. Inspect the real entry points, callers, state authorities, existing tests, aggregate checks, dirty worktree, and repository instructions.
2. Select a risk tier:
   - Tier 1: trivial change with no meaningful behavioral surface.
   - Tier 2: normal behavior change or bug fix.
   - Tier 3: money, authentication, authorization, durable data, concurrency, migration, public interface, irreversible side effect, or similarly costly failure.
3. Write a SPEC file at an explicit path using [references/templates.md](references/templates.md). Include concrete behaviors, invalid and boundary cases, Must NOT invariants, a failure model for Tier 3, the proposed evidence layers, and the exact setup changes.
4. List every proposed new dependency, generated helper, worktree or branch, environment change, and persistent artifact. Prefer existing project tooling and standard-library helpers.
5. Show the SPEC to the user and obtain approval of that exact revision before implementation. A clarification answer is input, not approval: revise the SPEC, append the reason, and request approval again.

SPEC approval authorizes only the implementation and local verification described by the task. It does not authorize commits, tags, pushes, deployments, persistent database writes, destructive cleanup, credential changes, paid services, or other separately controlled actions. Obtain the authorization required by the owning workflow immediately before those actions.

Keep the SPEC append-only after approval. If implementation reveals a wrong or missing requirement, stop, record the revision, and obtain approval of the revised SPEC before continuing. If the user explicitly requires an autonomous run without an approval pause, record `spec approval: not obtained (autonomous run)` and lower the final confidence claim.

### 2. Prove RED

For each new behavior, add a focused test and observe it fail for the intended behavioral reason before implementing the change.

- Prefer an assertion failure over an import, setup, or collection error.
- A bug fix starts with a test that reproduces the bug.
- If the test passes immediately, prove that it can detect the behavior by applying a temporary divergent implementation in an isolated or safely restorable state, observing failure, and restoring it.
- Do not edit the implementation and its behavioral assertion together to manufacture green.

Record the RED command and failure reason for the evidence notes. RED observations are development evidence, not final pass results.

### 3. Reach GREEN Minimally

Implement the smallest change that satisfies the approved behavior. Run the focused test and the relevant surrounding suite. Preserve unrelated dirty work and existing contracts not changed by the SPEC.

### 4. Refactor Under Green

Refactor only while the suite is green. Keep behavioral assertions fixed. Test-structure cleanup may extract helpers or fixtures in a separate step, but it must preserve assertions and rerun mutation or equivalent sensitivity checks when those checks are part of the gauntlet.

Any assertion change that alters accepted behavior returns to SPEC and RED.

### 5. Build The Gauntlet

Read [references/gauntlet.md](references/gauntlet.md) when selecting or creating gauntlet layers. Prefer the repository's existing tools and aggregate entry points. Add a new repository-owned gate only for a mechanically decidable invariant and follow `rumo-repository-gates`.

Use the smallest stack that can falsify the approved claims:

| Layer | Required when |
| --- | --- |
| Focused and surrounding tests | every behavioral change |
| Full relevant suite | regressions can cross the edited module |
| Types, lint, and format | the repository owns these checks |
| Changed-line or changed-branch coverage | coverage tooling exists or the approved SPEC adds it |
| Mutation testing | Tier 2 high-assurance work and Tier 3, unless unavailable with an explicit downgrade |
| Property, fuzz, race, stress, compatibility, rollback, UI, performance, or observability checks | the failure model names the corresponding risk |
| Real execution | the claim depends on assembled runtime behavior |
| Dependency, license, capability, and secret checks | dependencies or execution capabilities changed |
| Suite-health checks | flakiness or order dependence could invalidate results |

Every claimed layer must fail closed. For a home-grown checker, verify at least one known-bad input reaches its intended failure path before trusting a pass. A negative control proves only that case; do not overstate its coverage.

Persist one cross-platform or repository-native entry point that reruns every selected layer from fresh inputs and returns non-zero if any required layer fails. Remove stale reports before the run, identify the tested source state, and keep tool versions reproducible. Do not use personal paths, ambient scratch scripts, or ignored stale outputs as required evidence.

Never mark an omitted layer as passed. Classify it as:

- `N-A`: the relevant surface does not exist;
- `UNAVAILABLE`: the surface exists but the required tool could not run;
- `SUBSTITUTED`: another check ran, with the missing detection capability stated.

### 6. Run Fresh And Write EVIDENCE

After the last code, test, checker, configuration, and documentation edit, run the complete gauntlet once from fresh inputs. Only this final run supplies pass counts and measured results for EVIDENCE.

Write the report using [references/templates.md](references/templates.md). It must contain:

- the exact approved SPEC revision and source state;
- a bidirectional mapping between scenarios, Must NOT constraints, failure modes, and falsifying tests or gates;
- every final command and its actual numeric or observable result;
- omitted or substituted layers and their limits;
- failures encountered and how they were resolved;
- dismissed findings with evidence, not assertion;
- structural blind spots and unverified environment or field boundaries.

The result is blocked while a required gauntlet layer fails. Do not weaken assertions, lower thresholds, add broad skips, hide errors, or relabel a failing layer to obtain green.

## Tier 3 Independent Verification

Independent verification is optional unless the user or an owning policy requires it. When it is selected and fresh-context delegation is available, read [references/independent-verification.md](references/independent-verification.md) in full before starting. The verifier attacks the exact final source state and fixes nothing. A verdict against an earlier state does not transfer to later edits.

Cap verification at two rounds unless the user explicitly approves more. Report `passed`, `failed`, `blocked`, or `not performed`; do not convert tool absence or stale-state verification into a pass.

## Non-Negotiable Integrity Rules

1. Never weaken or delete a meaningful test to make the implementation pass.
2. Never claim a command, layer, environment, package, deployment, or field workflow that was not actually exercised.
3. Never use coverage percentage as a substitute for meaningful assertions.
4. Never mock the unit under test; mock external boundaries only when the claim permits it.
5. Never let an unreadable input, unexpected exit code, skipped mutant, or missing artifact become a successful gate.
6. Never describe local source checks as package, deployment, Windows, or real-field acceptance.
7. Never let the assurance workflow expand the user's authorization or overwrite unrelated work.

## Maintenance And Provenance

This skill adapts the MIT-licensed `old-coder` workflow. Read [references/upstream-review.md](references/upstream-review.md) when maintaining the adaptation or comparing it with upstream. The original license is preserved in [LICENSE.upstream](LICENSE.upstream).
