# SPEC And EVIDENCE Templates

Use these templates as a starting point. Adapt the evidence layers to the approved risk model instead of preserving empty rows.

## SPEC

```markdown
# SPEC - <task name>

- Tier: <1 | 2 | 3>
- Artifact path: <absolute path>
- Source scope: <repositories, modules, entry points>
- Isolation: <existing worktree | new worktree | branch | none, with reason>

## Setup Plan

- Tools or dependencies to add: <each with justification, or none>
- Persistent files to add or change: <exact paths>
- Environment changes: <or none>
- Git operations proposed: <or none; approval here does not replace commit/push authorization>
- External or destructive actions proposed: <or none; separately authorized>

## Scenarios

Feature: <capability in user language>

Scenario: <concrete successful behavior>
  Given <starting state>
  When <action and concrete input>
  Then <observable output and durable state>

Scenario: <concrete failure or boundary behavior>
  Given <starting state>
  When <invalid, duplicate, stale, hostile, or boundary input>
  Then <exact rejection, cleanup, and unchanged state>

## Must NOT

- <compatibility, permission, state, performance, or scope invariant>

## Failure Model (Tier 3)

| Failure mode | User or system impact | Falsifying layer |
| --- | --- | --- |
| <risk> | <impact> | <test, gate, rehearsal, or declared gap> |

## Planned Gauntlet

| Claim or risk | Layer | Command or scenario | What it cannot prove |
| --- | --- | --- | --- |
| <claim> | <unit/integration/browser/artifact/etc.> | <planned entry point> | <boundary> |

## Revisions

- Initial revision: <date and reason>
- <append later changes; never silently replace approved behavior>
```

## EVIDENCE

```markdown
# EVIDENCE - <task name>

- Tier: <1 | 2 | 3>
- SPEC: <absolute path and approved revision>
- Spec approval: <exact user approval | not obtained, autonomous run>
- Source state: <commit SHA or reproducible tree identity>
- Toolchain: <version sources>
- Final entry point: <one reproducible command>
- Final fresh run time: <timestamp and timezone>
- Independent verification: <passed | failed | blocked | not performed>

## SPEC To Evidence Mapping

| Scenario, Must NOT, or failure mode | Falsifying test or gate | Final result |
| --- | --- | --- |
| <item> | <file/test/layer> | <pass | fail | unverified | n-a> |

## Final Gauntlet Results

| Layer | Exact command or workflow | Actual result | Evidence boundary |
| --- | --- | --- | --- |
| <layer> | <command> | <counts, measurements, or observed state> | <what remains unproved> |

## Layers Not Run As Specified

- N-A: <surface does not exist, with reason>
- UNAVAILABLE: <surface exists but tool could not run>
- SUBSTITUTED: <replacement and what it cannot detect>

## Independent Verification

- Verifier and fresh-context status: <or not performed>
- Exact source state observed: <state>
- Inputs supplied: <task contract, SPEC, source state, entry point>
- Attacks performed: <not only findings>
- Findings and grading: <behavioral | description/mapping>
- Fixes after last verified state: <therefore unverified, or none>

## Dismissed Findings

- <finding> - dismissed because <specific file, test, command, or runtime evidence>
- Or: none

## Structural Blind Spots

- <unexercised runtime, platform, package, deployment, or field boundary>

## Honest Notes

- <RED observations, failed checks, SPEC revisions, substitutions, and confidence reductions>
```

Use `pass` only for an executed check that can falsify the mapped claim. A skipped row is `unverified` or `n-a`, never `pass`. Results from before the final edit do not belong in the final gauntlet table.
