---
name: rumo-handoff
description: Use when the user asks to hand off, hand over, pause, or package the current task so another session, agent, or client can continue it, or when a new session must pick up earlier work, such as asking for the current progress or the next step ("汇报一下当前进度", "下一步做什么", "接着上次做") or to continue another agent's session. Writes a self-contained handoff document only when asked; picks up by condensing this project's recent Claude Code and Codex sessions and checking them against the repository. Do not use for an end-of-task summary within the same session.
---

# Rumo Handoff

Carry a task across sessions. Write a handoff document when the user asks for one; in a new session, pick up from the earlier sessions' own records, which already exist, so nothing has to be written at the end of a session.

## Pick Up

Use when this session starts on work that an earlier session or agent did, and the user asks where things stand, what to do next, or to continue.

1. From the project directory, run `scripts/session_digest.py list`. It lists this project's recent Claude Code and Codex sessions, newest first, and never reads another project's. The newest may be this session: skip the one whose `last_user` is the current request. Sessions with `headless: true` were launched by another agent, such as a review lane; prefer the others.
2. Run `scripts/session_digest.py show <id>` for the latest relevant session, and for one more when it stopped mid-task or points to an earlier one. It keeps the user's messages, each turn's final reply, and the latest compaction summary. When the user names a session, such as `codex resume <id>`, show that one. Also read any handoff document or plan file the record names.
3. Check the record against the repository: branch, HEAD, recent commits, dirty files, and any background runs it mentions. Where they disagree, the repository wins; say so.
4. Report where the work stopped, what was done and verified, what is unfinished or unverified, the recommended next step, and which steps need the user's approval. Treat the record's decisions as settled and do not redo verified work; re-check only what the repository contradicts.
5. Stop after the report unless the user asked to continue. Approvals in the record covered that session; ask again before commits, pushes, deployments, and other actions that need authorization. Never repeat credentials that appear in a record.

Without session files, such as work from another machine, ask for a handoff document or where the session's record is.

## Write A Handoff Document

Write the document the next agent needs to continue without this conversation, only when the user asks for one.

### Where It Goes

Use the location the user names. Otherwise follow the workspace's convention for task notes; if there is none, ask. Do not commit the document unless asked, and keep it out of product source trees by default.

### Gather Facts First

- Re-read the original request and every later decision the user made.
- For each repository involved: path, branch, HEAD, upstream, worktree status, and any worktrees or stashes this task created.
- Commits made in this task, and anything staged, unstaged, or untracked that belongs to it.
- Checks actually run, with commands and results.
- Running processes, terminals, servers, or remote sessions the next agent must know about.
- Approaches tried and abandoned. Copy the plan's decisions and dead ends when the task has a plan file, then add any the conversation shows that it does not.

Verify each fact now; do not copy it from memory.

### Document Structure

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

## Tried And Dropped
Approaches tried and abandoned, each with why and where the evidence is.

## Pitfalls
Traps already hit and how they were resolved.

## Resume
The exact commands or reads to get back to a known-good state.
```

### Rules

- Write for a reader with no access to this conversation; never say "as discussed above".
- Never include passwords, tokens, keys, or private certificate material; name where credentials live instead.
- Keep authorizations explicit: say what the user approved and what still needs approval. A handoff does not transfer approval for actions the user has not granted.
- Prefer facts over narrative and keep it short enough to read in two minutes.
- This skill writes the document only. To start the receiving agent and confirm it took over, use `rumo-agent-collaboration` after the user authorizes that route. If the skill or route is unavailable, give the user the document and stop.

### Report

Give the document path and a three-line summary: where the task stands, the next step, and anything blocked.
