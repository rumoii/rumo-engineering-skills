---
name: rumo-clarify
description: Use before implementing a request whose goal, scope, acceptance criteria, or a risky decision is still unclear, such as a vague feature ask, an open-ended change, or a task touching data, permissions, deletion, or external publication without a stated target. Ask at most one round of short questions with recommended answers, or go deeper only when the user asks to dig in. Do not use when the request is already specific, for pure questions, or for reviews.
---

# Rumo Clarify

Reach shared understanding with the fewest questions that matter, then get out of the way.

## 1. Decide Whether To Ask

If the goal, scope, and acceptance criteria are already clear, restate the understanding in one sentence and start. Asking about a clear request is a failure, not caution.

## 2. Look Before Asking

Answer facts yourself from the code, documentation, configuration, history, or environment. Ask the user only for decisions: intent, priorities, trade-offs, and authority.

## 3. Ask One Round

- At most five numbered questions, ordered by impact.
- Each question carries a recommended answer and one line on what changes if the user picks differently.
- Ask only questions that are answerable now; leave questions that depend on earlier answers for later.
- Tell the user they can reply "ok" to accept every recommendation listed in this round, or answer selectively, for example "2: use X".
- "ok" accepts only the recommendations shown in this round. It never approves anything that was not asked.

## 4. Sort What Remains Open

- **Preference** (naming, layout, wording, minor behavior): adopt the recommended default and list it as an explicit assumption.
- **Critical** (target environment or database, deletion scope, permissions, irreversible operations, external publication, money or quota): do not default it. Pause the work that depends on it, say what is blocked, and keep going only on parts that do not depend on it. Do not start a second round on your own.

## 5. Dig Deeper Only On Request

When the user asks to dig in, go deeper, or keep asking, switch to rounds: each round asks only the questions whose prerequisites are now settled, in the same format. Stop when nothing is open or the user says enough.

## 6. Hand Off

Write an understanding summary of at most ten lines: goal, in scope and out of scope, acceptance criteria, assumptions, and blockers. Then implement directly for a small task, or move to `rumo-plan` for multi-step or cross-module work.

## Authority

Answers to clarifying questions do not widen what the agent may do. Authorization the user already gave explicitly is not asked again.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "I'll ask everything to be safe." | Long questionnaires get skimmed; ask the five that change the outcome. |
| "I'll ask where the config lives." | That is a fact you can look up. |
| "No answer on the target database, so I'll use the obvious one." | Critical decisions are never defaulted; mark them blocked. |
| "They said ok, so I can also push and deploy." | "ok" covers only the listed recommendations. |
| "The request is a bit vague, so I'll run the full interview." | One round is the default; deeper rounds are the user's call. |
