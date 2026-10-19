---
name: rumo-git-commit
description: Use when the user explicitly asks to commit, tag, release, push, clean up history, land a worktree or feature branch, open or update a pull request, or watch or fix the CI checks of an open pull request. Follow repository conventions for branch selection, commit language, message format, verification, and release versioning. Do not use merely because work is finished; without an explicit request, stop after rumo-verify.
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
- For substantive behavior changes, include a commit body explaining why the change is needed, the main changes, and verification actually performed; state when verification was not run. Only purely mechanical changes, such as formatting or spelling fixes, may use a title alone.
- After creating a commit, read its full message to confirm the intended title and body were saved before any authorized push.
- Never create a tag unless the user explicitly asks for tagging or release work.
- Never push unless the user explicitly asks.

Before a requested push, use [`rumo-verify`](../rumo-verify/SKILL.md) on the exact outgoing diff. Reuse still-valid evidence rather than rerunning unchanged checks.

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

## Pull Request

Open or update a pull request only when the user asks.

- Confirm the remote, source branch, and target branch, and that the source is pushed. Follow the repository's pull request template when one exists.
- Write the body in four parts: why the change is needed, what behavior changes, the verification actually run (taken from the `rumo-verify` report), and risks, rollback, and boundaries not verified.
- Add signatures, trailers, labels, and reviewers only as the repository convention or the user requires. Never merge it automatically, and do not edit someone else's pull request.
- Use the hosting platform's CLI or web interface; when neither is available, give the user the title and body to paste.

When the user asks to watch or fix the checks of an open pull request, read [references/pr-checks.md](references/pr-checks.md) first. Watching reports results only. A request to fix covers local fixes; committing and pushing them still need the user's explicit request, as above. Neither merges nor marks the pull request ready.

## Release

Use the repository-owned versioning and release mechanism. Run the bundled `scripts/calver.py` only when the repository explicitly adopts its CalVer scheme or the user specifically requests it. Tag the final landing commit, never an intermediate worktree commit.

Report commits created, branches affected, verification executed, push or tag results, and any remote divergence or acceptance boundary not verified.
