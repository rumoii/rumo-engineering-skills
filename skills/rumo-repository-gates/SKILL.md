---
name: rumo-repository-gates
description: Use when adding, changing, reviewing, or diagnosing a repository-owned CI check, static verifier, generated-file check, quality threshold, pre-commit rule, or aggregate test entry point in a application or shared-skill repository. Turn a mechanically decidable invariant into a deterministic fail-closed gate with focused self-tests, actionable diagnostics, clean-tree behavior, and explicit source or artifact dependencies.
---

# Rumo Repository Gates

Make important repository rules executable at the narrowest stable owner. Do not create a gate for a preference that requires subjective judgment, and do not leave a validator disconnected from the entry point developers and CI actually run.

## Define The Invariant

Before writing a script, state:

- the invalid repository state that must be rejected;
- the files or generated artifacts that authoritatively determine that state;
- whether the gate consumes source, build output, the Git index, a branch diff, or the working tree;
- the supported operating systems and required runtimes;
- the top-level local and CI commands that must execute it;
- the expected cost, ownership, and corrective action.

Reject goals such as "improve quality" until they become a deterministic condition. Prefer a small parser or structured API over regular-expression reconstruction when the repository already has a suitable parser.

## Place The Gate At Its Owner

Keep the verifier and its tests in the repository that owns the invariant. A product CI job must not depend on one developer's global Skill installation or personal checkout. Shared Skills may provide a reusable template, but the copied product gate becomes product-owned and evolves with that repository.

Edit generated output only through its source and generator. If the gate consumes build artifacts, declare and enforce that prerequisite; if it is a source gate, make it pass on a clean checkout without stale `lib`, `dist`, cache, or generated residue.

Connect the gate to the repository's real aggregate command and CI configuration. Inspect included GitLab files, child pipelines, module-specific workflows, and custom CI configuration paths before claiming a root file is effective.

## Fail Closed And Explain The Fix

- Return non-zero for every invalid state and zero only after all checks complete.
- Accumulate independent errors when doing so does not hide a destructive or expensive prerequisite failure.
- Print repository-relative paths, line numbers when known, the expected rule, and the actual violation.
- Treat missing required input, unreadable configuration, parser failure, and unsupported versions as failures rather than skips.
- Keep output deterministic and free of secrets, credentials, personal paths, timestamps, network-dependent ordering, and unrestricted business data.
- Avoid broad exceptions and fallback parsers that turn a broken gate into success.

Use explicit, documented exceptions with a narrow scope and an owner. Do not disable a rule globally to admit one justified case.

## Keep Execution Stable

Prefer repository-available runtimes and dependencies. Do not add network access, credentials, services, containers, or package installation to a static gate unless the invariant genuinely requires them and CI owns the prerequisite.

Keep read-only gates from modifying tracked files, the Git index, user configuration, or remote state. A formatter or generator may have a separate write mode, but its verification mode must detect drift without rewriting it.

Bound runtime and memory. Split expensive platform or environment checks into a named CI job instead of making every local edit pay the cost. Ensure shell commands and paths work on the repository's supported Windows and Unix environments, or declare the platform-specific job explicitly.

## Prove The Gate

Add focused tests or fixtures that show:

- a minimal valid repository state passes;
- each material invalid class fails for the intended reason;
- missing input and malformed input fail;
- diagnostics identify the repair location;
- path handling and clean-checkout behavior work;
- write mode, when present, is idempotent and separate from check mode.

Run the gate itself, its focused tests, the top-level command that includes it, configuration parsing, and `git diff --check`. When feasible, verify that a deliberately invalid temporary fixture makes the aggregate entry point fail; do not corrupt the user's working tree to test this.

Use `rumo-test-evidence` to select proof for the invariant, `rumo-change-verification` before claiming readiness, and `rumo-engineering-decision` when the gate introduces a material repository policy or cost.

## Report

State the invariant, authoritative inputs, local entry point, CI entry point, failure diagnostics, runtime and platform assumptions, focused invalid cases exercised, and whether a real remote pipeline executed. Do not equate locally parsed CI YAML with a successful runner job.
