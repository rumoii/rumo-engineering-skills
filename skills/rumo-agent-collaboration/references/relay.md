# Development Relay

Read for an explicitly requested multi-stage relay across agents, including develop, review, and fix even when the user does not name verification. Use this recipe to prepare bounded stages and pass evidence between owners. It does not schedule agents, resume a session automatically, or replace the execution routes in SKILL.md. It also works in clients without a scheduler: the current owner prepares each next step using the available, authorized route.

## Set The Sequence

Name the requested outcome, stages, acceptance checks, and owner of each stage. Keep research or design proportional to unresolved questions; use rumo-research for investigation and rumo-plan for design decisions and task order. If a needed skill is unavailable, state the gap and prepare the same bounded brief with the available tools.

Use rumo-review for the review stage and its [finding categories](../../rumo-review/references/loop.md#cycle) to distinguish must-fix findings from optional improvements. This classification does not start a loop. For external reviewers, follow its [panel rules](../../rumo-review/references/panel.md), including single-lane execution. A relay does not turn a review-only request into permission to fix.

- For a one-pass relay, the coordinator checks the fixes, then proceeds to verification without automatically starting another independent review. Report that the fixes were not independently re-reviewed; do not label the modified target review-approved. If another review is needed, follow the review route's authorization rules, reusing approval that already covers it.
- Only when the user requests a repeat-and-repair sequence, follow the [review loop](../../rumo-review/references/loop.md). The relay adds no default cycle or fix-attempt limit.

## Stage Contracts

| Stage | Minimum input | Required output and check | Next owner |
| --- | --- | --- | --- |
| Research, when needed | Question, constraints, available sources, evidence limits | Source-backed findings, unresolved questions, and implications; check material claims and source relevance | Designer or developer, named in the result |
| Design, when needed | Goal, research conclusions, current implementation, constraints | Chosen approach, alternatives that affect the decision, contracts and acceptance checks; check feasibility against the actual code and consumers | Developer |
| Develop | Agreed behavior and scope, target state, design when present, write boundaries, acceptance checks | Changes, regression evidence where required, commands actually run, and remaining gaps; the coordinator checks the result under SKILL.md before review | Reviewer |
| Review | Intent, exact target, repository guidance, review standard | Findings with trigger, consequence, and file-and-line evidence, or no actionable findings with limits; the coordinator validates each finding against the current code before assigning a fix | Fixer for confirmed must-fix findings or other fixes the user requested; verifier when none remain |
| Fix | Validated findings, current target, authorized write scope, required regression evidence | Each assigned finding fixed or resolved with evidence, changed files, and focused check results; the coordinator checks the fixes against the current target | Verifier for a one-pass relay; reviewer for an authorized loop |
| Verify | Final target, acceptance checks, relevant review decisions, known gaps | Fresh check results tied to that target, untested boundaries, and an acceptance decision under rumo-verify | Coordinator for the final report, or the named next owner if blocked |

The coordinator remains responsible for accepting delegated results. Stage owners do not transfer overall task ownership unless the user's request meets the transfer rule in SKILL.md. Keep a single writer active for the target; reviewers read only, and a fixer starts only after the preceding writer has stopped and the coordinator has accepted the handoff.

## Pass The Context

Give each stage a small brief containing:

- The requested outcome, scope, constraints, existing authorization, and stop conditions.
- The repository and worktree, branch and HEAD, comparison base when applicable, and the relevant staged, unstaged, and untracked changes. Identify dirty content with an inspectable snapshot or diff and untracked-file contents or digests; HEAD alone does not identify that target.
- The stage's minimum input, the files and evidence it must read, expected output location, and the exact acceptance command or observation.
- Relevant earlier artifacts and verified conclusions, unresolved questions, and which claimed results remain unverified.
- The current owner, the next owner, and the condition that hands work to that owner.

Pass only the context the recipient needs. Keep fix history, earlier findings, and coordinator conclusions out of an independent reviewer's brief, as the review loop and panel require; preserve them for the coordinator and fixer. Do not treat a receiver's summary as proof of the code or checks.

Tie every review and verification result to the exact target state it inspected. Reconcile later file changes before reusing the result, and repeat the affected checks when it no longer covers the target. A failed, incomplete, or stale result is not a pass. No findings from a completed review does not replace final verification; a reviewer that failed or returned no usable review supplies no such result.

## Wait, Pause, And Resume

Follow the route's existing launch-and-wait contract. After launching an external CLI, tell the user where it runs, where its result will be, and how completion becomes known, then end the turn as SKILL.md requires. The recipe does not promise that the next stage starts in the background; continue only when the route makes the result available and the coordinator can accept it.

When pausing or blocked, record completed stages separately from failed, incomplete, and pending stages, together with the target state, artifact and run IDs, current owner, next action, and any missing input. Preserve partial changes and existing failing-test evidence. For a later conversation, read [records.md](records.md) and reconcile the actual session, files, and owner before continuing. Do not relaunch a writer while the previous writer's state is uncertain.

Finish with the accepted target, stages completed, validated findings and resolutions, commands actually run, remaining gaps or blockers, and the current owner. Report an interrupted sequence as partial; never call the whole relay complete because its last agent stopped.
