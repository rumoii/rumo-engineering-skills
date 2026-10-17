# Parallel And Isolated Execution

Read this only when the user asks to run plan tasks in parallel or in isolation. Dispatching helpers is client-specific: it needs a client that can start a helper agent with a fresh context, such as a subagent. Without one, run the tasks one at a time in Execute mode.

## Choose What Can Run Together

- Run two tasks in parallel only when they share no files, generated outputs, schema, or configuration, and neither needs the other's result.
- Keep a task that changes a shared contract, a migration, or a build setting serial, and run the tasks that depend on it after it lands.
- When in doubt, run serially. Parallel work saves time only when integration is trivial.

## Dispatch

- Give each helper only its task: the goal, the files in scope, the check that proves it done, the repository guidance, and the plan's constraints. Withhold the planning conversation and other tasks' details.
- A helper does not commit, push, install dependencies, or touch files outside its scope. It reports the files it changed, the check it ran with the result, and anything it could not finish.

## Isolate

- When helpers would edit the same working tree at once, give each its own git worktree on its own branch from the same base commit, and record each path and branch.
- Land each branch through the branch-landing steps in `rumo-git-commit`. Stop on a conflict and ask; do not resolve it silently.
- Remove a worktree only after its branch has landed or the user discards it, following `rumo-filesystem-safety`.

## Accept Each Result

- Have a fresh-context helper review each result against the task's goal and the review standard in `rumo-review`, without the implementer's reasoning.
- Rerun the task's check yourself on the integrated result. A task is done when that check passes after integration, not when its helper says so.

## Report

Per task: the helper's outcome, review findings, the integrated check result, and the branch or worktree it came from.
