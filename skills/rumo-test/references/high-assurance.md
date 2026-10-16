# High Assurance

Trust shifts from reading the code to two artifacts the user can check: a spec they approved before work began, and an evidence report produced by one clean, reproducible run after work ended. The evidence covers only what its checks exercise; it does not prove the spec is complete.

Do not use this mode for review-only requests, wording changes, routine refactors, or ordinary bug fixes unless the user asks for it or the failure cost is high.

## Flow

```text
spec -> approval -> failing test -> passing test -> refactor -> check suite -> evidence
                         ^__________________________________________|
```

## 1. Spec

Before touching implementation files:

1. Inspect entry points, callers, sources of truth, existing tests and aggregate checks, the dirty worktree, and repository instructions.
2. Rate the risk:
   - **Low:** trivial, no meaningful behavior surface.
   - **Normal:** an ordinary behavior change or bug fix.
   - **High:** money, authentication, authorization, durable data, concurrency, migrations, public interfaces, or irreversible effects.
3. Write the spec at a path the user agrees on, with these parts:
   - **Behaviors:** concrete scenarios with inputs and expected outcomes, including invalid and boundary cases.
   - **Must not:** invariants that must hold no matter what.
   - **Failure model (high risk):** how this could fail in production and what would detect each failure.
   - **Checks:** the evidence layers that will be run and why each is needed.
   - **Changes to the setup:** new dependencies, helpers, branches, environment changes, and persistent files. Prefer existing tooling.
4. Show the spec and get approval of that exact version. A clarifying answer is input, not approval: revise, note why, ask again.
5. After approval, only append to the spec. If a requirement proves wrong or missing, stop, record the revision, and get it approved before continuing.

If the user explicitly wants an unattended run without the approval pause, write "spec approval: not obtained (unattended run)" in the spec and lower the confidence of the final claim.

## 2. Failing Test, Passing Test, Refactor

Follow the test-first steps in SKILL.md for every behavior in the spec, and keep a note of each failing command and why it failed. These notes are development history; the pass counts in the evidence come only from the final run.

## 3. Check Suite

Use the repository's existing tools and aggregate entry point where they exist. Select only what can falsify the approved claims:

| Check | Include when |
| --- | --- |
| Focused and surrounding tests | always |
| Full relevant suite | a regression could cross the edited module |
| Types, lint, format | the repository already runs them |
| Changed-line or branch coverage | tooling exists or the spec adds it |
| Mutation testing | normal-risk work in this mode and all high-risk work, unless unavailable (say so) |
| Property, fuzz, race, stress, compatibility, rollback, UI, performance, observability | the failure model names that risk |
| Real execution of the assembled system | the claim depends on runtime assembly |
| Dependency, license, capability, secret scans | dependencies or execution capabilities changed |
| Repeat or order-shuffle runs | flakiness could invalidate results |

Every check must fail closed. A checker written for this task must first be shown failing on a known-bad input. That proves only that case; do not overstate it.

Commit one repository-native entry point that reruns every selected check from clean inputs and exits non-zero if any fails. Delete stale reports before running, record the source revision tested, and pin tool versions. Personal paths, scratch scripts, and leftover outputs are not evidence.

A check that did not run is never a pass. Label it:

- **N/A:** the surface does not exist.
- **Unavailable:** the surface exists but the tool could not run.
- **Substituted:** a different check ran; state what it cannot detect.

## 4. Evidence Report

After the last edit to code, tests, checkers, configuration, or docs, run the entry point once. Then write the report:

- the approved spec version and the source revision;
- a two-way map: every scenario, must-not rule, and failure mode points to the checks that would catch it, and every check points back to what it covers;
- every final command with its actual numbers or observable result;
- unavailable or substituted checks and their limits;
- failures met during the work and how they were resolved;
- findings dismissed, each with evidence;
- known blind spots and anything not verified in a real environment.

While a required check fails, the result is blocked. Never weaken an assertion, lower a threshold, add a broad skip, or relabel a failure to get green.

## Optional Independent Verification

When the user or a policy requires it and a fresh-context helper is available, give the helper the spec, the final source revision, and the evidence report, and ask it to attack the claims without fixing anything. A verdict on an older revision does not carry over to later edits. Allow at most two rounds unless the user approves more, and report the outcome as passed, failed, blocked, or not performed.

## Non-Negotiables

1. Do not weaken or delete a meaningful test to make code pass.
2. Do not claim a command, layer, environment, package, deployment, or field result that was not exercised.
3. Do not present coverage as a substitute for assertions.
4. Do not mock the unit under test.
5. Do not let unreadable input, an unexpected exit code, a skipped mutant, or a missing artifact count as success.
6. Do not present local source checks as package, deployment, platform, or field acceptance.
7. Do not let this workflow widen the user's authorization or overwrite unrelated work.
