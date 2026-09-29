---
name: rumo-filesystem-safety
description: Use when an agent is asked to delete files or directories, clean build outputs or caches, or write a cleanup command or script. Confirm the exact target and workspace boundary, inspect links before recursion, preview the affected paths, and prefer recoverable deletion. This skill guides decisions but does not intercept commands.
---

# Rumo Filesystem Safety

Prevent accidental filesystem deletion by checking the target before acting. This skill is guidance, not an enforcement hook: an agent can still bypass it with a direct command or another tool.

## Identify The Target

- Establish what the user authorized, the owning workspace, and the exact files or directories to remove. A request to clean one path does not authorize deleting its parent or neighboring paths.
- Inspect the target's current contents before recursive cleanup. In a Git repository, check tracked, untracked, and ignored contents that could be affected; ignored files are not automatically disposable.
- Do not construct deletion paths from empty or unchecked variables, broad wildcards, or assumptions about the current directory.

## Check The Boundary

- Confirm each target's absolute location and its parent path before deletion. Stop if a target falls outside the authorized workspace or resolves to a filesystem root, user home, system directory, repository root, or Git metadata without explicit scope for that target.
- Identify symbolic links, Windows junctions, and other reparse points before recursive operations. Do not traverse a link to delete its destination. If only the link itself is in scope, use a platform-appropriate non-recursive operation; stop when its behavior is uncertain.
- Treat commands such as recursive `rm`, `Remove-Item -Recurse`, `git clean -fdx`, and `git reset --hard` as destructive according to their actual targets and effects. Do not infer safety from a familiar command name or a clean Git status.

## Preview And Delete

- Show the concrete affected paths and any uncommitted or otherwise irreplaceable contents before a broad or recursive deletion. Stop if such contents were not explicitly included in the request. Recheck the target immediately before execution if the filesystem may have changed.
- Prefer a recoverable move or operating-system trash when it fits the task. Use permanent deletion only when its irreversible effect is authorized for the exact target.
- Keep cleanup commands bounded to the approved targets. If path expansion, link handling, or the deletion tool's behavior is unclear, stop and explain the uncertainty.

## Report The Result

State what was removed, what was skipped, the method used, and how to restore recoverable items. If a deletion failed or only partly completed, report the remaining state without retrying against a broader path.

## Related Skills

- Use [`rumo-coding-guidelines`](../rumo-coding-guidelines/SKILL.md) to keep code changes within the requested scope.
- Use [`rumo-change-verification`](../rumo-change-verification/SKILL.md) to verify the exact changed files before delivery.
