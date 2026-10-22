# Project Verification Recipe

A recipe records, once and proven, how to verify a project's real behavior: start it, confirm it is usable, drive a feature the way a user would, keep the proof, and clean up. The next agent reads it cold in the middle of a task, so every step is concrete and taken from this repository.

## Investigate The Repository

Answer these from the code, configuration, and documentation; ask the user only what you cannot observe:

- **Surface:** what a user touches, such as a web UI, CLI, service API, desktop or mobile app, or library. When there are several, pick the primary one and list the rest.
- **Launch:** the repository's own start commands, ports, environment variables, seed data, migrations, and sign-in. Use `rumo-frontend`'s dev-server reference for frontend start-up and `rumo-project-profile` for runtime facts the repository does not hold.
- **Drive:** existing automation first, such as browser test specs, CLI scripts, or plain HTTP requests, then a generic harness.
- **Observe:** what can serve as proof: screenshots, terminal transcripts, response bodies, logs, exit codes, stored data.
- **Isolate:** whether two instances can run side by side through separate ports, data directories, or profiles. If they cannot, the recipe says so and forbids driving an instance it did not start.

If the checkout does not build or start, fix that within the task's scope or report the exact failure before writing anything; a recipe written against a broken start teaches wrong steps.

## Choose The Location

The recipe is a skill named `verify-<app>` with its own `SKILL.md`, so the client can discover it.

| Repository | Location |
| --- | --- |
| Accepts committed agent files, such as the user's own repository | The client's project skill directory, committed with the code. Add one line to the project's `AGENTS.md` naming the recipe path, so clients that read another directory still find it. |
| Must not carry agent files, such as a fork that sends pull requests upstream or a repository whose rules forbid them | The client's user skill directory. Its `description` names the one repository it serves, and the recipe records the commit it was proven against. Every worktree and clone then shares one copy, and nothing reaches a pull request. |

Ask the user when you cannot tell whether the repository accepts committed agent files.

Client-specific paths: Claude Code reads project skills from `.claude/skills/` and user skills from `~/.claude/skills/`; Codex reads `.agents/skills/` and `~/.agents/skills/`. For other clients, use their documented skill directories, or put the recipe in the project's documentation and point to it from `AGENTS.md`. Do not share a recipe between clients through a symbolic link: on Windows without Git symlink support the link checks out as a plain text file.

## Write The Recipe

`SKILL.md` holds frontmatter with `name: verify-<app>` and a `description` naming the application, its surface, and when to use the recipe, followed by these sections, each filled from what the investigation found:

- **Launch:** the exact commands, and the sign that the application is usable rather than merely running, such as a page that renders after sign-in or an API call that returns data. Start from an empty data directory, including migrations and seed data, and include teardown. A short-lived CLI is built once and then run in a fresh isolated session for each drive.
- **Doctor:** one read-only check that this instance is worth driving: the process is up, the build or version is the expected one, the port belongs to this run, and sign-in is valid. Run it first and again whenever something looks wrong.
- **Drive:** commands and selectors that exist in this repository. Prefer stable handles such as accessible names, data attributes, routes, and prompt strings over coordinates or element order.
- **Evidence:** what to capture and where it goes. Drive the real user path, never internal setters or test-only endpoints; capture the action and the resulting state, and check side effects such as written files, stored rows, or sent messages. When a dry-run or test mode is the safe path, observe what it really skips instead of trusting its name.
- **Cleanup:** remove instances and scratch state this run created. Stop only processes this run started; never stop a process by name. Cleanup never deletes the evidence.
- **Helpers:** any script the recipe ships is runnable as shown in the recipe body.

Write every command relative to the repository root so it works in any checkout or worktree; never write one checkout's absolute path.

Add a feature map: `features/README.md` with baseline preconditions, driving conventions, and an index, plus one file per user-facing feature, starting with the three to five most important. Each feature file covers its sub-behaviors, every way a user reaches it, the drive steps with each action's exact command and observable result, and the traps that can waste or invalidate a run. When seed data lacks a precondition, the feature reports the failure and the trap is recorded; never weaken the steps to make them pass.

## Prove It Once

Run the recipe as written: launch, doctor, drive one mapped feature, capture evidence, clean up, then confirm the evidence still exists where the recipe says. Fix whatever fails and run cleanup after every failed attempt so no process or port is left behind. Until the recipe has run end to end, it is a draft. When you proved it in a stand-in environment, such as a local stack instead of a remote one, list each step the stand-in performed that the real target will not; those steps stay unverified.

## Maintain It

When asked to check a recipe, or when the default verify mode finds drift:

1. Read the feature index and fix missing, extra, or dead entries.
2. For each feature, compare the recipe with the current source and note likely drift with file references.
3. Launch once, run the doctor, and drive every feature, keeping the evidence through every cleanup.
4. Sort each problem: a wrong description is fixed in the recipe; working behavior the steps cannot drive is a harness gap, fixed in the recipe or its helpers and driven again; broken application behavior is a product defect. A product defect found during maintenance is reported, never written around in the recipe.
5. Edit only the recipe's own directory. Report one outcome: unchanged, corrected (with the changed files), or blocked (with the reason).

A feature that cannot be reached counts as unreachable only when the report names the missing precondition, such as sign-in, entitlement, platform, or external state, and the route attempted.

## Stop Conditions

- The launch needs credentials, a shared or remote environment, or writes to persistent data the user has not approved: stop and ask.
- The only available instance is one this run did not start: do not drive it; report the boundary.
- Generating the recipe would commit files to a repository whose rules are unclear: ask before writing.
