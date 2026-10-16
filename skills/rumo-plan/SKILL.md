---
name: rumo-plan
description: Use when turning an agreed multi-step or cross-module task into a short spec and verifiable task breakdown before implementation, or when creating, updating, superseding, implementing, or rejecting a durable engineering decision record (ADR) for a cross-module contract, data or wire format, permission model, lifecycle rule, deployment topology, migration, or rollback strategy. Do not use for single-file fixes, mechanical edits, or choices already owned by a current decision record; settle unclear goals with rumo-clarify first.
---

# Rumo Plan

Make the work and its reasons explicit before they become code.

## Modes

| Mode | Use when | Output |
| --- | --- | --- |
| Plan | The task spans several steps, modules, or sessions | A short spec plus ordered, verifiable tasks |
| Decision record | A material choice must outlive this conversation, or an existing record needs updating | A decision record in the repository's convention |

Unclear goals or acceptance criteria go to `rumo-clarify` first. A decision record can be maintained even for a small change when it owns the affected mechanism.

## Plan Mode

1. Inspect the real entry points, owners, tests, and repository instructions for the affected area.
2. Write the spec in a few lines each: goal, non-goals, constraints, acceptance criteria, and open decisions with recommended answers.
3. Break the work into tasks. Each task names the files or modules it touches, the check that proves it done, and what it depends on. Prefer thin end-to-end slices over layer-by-layer batches.
4. Mark tasks that need separate authorization: database writes, deployments, pushes, deletions, paid services.
5. Show the plan and wait for approval of that exact version before implementing. A clarifying answer revises the plan; it is not approval.
6. While implementing, stop and revise the plan when a task turns out wrong or a hidden requirement appears; do not silently drift.

Save the plan where the user or repository wants it. Without a convention, keep it in the conversation rather than inventing a directory.

## Decision Record Mode

Read [references/decision-records.md](references/decision-records.md) before writing or moving a record.

- Search for an existing record that owns the same mechanism. Update it when only facts, paths, or evidence changed; write a new record that links the old one when the decision itself changed.
- Follow the repository's existing location, naming, numbering, and language. Without one, propose the default layout in the reference and ask before creating it.
- Do not mark a record implemented because code was drafted or unit tests passed; state the source, artifact, deployment, or field evidence that exists.
- A decision record never authorizes database writes, deployments, or other controlled actions.
- Do not create decision directories or policies during a review-only request.

## Report

For plans: the spec, the task list with checks, items needing separate authorization, and the approval status. For records: status, path, superseded records, and evidence boundaries.
