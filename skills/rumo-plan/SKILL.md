---
name: rumo-plan
description: Use when turning an agreed multi-step or cross-module task into a short spec and verifiable task breakdown before implementation, when executing an agreed plan task by task, or when creating or maintaining a durable engineering decision record (ADR) for a cross-module contract, data or wire format, permission model or security policy, lifecycle rule, deployment, migration, or rollback. Do not use for single-file fixes or mechanical edits, and do not write a duplicate record for a choice an existing record already owns (update or supersede it instead); settle unclear goals with rumo-clarify first.
---

# Rumo Plan

Make the work and its reasons explicit before they become code.

## Modes

| Mode | Use when | Output |
| --- | --- | --- |
| Plan | The task spans several steps, modules, or sessions | A short spec plus ordered, verifiable tasks |
| Execute | An agreed plan is ready to implement | Tasks done in order, each with its check result |
| Decision record | A material choice must outlive this conversation, or an existing record needs updating | A decision record in the repository's convention |

Unclear goals or acceptance criteria go to `rumo-clarify` first. A decision record can be maintained even for a small change when it owns the affected mechanism.

## Plan Mode

1. Inspect the real entry points, owners, tests, and repository instructions for the affected area.
2. Write the spec in a few lines each: goal, non-goals, constraints, acceptance criteria, and open decisions with recommended answers. When more than one design is viable and the choice changes an interface, stored data, or the amount of work, list two or three options with their trade-offs and a recommendation, and break the work down only after the user picks one. Options must differ in where the change lives, how data flows, or what it costs; the same design with another parameter or library is one option. Before recommending, check each option for these design smells: a layer that only forwards calls and hides nothing; one piece of knowledge, such as a file format or business rule, spread across several modules; modules split by execution order (read, process, write) instead of by the knowledge each owns; one piece of state written by more than one module; two supported ways to do the same task; and a list that must be kept in step by hand in several places. When the user wants another model's design to compare, hand it a read-only design brief through `rumo-agent-collaboration` and compare its draft with yours.
3. Break the work into tasks. Each task names the files or modules it touches, the check that proves it done, and what it depends on. Prefer thin end-to-end slices over layer-by-layer batches.
4. Mark tasks that need separate authorization: commits, tags, pushes, deployments, database writes, deletions, credential changes, dependency installs, and paid services.
5. Show the plan. When the user already authorized this scope and the plan adds no new decision, continue; otherwise wait for approval of that exact version, pausing only the tasks that depend on the open decision or authorization. A clarifying answer revises the plan; it is not approval.
6. While implementing, stop and revise the plan when a task turns out wrong or a hidden requirement appears; do not silently drift.

Save the plan where the user or repository wants it. Without a convention, keep it in the conversation rather than inventing a directory.

## Execute Mode

Work an agreed plan one task at a time, in dependency order.

1. Before a task, re-read the files it touches and the check it names.
2. After the task, run that check. Mark the task done only when the check passes, and record the command and result.
3. When a check fails, stay on that task until it passes or the plan needs revising; never start the next task on top of a failing one.
4. Report per task or small batch, and end with one line per task: done with its evidence, blocked with the reason, or not started.
5. When the plan lives in a file and the work spans several steps or sessions, keep a "Decisions and dead ends" section at its end: append one line for each fork, failure, or change of direction, with the date, the decision, why, where the evidence is, and the result. Record approaches that were tried and abandoned with the reason, so the next session does not try them again. Skip routine steps, and never edit or delete an earlier line; a reversed decision gets a new line.

Run tasks in parallel or in separate worktrees only when the user asks, and never run two tasks in parallel when they touch the same files. Read [references/parallel-execution.md](references/parallel-execution.md) before doing so.

## Decision Record Mode

Read [references/decision-records.md](references/decision-records.md) before writing or moving a record.

- Search for an existing record that owns the same mechanism. Update it when only facts, paths, or evidence changed; write a new record that links the old one when the decision itself changed.
- Follow the repository's existing location, naming, numbering, and language. Without one, propose the default layout in the reference and ask before creating it.
- Do not mark a record implemented because code was drafted or unit tests passed; state the source, artifact, deployment, or field evidence that exists.
- A decision record never authorizes database writes, deployments, or other controlled actions.
- Do not create decision directories or policies during a review-only request.

## Report

For plans: the spec, the task list with checks, items needing separate authorization, and the approval status. For execution: each task's status with its check evidence. For records: status, path, superseded records, and evidence boundaries.
