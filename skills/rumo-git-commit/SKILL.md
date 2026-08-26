---
name: rumo-git-commit
description: Use when the user explicitly asks to commit, tag, release, push, clean up history, or land a worktree or feature branch. Follow repository conventions for branch selection, commit language, message format, verification, and release versioning.
---

# Git Commit

Perform only the Git operations explicitly requested by the user. Confirm the repository, worktree, current branch, upstream, target branch, outgoing scope, and dirty state before staging or changing history.

## Repository Conventions

Read `AGENTS.md`, `CONTRIBUTING.md`, release documentation, commit hooks, CI rules, and recent accepted history. Use their commit language and message format. If no reliable convention exists, follow the dominant recent history or ask when the choice materially affects acceptance.

Do not require a particular language, trailer set, version scheme, or branch pattern merely because this skill is installed. Optional private conventions may come from [`rumo-project-profile`](../rumo-project-profile/SKILL.md).

## Commit

- Stage only files belonging to the current task.
- Preserve unrelated tracked, staged, unstaged, and untracked work.
- Split atomic commits when changes are independently reviewable and each commit remains usable.
- Never create a tag unless the user explicitly asks for tagging or release work.
- Never push unless the user explicitly asks.

Before a requested push, use [`rumo-change-verification`](../rumo-change-verification/SKILL.md) on the exact outgoing diff. Reuse still-valid evidence rather than rerunning unchanged checks.

## Branch Landing

Prefer the user-named target. Otherwise resolve the target from repository documentation, the remote default branch, upstream configuration, or an unambiguous long-lived branch. Do not invent product branch patterns.

When the source is a worktree or feature branch:

1. Commit the task on the source branch.
2. Require a clean target worktree.
3. Fetch and inspect divergence.
4. Fast-forward when only behind.
5. Stop on divergence unless the user chooses merge or rebase.
6. Precheck conflicts with `git merge-tree` when available.
7. Prefer cherry-pick for a linear landing unless topology must be preserved or the user requested merge.
8. Verify the landed state before push.

History rewriting, interactive rebase, force push, deleting branches, and replacing tags require a preview and explicit confirmation because they can invalidate other clones or references.

## Release

Use the repository-owned versioning and release mechanism. Run the bundled `scripts/calver.py` only when the repository explicitly adopts its CalVer scheme or the user specifically requests it. Tag the final landing commit, never an intermediate worktree commit.

Report commits created, branches affected, verification executed, push or tag results, and any remote divergence or acceptance boundary not verified.
