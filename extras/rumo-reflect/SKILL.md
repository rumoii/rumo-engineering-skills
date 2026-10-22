---
name: rumo-reflect
description: Use only when the user explicitly asks to reflect on, review, or learn from the current session, such as "reflect", "复盘一下", or "what should the skills learn from this", or accepts an offer to review the session. Find recurring mistakes, user corrections, and skipped rules in the conversation, propose the strongest place to fix each one (a check, a pinned test, skill text, or project instructions), and discuss every item with the user, who decides; nothing changes without approval. Do not use for progress updates, end-of-task summaries, handoff documents (use rumo-handoff), or daily reports.
---

# Rumo Reflect

Turn what went wrong in this session into a fix the next session cannot miss, and change only what the user approves.

## Collect Candidates

Read the current conversation and the files it changed. Look for:

- corrections the user made, and repeated attempts or workarounds before something worked;
- a rule in a skill, `AGENTS.md`, `CLAUDE.md`, or memory that the agent broke;
- a skill that should have loaded and did not, or loaded when it should not have;
- a step that cost time and produced nothing.

Keep a candidate only when the situation will plausibly recur and a fix would change a future decision. Drop one-offs, matters of taste, and mistakes an existing rule already prevented. When a rule existed and was still broken, the candidate is why it was missed: its trigger wording, its placement, or a step that hides it.

Record for each candidate: what happened with its place in the conversation, the decision it would change next time, the proposed location, and the proposed change in one or two sentences.

## Pick The Strongest Place

Propose the first location that can hold the fix:

1. Remove the cause with structure, so the mistake can no longer be made: delete the outdated pattern an agent would copy, merge lists that must be kept in sync by hand into one source, or make the parser or validator reject the wrong form outright.
2. An automatic check the repository already runs: a validator, lint rule, script, test, or hook. Its error names the fix.
3. A pinned rule test, when the repository keeps one for skill text.
4. Skill text: the `description` when triggering failed, the body when a step was skipped or unclear.
5. Project instructions (`AGENTS.md`, `CLAUDE.md`) or the client's memory, for facts about one project or user.

For each candidate, say why each higher level cannot hold it. Prefer tightening an existing rule over adding a new one, and a new skill only when no skill owns the situation. Keep private project facts out of shared skills; put them in a project profile (`rumo-project-profile`) or the project's own files.

## Discuss, Then Decide

Show the candidates as a numbered table: lesson, evidence, proposed location, proposed change, and your recommendation (accept, reject, or backlog) with one line of reasoning. Then stop and wait.

The user decides every item. Apply only items the user explicitly accepts; a general "ok" accepts only the recommendations in the table shown. Backlog items go only where the user says; never open issues, tickets, or notes on your own. A changed proposal is a new item and needs its own approval.

## Apply

- Edit only the accepted items, at the agreed location. Follow `rumo-prose` for skill and instruction text when it is installed.
- Edit the source of a skill, not an installed copy that an update overwrites, such as a plugin cache. When the source is outside the current workspace or belongs to someone else, give the user the exact proposed edit instead of writing it.
- For a new check or pinned test, run it against the real mistake from this session and confirm that it fails, using the pre-fix version when the mistake was already corrected; a check that never caught the mistake proves nothing. Record the command and result.
- Run the checks the edited repository requires for those files.
- Do not commit or push unless the user asks; then follow `rumo-git-commit`.

## Stop Conditions

- Nothing in the session recurs or would change a decision: say so. Do not invent lessons to fill the table.
- A fix needs a product decision, another person's repository, or access you do not have: report it as a proposal and stop.

## Report

Applied items with path and one line each, rejected items with the user's reason, backlog items with where they were recorded, and the checks run on the changed files.
