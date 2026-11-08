---
name: rumo-handoff
description: Use when the user asks to wrap up ("收尾"), hand off, pause, or package a task so another session, agent, or client can continue it, or when a new session must pick up earlier work, such as asking for current progress, the next step, or where a topic stands ("汇报一下当前进度", "下一步做什么", "接着上次做", "回忆一下 X 做到哪了") or to continue another agent's session. Writes a handoff document when asked or when wrapping up leaves work open; picks up from this project's recent Claude Code, Codex, and Kimi Code sessions, checked against the repository. Do not use for a plain end-of-task summary.
---

# Rumo Handoff

Carry a task across sessions. Wrap up a task when the user asks. Write a handoff document when the user asks for one or a wrap-up leaves work open. In a new session, pick up from the earlier sessions' own records, which already exist, so an ordinary session end needs no document.

## Status Card

A status card is one short page per project that tells the user where it stands: what is theirs to do, what is done and how that is known, and which decisions are theirs. Handoff documents and plans stay the detail for agents. Read [references/status-card.md](references/status-card.md) before writing or updating one.

- Use the status file the workspace's instructions name; otherwise `STATUS.md` at the root of the main checkout. From a linked worktree, find the main checkout through `git rev-parse --git-common-dir` and update its card; never start a second one in the worktree.
- Write it for the user, in the user's language. Verify every fact in it now; where it disagrees with the repository, the repository wins.
- Record a decision as the user's only when the user made or confirmed it. A decision the agent made stays marked unconfirmed until the user confirms it.
- Do not commit it unless asked. Before committing it to a public repository, warn that it holds the user's decisions and local paths.

## Wrap Up

Use when the user says "wrap up" or "收尾", including "先收尾，明天继续". Do not report the wrap-up finished until every item below has a state you checked now.

Asking to wrap up authorizes the cleanup below and nothing else. It never commits, pushes, merges, or deploys; list what is uncommitted or unpushed.

1. **Inventory.** For each repository involved: branch, HEAD, upstream, dirty files, and worktrees. Also the terminals, agents, servers, and processes this task started, and any temporary settings it placed. Only what the session's record proves this task started counts as its own.
2. **Update records.** Bring the task's existing progress records, plan file, and the project's status card up to date: task status, decisions and dead ends, what remains. Do not create new records; when the project has no status card, offer to start one and write it once the user agrees.
3. **Clean up what is provably safe.**
   - An agent still running: leave it and report it.
   - A terminal this task opened, once its agent has ended and its result has been read: close it. Never close this session's own terminal or one the user opened.
   - A process or server this task started: stop it unless the user is still using it. Remove temporary settings this task placed.
   - A worktree this task created, when it is clean, its commits are on the target branch or it has none, no agent, including this session, runs there, and no kept worktree links into it: remove it without force, following `rumo-filesystem-safety` for ignored content and links, such as a `node_modules` linked to the main checkout. Delete its branch only with `git branch -d`; when that refuses, keep the branch and report it. In Orca, use Orca's own worktree and terminal commands.
   - An unmerged, dirty, linked-to, or unprovable worktree: keep it, say why, and ask what to do. Do not repair links during a wrap-up.
4. **Handoff document.** When anything remains unfinished, unverified, unmerged, or unpushed, write or update one as [Write A Handoff Document](#write-a-handoff-document) describes. When nothing remains, write none and say so.
5. **Report.** After re-checking the state, give what was cleaned, what was kept and why, the handoff path, the next step, and what needs the user's decision. List the decisions this session added to the status card and every unconfirmed one, ask the user to confirm or correct each, and update the card with the answers.

## Pick Up

Use when this session starts on work that an earlier session or agent did, and the user asks where things stand, what to do next, or to continue.

1. From the project directory, run `scripts/session_digest.py list`. It lists this project's recent Claude Code, Codex, and Kimi Code sessions, newest first, and never reads another project's session content. Discovery reads session ownership metadata before selecting this project's sessions. The newest may be this session: skip the one whose `last_user` is the current request. Sessions with `headless: true` were launched by another agent, such as a review lane; prefer the others.
   - When the user names a topic ("where is the recognition work"), has been away for days, or several lines of work may be open, list a window instead: `list --since 14 --limit 30`, adding `--grep '<term|synonym|English term>'` for a topic. `--grep` searches the user's messages, compaction summaries, and titles. Group the sessions into lines of work by their first and last user messages.
2. Read the project's status card first when it has one. Then run `scripts/session_digest.py show <id>` for the latest relevant session, and for one more when it stopped mid-task or points to an earlier one. With several lines of work, show only the latest session of each unfinished line, at most three, with `--budget 15000`. It keeps the user's messages, each turn's final reply, and the latest compaction summary. When the user names a session, such as `codex resume <id>` or `kimi --session <id>`, show that one. Also read any handoff document or plan file the record names.
3. Check the record against the repository: branch, HEAD, recent commits, dirty files, and any background runs it mentions. Where they disagree, the repository wins; say so.
4. When a status card exists, lead with it as written, then add where the sessions or the repository disagree with it and what happened after its last update. Report where the work stopped, what was done and verified, what is unfinished or unverified, the recommended next step, and which steps need the user's approval. Treat the record's decisions as settled and do not redo verified work; re-check only what the repository contradicts. With several lines of work, give each one line led by one status checked against git, in the user's language: pushed, committed but not pushed, uncommitted and verified, uncommitted and unverified, in progress on a branch, reverted, planned but not started, or dropped. Then list at most five recurring problems or dead ends, and end with the single most useful next step.
5. Stop after the report unless the user asked to continue. Approvals in the record covered that session; ask again before commits, pushes, deployments, and other actions that need authorization. Never repeat credentials that appear in a record.

Without session files, such as work from another machine, ask for a handoff document or where the session's record is.

## Write A Handoff Document

Write the document the next agent needs to continue without this conversation, only when the user asks for one or a wrap-up leaves work open.

### Where It Goes

Use the location the user names. Otherwise follow the workspace's convention for task notes; if there is none, ask. Do not commit the document unless asked, and keep it out of product source trees by default.

Make the handoff discoverable without this conversation. When the workspace's own instructions name a task index, status document, or handoff registry that the next agent reads, add a concise link there with the current state and check that it resolves. Do not edit other tracked files, such as a product README, to point at an uncommitted handoff, and do not create a parallel documentation system. Otherwise give the user the exact path to pass to the receiving agent; ask where to link it when the user expects automatic discovery.

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
- Writing a handoff covers the document and its necessary navigation link only. To start the receiving agent and confirm it took over, use `rumo-agent-collaboration` after the user authorizes that route. If the skill or route is unavailable, give the user the document and stop.

### Report

Give the document path, how the next agent will discover it, and a three-line summary: where the task stands, the next step, and anything blocked.
