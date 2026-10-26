# Task Flows

Each flow is the default route for one kind of task: when it applies, its steps, which skill owns each step, and where to stop. Pick the flow that matches the request. When a task changes kind midway, such as an investigation the user turns into a fix, switch flows and say so. Skip a step only with a reason you state in the final report.

None of these flows commits, pushes, merges, deploys, or writes to a shared environment on its own; those keep their separate approvals.

## Everyday Work

- **Small edit.** A wording, configuration, or one-place code change with an obvious result. Read the code, make the edit, run the most relevant check, then `rumo-verify`. No plan and no review.
- **Defect fix.** A reported bug the user wants fixed. `rumo-debug` reproduces it and proves the cause; a failing test captures it (`rumo-test`); the fix turns it green and the surrounding tests still pass; the project's verification recipe drives the real feature when one exists; then `rumo-verify`. When the bug will not reproduce, report what was tried instead of patching a guess. After two failed fixes, test the premise ([principles.md](principles.md)).
- **Feature.** New or changed behavior. `rumo-clarify` when the goal or acceptance is unclear, `rumo-plan` when the work spans several steps or modules, the risk gate, thin end-to-end slices that each still work, the verification recipe when one exists, then `rumo-verify`. `rumo-review` only on request.
- **Investigation.** A question about how something works, why it was built that way, or which option to choose. Stay read-only and answer with file, line, and runtime evidence; for a choice between options, give a recommendation with its trade-offs.
- **Resume.** Continuing work another session or agent started. When the user names no record, find it with `rumo-handoff`'s Pick Up. Read the handoff document, the plan's decisions and dead ends, or the run record. The record may be another CLI's session, such as one named by `codex resume <id>`: read that session from the CLI's own session files and continue the work yourself; resuming it inside that CLI is delegation, which only the user can ask for. Then check the repository's actual branch, commits, and dirty files against them; name the resume point; then continue under the flow that fits the remaining work. Do not redo work the record shows as done and verified, but do not trust a claim the repository contradicts.
- **Refactor.** A change to structure that must keep behavior. Confirm that existing tests cover the behavior being moved, and add characterization tests first when they do not; move in small steps that keep those tests green; rerun the same tests unchanged at the end. Delete the old path once every caller has moved instead of keeping both. See Delete Before Adding and Keep The Reader's Load Small in [principles.md](principles.md).

## Measurement

- **Performance problem.** Something is too slow or uses too much memory. Measure a baseline with fixed data, environment, and command; find the hot path with a profiler or trace; fix it; measure again the same way and report both numbers with the method. Repeat the measurement when the numbers vary between runs. Never claim it got faster without a measurement taken the same way before and after. Explain the number before reporting it ([principles.md](principles.md)).
- **Metric improvement.** Sustained work to move one number toward a target, such as start-up time or bundle size. Fix the measurement first and show that it detects a change; record every attempt as one line in the plan's decisions and dead ends, with the hypothesis, the change, the before and after values, and whether it was kept or reverted; revert any attempt that does not help. Stop when the target is met or the remaining ideas are not worth their cost. Never loosen the target to declare success.

## Diagnosis And Exploration

- **Runtime diagnosis.** A leak, a busy loop, a visual glitch, or a profile, trace, or heap snapshot captured earlier. Capture the live signal or read the artifact, narrow it to one mechanism, confirm the mechanism with added logging or a probe, and map it to a source file and line (`rumo-debug`). This flow ends with a diagnosis; a fix needs its own request.
- **Prototype.** A cheap, throwaway build to make one design or behavior decision. Name the decision first. If you cannot name the decision, it is not a prototype; use the feature flow. Build outside the product source tree with the lightest stack that shows the idea; put alternatives behind one switch and make uncertain parameters adjustable; observe or screenshot each variant; recommend one. Prototype code never enters the product: the chosen direction is built again under the feature flow.
- **Visual parity.** Making a UI match another implementation, or migrating its styling, without visible change. Capture baseline screenshots of every state before changing anything, migrate one component at a time, and compare each against its baseline; investigate any nonzero difference (`rumo-frontend`). Never edit the baseline or the comparison tool to make a diff pass; if the baseline looks wrong, stop and ask.

## Repository Workflows

- **Skill or prompt change.** Editing a `SKILL.md`, agent instructions, or a prompt. Write it with `rumo-prose`, run the repository's validators, and when the change alters triggering or behavior, run the repository's evaluation cases for it before calling it ready.
- **Pull request follow-up.** Only when the user asks to watch or fix an open pull request (`rumo-git-commit`). Resolve conflicts first, then review comments, then failing checks; classify a failure before rerunning it. Never merge the pull request or mark it ready.
- **Pause.** The user stops the work, or the session must end before the task is done. Finish or back out of the current step and start nothing new; take no irreversible action to pause. Write a resume note with `rumo-handoff` when the user wants one, or report the state in the final message. Leave the changes as they are; commit only when the user asks.
