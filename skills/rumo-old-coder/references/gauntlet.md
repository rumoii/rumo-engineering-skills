# Gauntlet Design

Read this reference while selecting or implementing gauntlet layers. Start from the target repository's existing package files, CI configuration, Makefile or wrapper scripts, and aggregate checks. The examples below are defaults, not permission to install tools or change dependencies without the approval required by the SPEC and repository workflow.

## Common Ecosystems

| Ecosystem | Tests and types | Lint and format | Coverage and mutation | Risk-specific options |
| --- | --- | --- | --- | --- |
| Java | Maven or Gradle test/verify tasks | Checkstyle, Spotless, Error Prone, repository checks | JaCoCo changed-line inspection, PIT scoped to changed packages | jqwik, Testcontainers, compatibility tests, concurrency stress |
| JavaScript/TypeScript | Vitest or Jest; `tsc --noEmit` | ESLint and repository formatter checks | V8/Istanbul changed-line coverage, Stryker | fast-check, Playwright, axe-core, API contract tests |
| Python | pytest; mypy or pyright | Ruff and repository formatter checks | coverage.py with a failing threshold, diff-cover, mutmut or cosmic-ray | Hypothesis, subprocess/CLI execution, database integration |
| Go | `go test`, `go build`, race detector | `go vet`, staticcheck, gofmt check | built-in coverage, project mutation tool or manual mutation | `testing/quick`, fuzzing, shuffled tests, benchmarks |
| Rust | `cargo test`, `cargo check` | Clippy and rustfmt check | cargo-llvm-cov, cargo-mutants | proptest, fuzzing, loom or concurrency stress |
| SQL | project/database-native integration tests against the real dialect | SQLFluff or repository rules | statement and predicate mapping, manual mutation | forward/rollback rehearsal, lock and data-volume checks |

Use repository wrappers such as `mvnw`, `gradlew`, pinned package-manager commands, or existing Python environments. On native Windows, use the repository's `.cmd`, PowerShell, or Python entry points rather than assuming a POSIX shell. If a new aggregate runner is justified, prefer a small standard-library Python script that behaves consistently on macOS, Linux, Git Bash, WSL, and Windows PowerShell.

## Failure-Model Layers

Tier 3 begins with a concrete failure model. Add a layer only when it can falsify a named risk.

| Risk | Suitable evidence |
| --- | --- |
| Unauthorized access or tenant leakage | actor/action/resource/tenant tests through the production authorization path |
| Duplicate or partial durable writes | transactional integration, idempotency, retry, restart, and rollback checks |
| Race, deadlock, cancellation, or shutdown loss | race detector, barriers, stress loops, forced cancellation, restart tests |
| Public API or persisted-format break | old/new consumer matrix, contract snapshots, migration and rollback tests |
| Parser or hostile-input failure | property tests, fuzzing, size limits, malformed and adversarial corpus |
| Performance or unbounded growth | benchmark with an approved budget, realistic data volume, resource bound assertions |
| Silent production failure | log, metric, state-transition, and reconciliation assertions |
| UI behavior or accessibility | real browser workflow, interaction assertions, accessibility or visual checks |
| Package or platform mismatch | final artifact inspection and execution on the named architecture or operating system |

Mutation and coverage do not substitute for these layers. They assess test sensitivity and execution, not the completeness of the failure model.

## Coverage

Coverage is a gate only when missing required coverage causes a non-zero exit. Prefer changed-line and changed-branch coverage over a global percentage. A high global number can hide an entirely untested change.

Map every uncovered changed branch to one of:

- a meaningful test added;
- unreachable or generated code with evidence;
- an explicit unverified limit in EVIDENCE.

Do not add assertions whose only purpose is touching lines.

## Mutation

Prefer a maintained syntax-aware mutation tool already supported by the project. Scope it to the changed behavior when a full run is impractical, and record that boundary.

When no suitable tool exists, manual mutation is a substitution:

1. Persist a cross-platform runner in the target repository.
2. Select three to five plausible behavioral defects such as a boundary flip, deleted guard, boolean inversion, missing state transition, or incorrect constant.
3. Apply one mutant at a time and prove the production source actually changed to that mutant.
4. Run the relevant suite; every non-equivalent mutant must produce a failing test.
5. Restore the exact original bytes and verify the intended working-tree diff.
6. Rerun the clean suite.

The runner must fail if a source match is missing, ambiguous, unreadable, not applied, or not restored. A killed mutant validates the exercised suite as a whole; do not attribute it to a specific test unless that attribution was independently established.

Before calling a survivor a defect, show one concrete input for which the original and mutant differ. Otherwise it may be equivalent.

## Home-Grown Gates

Custom grep rules, manifest checkers, source-state scripts, and mutation runners belong to the trust chain. They must:

- reject missing, unreadable, malformed, or stale authoritative input;
- distinguish an expected negative result from an execution error;
- avoid `|| true`, swallowed exceptions, and fallback success;
- print actionable repository-relative diagnostics;
- have a focused negative control that fails for the intended reason;
- state what the control does not prove.

For a must-find-nothing search, success means the search completed and found no forbidden item. A match is failure, and a search error is also failure.

## One Fresh Entry Point

The aggregate entry point must:

1. remove stale reports and generated evidence inputs;
2. identify the exact source state and reject relevant uncommitted drift when the evidence claims a commit;
3. run each selected layer and record completion only after success;
4. fail on the first required broken layer or produce an explicit complete failure summary;
5. verify that every expected layer ran before printing success;
6. leave unrelated user files and configuration untouched.

EVIDENCE cites this entry point. Scratch commands that no longer exist, developer-specific absolute paths, and cached reports cannot be required to reproduce the result.
