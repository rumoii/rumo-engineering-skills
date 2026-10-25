---
name: rumo-coding-guidelines
description: Use when writing, fixing, or refactoring code in a software repository, as the baseline discipline alongside more specific skills. Ground every edit in the real code path, do only the requested work and what it necessarily implies, avoid speculative abstraction and drive-by edits, and close with verification. Do not use alone for review-only, diagnosis-only, or question-answering requests.
---

# Rumo Coding Guidelines

Every change should trace back to the request, the code path it touches, and evidence that it works.

When the user wants these rules active even when this skill is not loaded, offer the always-on block in [references/agents-snippet.md](references/agents-snippet.md). Only after the user agrees, add it to their `AGENTS.md` or `CLAUDE.md` with `scripts/baseline_block.py --target <file> --install`, which changes nothing outside its markers.

## Before Editing

- Read the repository's agent instructions (`AGENTS.md`, `CLAUDE.md`, nearby guidance) and follow them over these defaults.
- Find the real entry point, call chain, configuration, and the existing pattern for this kind of change. Do not locate code from memory, screenshots, error summaries, or file names alone.
- Check the dependencies, types, and documentation already in the project before writing replacement code or adding a package. Do not assume a library lacks a feature without checking its API.
- When the request has several reasonable readings, state the trade-off. Resolve high-risk ambiguity first; `rumo-clarify` covers how.
- When several repositories are involved, keep track of which ones were read, changed, and verified.
- When the change touches money, authentication, authorization, durable data, concurrency, migrations, public interfaces, or irreversible effects, load the `rumo-test` skill and apply its high-assurance risk gate before editing; knowing that the gate exists does not apply it.

## Scope Test

Before adding anything the user did not name, answer three questions:

1. Did the user ask for it?
2. Will the requested result fail without it?
3. What concrete code, data, deployment fact, or user decision shows it is needed?

If the first two answers are no, leave it out and mention it only when the user would want to know. The goal is the smallest correct result, not the smallest diff: keep callers, tests, accessibility, security, existing-data migration, supported platforms, and deployment steps working whenever evidence shows they depend on the change.

## While Editing

- Build the thinnest version that works end to end through the real entry point, then add capability in layers that each still work.
- Do not add generic abstractions, plugin points, configuration switches, or fallback frameworks for a single use.
- Do not reformat, rename, reorder, or refactor neighboring code. Match the surrounding style even when you would choose differently.
- Remove only the dead code this change created.
- Do not keep obsolete paths alive with shims, dual writes, flags, or deprecation periods unless the current contract requires them. Before deleting a path, confirm its callers, generated outputs, and deployment references. Contracts with external, persisted, or deployed consumers follow `rumo-interface`.
- Do not accept a stopgap whose stated purpose is to be replaced later. Record material architectural choices with `rumo-plan`.
- Keep internal risk notes out of deliverables. Add a disclaimer or warning only when the user asked, a decision depends on it, or leaving it out would make the result false or unsafe.
- Report unrelated problems you notice instead of fixing them.
- At these moments read the matching entry in [references/principles.md](references/principles.md): before adding to or restructuring code, after two failed fixes for one symptom, when a requirement only fits through special cases, before writing stateful or heavily branching logic, when writing validation or adapters, when a behavior spans more than three files, before a repetitive edit, and before reporting a measured number.

## Authorization

Treat review, explanation, and monitoring requests as read-only until the user asks for a change. When the request changes mode or scope, re-read it rather than carrying old assumptions forward. Stop searching, testing, or reviewing once the evidence answers the question.

## Working With Other Skills

- The user's task picks the main workflow; specialist skills add their checks to it rather than starting a workflow of their own.
- Share one reading of the repository state, call chain, risk, and evidence across them, and close with one report that covers each skill's checks.
- Reuse a check result while the code, configuration, and target version it ran against are unchanged; after any of them changes, rerun the checks it affects.
- A high-assurance final run is always a fresh run after the last edit; earlier passes never replace it.

### Task Flows

Match the task to one of these routes. For any route except a small edit or an investigation, whose rows below are complete, read [references/task-flows.md](references/task-flows.md) for its steps and stop points before following it. A flow is a default route, not a checklist to copy; when you skip a step, say why in the final report. Tasks that fit none keep the rules above.

| Task | Route |
| --- | --- |
| Small edit | Read, edit, most relevant check, `rumo-verify`; no plan, no review |
| Defect fix | `rumo-debug` proves the cause, failing test, fix, verification recipe, `rumo-verify` |
| Feature | `rumo-clarify` if unclear, `rumo-plan` if multi-step, `rumo-test` risk gate, thin slices, recipe, `rumo-verify` |
| Investigation | Read-only answer with evidence |
| Resume | Read the handoff or decision record, check the actual repository state, continue |
| Refactor | Cover the behavior with tests, move in green steps, rerun the same tests |
| Performance problem | Baseline measurement, profile, fix, same measurement again; report both numbers |
| Metric improvement | Fixed measurement, one logged attempt at a time, keep or revert, never loosen the target |
| Runtime diagnosis | Capture the signal, narrow to one mechanism, confirm, map to source; diagnosis only |
| Prototype | Name the decision, throwaway build outside the product, switchable variants, recommend |
| Visual parity | Baseline screenshots, one component at a time, image comparison |
| Skill or prompt change | `rumo-prose`, repository validators, evaluation cases when behavior changes |
| Pull request follow-up | On request: conflicts, review comments, then checks (`rumo-git-commit`); never merge |
| Pause | Stop at a safe boundary, nothing irreversible, resume note; commit only on request |

## Close With Evidence

- Turn the task into a checkable goal, for example: reproduce, fix, run the focused test.
- Prefer focused tests, builds, linters, script self-tests, `git diff --check`, or a real request or page check. Use `rumo-verify` before claiming the change is ready.
- When a check fails, report the command, the reason, and the remaining risk. When a check cannot run, say so; never substitute "should work".

## Before Handing Back

- Every changed file and hunk belongs to this task.
- No unrequested abstraction, option, or capability slipped in.
- Existing dependencies and patterns were checked before custom code was added.
- When handing back changed work, the final message separates what changed, what was verified, and what remains unverified or blocked. A read-only or planning turn reports what it found and what the user must decide next.
- When the user corrected you twice or more in this task, or the same kind of mistake recurred, end with a one-line offer to review the session for lessons, at most once per session. Do not start the review or edit any skill or instruction file unless the user accepts. Use the `rumo-reflect` skill for the review when it is installed; otherwise list the lessons and change nothing without approval.
