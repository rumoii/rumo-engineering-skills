---
name: rumo-prose
description: Use when writing, reviewing, or trimming prose in a software repository, including Markdown, code and test comments, JavaDoc/JSDoc, diagnostics, logs, API errors, configuration descriptions, UI strings, prompts, and agent-facing files such as SKILL.md, AGENTS.md, and CLAUDE.md. Keep every behavior and failure fact while removing repetition, narration, and session residue. Do not use for formal Word delivery documents.
---

# Rumo Prose

Write as much as a maintainer, caller, operator, or user needs to act correctly, and no more. Cut words only after every fact they carried survives somewhere.

## Scope And Authority

- A review or audit reports findings; a write, fix, or trim request authorizes edits inside the named scope.
- Check wording against the code, configuration, schema, or runtime behavior it describes before judging it.
- Edit generated text at its source. Leave fixtures, snapshots, vendored files, and historical records alone unless they are the explicit target.
- Prompts, API errors, and product strings are behavior: update their tests or snapshots when wording changes what users or models see.

## Keep The Facts

Before shortening a passage, list what it asserts: who acts, under which condition and order, what is required or forbidden, side effects and cleanup, failure and recovery, authorization and data scope, compatibility, and any guarantee that something does not happen. The shorter version must still assert all of them. Keep a non-obvious reason when dropping it would invite misuse; otherwise point to where the reason lives.

## Standards By Surface

| Surface | Write |
| --- | --- |
| Public API docs | caller-visible behavior that types do not show: failures, side effects, threading, cancellation, ownership |
| Code comments | the constraint or reason behind non-obvious code, never a restatement of the next line |
| Tests | the behavior and condition being pinned |
| Errors | the failed operation, the target, a safe next step, and a stable category, without secrets |
| Logs | correlation fields and state transitions needed to diagnose, without credentials or full payloads |
| UI strings | product language naming the action and its consequence, with no implementation terms |
| Repository Markdown | current behavior in present tense; rationale belongs in a decision record |

## Remove Session Residue

Durable text must make sense to someone who never saw the chat, review, or plan that produced it. Remove review ordinals without a committed owner, phrases like "this change" or "later PR", reviewer-directed asides, references to uncommitted plans, and "used to / now" stories on current-state surfaces. Rewrite any real fact they contain in the present tense.

## Agent-Facing Files

Read [references/agent-docs.md](references/agent-docs.md) before writing or reviewing a SKILL.md, AGENTS.md, CLAUDE.md, or a reusable prompt.

## Verify And Report

Re-read each edited passage against its source of truth, search the changed scope for stale terms or duplicated statements, and run the checks the surface requires. Report the scope, the kinds of changes, the evidence used, and any wording that still needs a product decision.
