---
name: rumo-filesystem-safety
description: "Use when about to delete or bulk-clean files or directories, or when writing a cleanup script intended for later execution, even if it is not run now: recursive or wildcard removal, git clean or reset --hard that discards working-tree content, purging build outputs or caches, or deleting untracked or ignored content. Scale the review to the blast radius, and never treat writing a script as authorization to execute it. Do not use for database data cleanup (use rumo-database-change-safety) or source-file removal within a requested refactor."
---

# Rumo Filesystem Safety

Prevent accidental filesystem deletion by matching the review effort to the blast radius. This skill is guidance, not an enforcement hook: an agent can still bypass it with a direct command or another tool.

Writing or editing a cleanup script does not authorize running it. Apply the same target, boundary, link, and preview rules to the script's future effects; execute deletion only when separately authorized.

## Choose The Path

Use the light path only when every one of these holds:

- The user named a few exact paths (about 1-5); each can be identified without enumeration or expansion.
- Each target is an ordinary file or directory inside the authorized workspace; no subtree needs surveying.
- No wildcards, empty variables, or assumptions about the current directory are used to build the paths.
- The content is known to be disposable: regenerable (build output, cache, temporary file), Git-tracked, or explicitly named by the user as something to remove.

Use the full path whenever any of these applies:

- Recursive removal, whole-directory cleanup, wildcards, or a path count that is not enumerated one by one.
- Batch-destructive commands such as recursive `rm`, `Remove-Item -Recurse`, `git clean -fdx`, `git reset --hard`, or `find -delete`, judged by their actual targets and effects, not by familiar names.
- Targets outside the established workspace, or a workspace boundary that is not yet confirmed.
- Untracked or ignored content whose value is unknown; ignored files are not automatically disposable.
- A cleanup command or script that will run repeatedly.
- Suspected symbolic links, Windows junctions, or other reparse points among the targets or their parent directories.
- Removing something because it duplicates another path.

## Light Path

- Echo the exact paths to be removed and resolve each through every component, not only the last, to confirm what it really is and that it lies inside the authorized workspace. If a named target is itself a link, remove only the link node.
- Delete directly under the recovery policy — no preview inventory, no tracked/untracked audit.
- Report in one line: what was removed and by what method.

## Full Path

### Identify The Target

- Establish what the user authorized, the owning workspace, and the exact files or directories to remove. A request to clean one path does not authorize deleting its parent or neighboring paths.
- Inspect the target's current contents before recursive cleanup. In a Git repository, check tracked, untracked, and ignored contents that could be affected.
- Do not construct deletion paths from empty or unchecked variables, broad wildcards, or assumptions about the current directory.
- Removing a duplicate requires proof that the copies are separate objects: their fully resolved paths, or file IDs, differ. Identical content and timestamps in several places are what one object seen through links looks like, not evidence of independent copies.

### Check The Boundary

- Confirm each target's absolute location and its parent path before deletion. Stop if a target falls outside the authorized workspace or resolves to a filesystem root, user home, system directory, repository root, or Git metadata without explicit scope for that target.
- Identify symbolic links, Windows junctions, and other reparse points on every component of each path before deleting, not only on the target: a linked parent directory makes `a/skills/x` and `b/skills/x` the same directory. Do not traverse a link to delete its destination. If only the link itself is in scope, use a platform-appropriate non-recursive operation; stop when its behavior is uncertain.
- Do not infer safety from a familiar command name or a clean Git status.

### Preview And Confirm

- Show the concrete affected paths and any uncommitted or otherwise irreplaceable contents before a broad or recursive deletion. If such contents were not explicitly included in the request, stop and ask the user before proceeding. Recheck the target immediately before execution if the filesystem may have changed.
- When a batch-destructive command's actual effect exceeds what the request clearly authorizes, list that effect and obtain confirmation before running it.

### Delete

- Keep cleanup commands bounded to the approved targets. If path expansion, link handling, or the deletion tool's behavior is unclear, stop and explain the uncertainty.
- If a deletion failed or only partly completed, report the remaining state without retrying against a broader path.

## Recovery Policy

- Recoverability is optional, never a precondition. Do not block or complicate a deletion merely because it would be irreversible.
- Permanent deletion is fine when the user asked for that deletion, the content is regenerable (build outputs, caches, temporary files, generated artifacts), or the paths are Git-tracked and recoverable from history.
- The operating-system trash (recycle bin) is a convenience option when the content is non-regenerable and the request does not clearly authorize permanent destruction. Using it is never required.
- Never create ad-hoc backup copies as part of a deletion: no `.bak` files, `*_backup` copies, `*.orig` files, timestamped duplicates, or side-by-side backup directories. If the user explicitly asks for a backup, write it only to a user-named destination outside the tree being deleted.

## Report

State what was removed, what was skipped, the method used (permanent deletion or operating-system trash), and the realistic recovery path: trash location, Git history, or none. Do not invent a recovery path that does not exist.

## Related Skills

- Use [`rumo-coding-guidelines`](../rumo-coding-guidelines/SKILL.md) to keep code changes within the requested scope.
- Use [`rumo-verify`](../rumo-verify/SKILL.md) to verify the exact changed files before delivery.
- Use [`rumo-database-change-safety`](../rumo-database-change-safety/SKILL.md) for destructive cleanup of persisted database data; this skill covers filesystem paths.
