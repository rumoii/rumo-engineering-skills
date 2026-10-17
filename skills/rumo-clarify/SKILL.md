---
name: rumo-clarify
description: Use before implementing a request whose goal, scope, acceptance criteria, or a risky decision is still unclear, such as a vague feature ask, an open-ended change, or a task touching data, permissions, deletion, or external publication without a stated target. Group the questions that can be answered now, with recommendations; follow up only for newly exposed consequential decisions, or explore deeper when the user asks. Do not use when the request is already specific, for pure questions, or for reviews.
---

# Rumo Clarify

Reach shared understanding with the fewest questions that matter, then get out of the way.

## 1. Decide Whether To Ask

If the goal, scope, and acceptance criteria are already clear, restate the understanding in one sentence and start. Asking about a clear request is a failure, not caution.

## 2. Look Before Asking

Answer facts yourself from the code, documentation, configuration, history, or environment. Ask the user only for decisions: intent, priorities, trade-offs, and authority.

## 3. Group Answerable Questions

- At most five numbered questions, ordered by impact.
- Each question carries a recommended answer and one line on what changes if the user picks differently.
- Ask only questions that are answerable now; leave questions that depend on earlier answers for later.
- In a plain-text round, tell the user they can reply "ok" to accept every recommendation listed in this round, or answer selectively, for example "2: use X". When the client offers a structured question tool, put the recommended option first and leave out the "ok" line.
- "ok" accepts only the recommendations shown in this round. It never approves anything that was not asked.
- When you end the turn with questions unanswered, end on the questions, not on a completion report.

## 4. Sort What Remains Open

- **Preference** (naming, layout, wording, minor behavior): adopt the recommended default and list it as an explicit assumption.
- **Critical** (target environment or database, deletion scope, permissions, irreversible operations, external publication, money or quota): do not default it. Pause the work that depends on it, say what is blocked, and keep going only on parts that do not depend on it.

Follow up only when an earlier answer exposes a consequential decision that cannot be resolved safely from the repository. Group the newly answerable decisions and explain what the answer changes. Do not repeat settled questions. When an answer changes the goal, restate the new goal first. Do not ask one decision per round as each comes up.

## 5. Dig Deeper Only On Request

When the user asks to dig in, go deeper, or keep asking, switch to rounds: each round asks only the questions whose prerequisites are now settled, in the same format. Stop when nothing is open or the user says enough.

## 6. Hand Off

Write an understanding summary of at most ten lines: goal, in scope and out of scope, acceptance criteria, assumptions, and blockers. Then implement directly for a small task, or move to `rumo-plan` for multi-step or cross-module work.

## Example

Request: "Add an export feature to the order list."

Good round, after reading the code:

```text
Understanding: an export button on the order list page.
Found: the customer list already exports CSV through the shared export helper.

1. Format? Recommended: CSV, like the customer list. Excel would add a dependency.
2. Which rows? Recommended: the current filter result. All orders would need a background job.
3. Who may export? Recommended: anyone who can view the list. Restricting it adds a permission.

Reply "ok" to accept all three, or answer by number, e.g. "2: all orders".
```

Weak round: "Which framework is the frontend? Where is the order list? CSV or Excel or both? What file name? Which columns? Which date format? ..." It asks facts the code answers, offers no recommendations, and buries the one decision that changes the design.

## Authority

Answers to clarifying questions do not widen what the agent may do. Authorization the user already gave explicitly is not asked again.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "I'll ask everything to be safe." | Long questionnaires get skimmed; ask the five that change the outcome. |
| "I'll ask where the config lives." | That is a fact you can look up. |
| "No answer on the target database, so I'll use the obvious one." | Critical decisions are never defaulted; mark them blocked. |
| "They said ok, so I can also push and deploy." | "ok" covers only the listed recommendations. |
| "The request is a bit vague, so I'll run the full interview." | Ask the decisions needed now; an open-ended interview is the user's call. |
| "I'll ask about each decision as it comes up." | Drip-fed rounds interrupt the user again and again; collect the open decisions and ask them together. |
