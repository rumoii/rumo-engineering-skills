---
name: rumo-test
description: Use when planning, writing, or assessing tests for a behavior change, including whether existing tests are enough, which evidence layers (unit, integration, browser, artifact, deployment, field) to use, and test-driven development. Do not use to find the root cause of an existing defect (use rumo-debug) or to check an already finished diff before handoff (use rumo-verify).
---

# Rumo Test

Tests are evidence for claims. A large suite, a coverage number, an HTTP 200, or a screenshot proves nothing about behavior it never exercised.

## Modes

| Mode | Use when |
| --- | --- |
| Evidence plan (default) | Deciding what to test, or whether existing tests are enough; works without writing code |
| Test-first | Implementing a behavior change or bug fix |

The risk gate for money, authentication, data, interfaces, and other high-risk changes, with its spec-and-evidence flow, lives in `rumo-coding-guidelines`.

## Evidence Plan

1. Write each claim as an observable outcome under a condition. Reject "works correctly".
2. Name the production entry point, the source of truth, external dependencies, and supported platforms involved.
3. Pick the lowest layer that can falsify each claim, then add layers only for behavior that assembly or environment introduces. Read [references/evidence-layers.md](references/evidence-layers.md) when choosing layers or listing risks.
4. Keep source, built artifact, deployment, and field claims separate; each needs its own evidence.
5. For every planned check, name the claim and risk it covers. Drop a check only when another one exercises the same mechanism at least as strongly.

## Test-First

1. Write a focused test for one behavior and watch it fail because the behavior is missing, not because of an import or setup error. A bug fix starts with a test that reproduces the bug.
2. If the test passes immediately, prove it can catch the problem: break the implementation temporarily in a restorable way, see the test fail, restore.
3. Write the smallest implementation that turns it green, then run the surrounding suite.
4. Refactor only while green, without touching behavioral assertions. An assertion change that alters accepted behavior goes back to step 1.
5. Never edit the implementation and its assertion together to manufacture a pass.

Example, for a bug where an order placed just before local midnight lands in the next day's sales report:

- Strong: `daily_report_keeps_order_placed_at_2359_local` stores an order through the real service at 23:59 in the shop's time zone, then asserts it appears in that day's report and not in the next. It failed before the fix, which grouped orders by UTC date.
- Weak: a test that mocks `to_local_date` and asserts it was called. It passed before the fix, so it proves nothing about the bug.

## Rules For Every Mode

- Exercise the same parser, route, serializer, migration, or launcher that production uses when the claim depends on it.
- Use deterministic clocks, barriers, or recorded inputs instead of sleeps and live external services.
- Keep skips explicit and narrow. A test that skips itself in a missing environment is not evidence that the environment passed.
- Confirm that negative tests fail at the intended rejection, not earlier for an unrelated reason.
- Keep secrets and unrestricted customer data out of fixtures, snapshots, and logs.
- Do not mock the unit under test, weaken a meaningful assertion, or lower a threshold to get green.

## Report

For each claim: the layer, the exact command or scenario, the result, and what it does not prove. Distinguish tests written from tests run, local from CI, fake from real integration, artifact inspection from deployment, and deployment from field acceptance.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "Coverage is 90%, so it's tested." | Coverage shows lines ran, not that anything was asserted. |
| "The test passed first time, good." | A test that never failed may not test anything; prove it can fail. |
| "CI will run everything anyway." | A focused test catches the regression now and names the claim. |
| "The mock returns the right thing." | Then the mock is tested, not the integration. |
| "It's skipped on this machine, so it's fine." | A skip is missing evidence; report it. |
