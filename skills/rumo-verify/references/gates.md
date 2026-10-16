# Building Repository Gates

A gate turns a rule that a machine can decide into a check that blocks bad states. Do not build a gate for a matter of taste, and do not leave a validator unconnected to the commands developers and CI actually run.

## Define The Invariant First

Write down, before any code:

- the invalid repository state to reject;
- the files or generated artifacts that decide it;
- whether the gate reads source, build output, the Git index, a branch diff, or the working tree;
- supported operating systems and runtimes;
- the local and CI commands that will run it;
- its expected cost, owner, and the fix a developer should apply.

Reject goals like "improve quality" until they become a deterministic condition. Prefer an existing parser or structured API over reconstructing structure with regular expressions.

## Put It Where The Rule Lives

- Keep the gate and its tests in the repository that owns the rule. CI must not depend on anyone's personal skill installation or checkout; a gate copied from a skill becomes the product's own code.
- Change generated output only through its source and generator. A gate that reads build artifacts declares and enforces that prerequisite; a source gate passes on a clean checkout without stale build or cache residue.
- Wire the gate into the real aggregate command and CI configuration. Check included CI files, child pipelines, and custom config paths before claiming a root file takes effect.

## Fail Closed, Explain The Fix

- Exit non-zero for every invalid state and zero only after all checks finish. Collect independent errors unless an earlier failure makes later checks meaningless or expensive.
- Print repository-relative paths, line numbers when known, the rule, and the violation.
- Treat missing input, unreadable configuration, parser failure, and unsupported versions as failures, not skips.
- Keep output deterministic and free of secrets, personal paths, timestamps, and unrestricted business data.
- Avoid broad exception handlers and fallback parsers that turn a broken gate into a pass.
- Make exceptions narrow, documented, and owned; never disable a rule globally for one case.

## Keep It Stable

- Use runtimes and dependencies the repository already has. Add network access, credentials, services, or installs only when the rule truly needs them and CI owns the prerequisite.
- A check mode never modifies tracked files, the index, user configuration, or remote state. A formatter or generator may have a separate write mode, but its check mode only detects drift.
- Bound time and memory. Move expensive platform checks to a named CI job. Make commands and paths work on every supported OS, or declare the platform-specific job explicitly.

## Prove The Gate

Add tests or fixtures showing that a minimal valid state passes, each class of invalid state fails for the intended reason, missing and malformed inputs fail, diagnostics point at the repair location, and path handling and clean checkouts work. When a write mode exists, show it is idempotent and separate from check mode.

Run the gate, its tests, the aggregate command that includes it, and `git diff --check`. Where feasible, prove the aggregate entry point fails on a deliberately invalid temporary fixture, never by corrupting the user's working tree.

## Report

State the invariant, the deciding inputs, the local and CI entry points, sample diagnostics, runtime and platform assumptions, the invalid cases exercised, and whether a real CI run happened. A locally parsed CI file is not a passing pipeline.
