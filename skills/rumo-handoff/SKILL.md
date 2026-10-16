---
name: rumo-handoff
description: Use when the user asks to hand off, hand over, pause, or package the current task so another session, agent, or client can continue it. Write a self-contained handoff document with goal, decisions, repository state, verified and unverified results, next steps, and how to resume. Do not use for ordinary progress updates or end-of-task summaries.
disable-model-invocation: true
---

# Rumo Handoff

Write the document the next agent needs to continue without this conversation.

## Where It Goes

Use the location the user names. Otherwise follow the workspace's convention for task notes; if there is none, ask. Do not commit the document unless asked, and keep it out of product source trees by default.

## Gather Facts First

- Re-read the original request and every later decision the user made.
- For each repository involved: path, branch, HEAD, upstream, worktree status, and any worktrees or stashes this task created.
- Commits made in this task, and anything staged, unstaged, or untracked that belongs to it.
- Checks actually run, with commands and results.
- Running processes, terminals, servers, or remote sessions the next agent must know about.

Verify each fact now; do not copy it from memory.

## Document Structure

```markdown
# Handoff: <task>

## Goal
One or two sentences, plus acceptance criteria.

## Decisions
What the user decided, with the reason when it matters. Mark anything still open.

## State
Repositories, branches, commits, dirty files, processes, environments.

## Verified / Not Verified
What was checked and how; what remains unproven and why.

## Next Steps
Ordered, concrete actions. Mark steps that need user approval.

## Pitfalls
Traps already hit and how they were resolved.

## Resume
The exact commands or reads to get back to a known-good state.
```

## Rules

- Write for a reader with no access to this conversation; never say "as discussed above".
- Never include passwords, tokens, keys, or private certificate material; name where credentials live instead.
- Keep authorizations explicit: say what the user approved and what still needs approval. A handoff does not transfer approval for actions the user has not granted.
- Prefer facts over narrative and keep it short enough to read in two minutes.

## Report

Give the document path and a three-line summary: where the task stands, the next step, and anything blocked.
