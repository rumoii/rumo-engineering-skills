# Review And Fix Loop

Use only when the user explicitly asks to review, fix, and repeat until no blocking finding remains. Every pass applies the review standard in SKILL.md; this file adds the repeat-and-repair control. It does not authorize commits or pushes.

## Target

Settle one target before starting: uncommitted changes (default after a fix), a base branch, a commit, or a custom instruction. Record repository, branch, and worktree status. With several repositories, run a separate loop for each.

## Review Backends

Prefer an independent fresh context, but never hard-code a provider. Use the lane the user names for this loop; otherwise use the configured `review` lane. If no lane is configured or the choice is materially ambiguous, ask instead of defaulting to Codex or another provider.

Before the first external review, name the backend, model, diff and repository guidance to send, and that repeated cycles may spend quota. One agreement covers later cycles on the same lane and content scope; ask again before changing either. Give the reviewer only the target, the review standard in SKILL.md, and the necessary repository guidance. Withhold the fix history and earlier findings so it reviews the code, not your reasoning. It reports findings and never edits code.

For a configured Codex lane, read [codex-app-server.md](codex-app-server.md) and run `scripts/app_server_review.py` for an independent thread and machine-readable result. For another configured lane, use the single-lane execution and record rules in [panel.md](panel.md), not a multi-model panel. A client-native fresh-context helper is also suitable when the user selects it.

If the selected route is unavailable, report it and either stop or use the current session with the user's agreement. Say when a review was not independent; never substitute another provider or start a panel to keep the loop going. A review panel of other models can replace or join the independent review only when the user asked for one; read [panel.md](panel.md) first.

## Cycle

1. Review the target.
2. Check each finding against the code with [judging-findings.md](judging-findings.md), then sort:
   - **Must fix:** P0, P1, P2, correctness bugs, data-loss or security issues, broken builds or tests, and findings explicitly marked as blocking.
   - **Consider:** P3, style, maintainability, unclear risk.
   - **Not actionable:** false positives (record why with file, line, or test evidence), items already fixed, items without enough evidence.
3. Fix only the must-fix items, inside the reviewed target.
4. Add the smallest regression test when a finding concerns behavior, data contracts, permissions, concurrency, or error handling.
5. Run focused verification: the exact tests, compile or lint, `git diff --check`; widen only when the blast radius requires it.
6. Review the same target again.

An unlabeled finding that clearly blocks acceptance counts as must fix. Do not loop on P3 or style unless the user asked for full polish. "Until the review is empty" means "until no blocking findings remain"; review tools often print summaries or suggestions forever.

## Stop Conditions

Choose the next cycle from new evidence, resolved findings, remaining risk, and cost; there is no default cycle or fix-attempt limit. Respect the user's explicit budget. When a finding recurs without information gain, stop that repair strategy, recheck its cause and the verification route, and use a different evidence-backed approach. If no safe approach can progress, report the missing input or condition instead of stacking patches.

Stop and report when:

- the latest review has no must-fix items (list remaining consider items separately);
- a fix needs a product decision, contract change, data migration, deployment, credentials, or changes outside existing authorization;
- verification fails for a reason outside the change and cannot be isolated;
- the user's budget is exhausted or they ask to stop.

## Safety

Preserve unrelated changes and never revert them. Re-read files before editing if the worktree changed during the loop. Tie every edit to a concrete finding.

## Report

The target and number of cycles, fixed must-fix findings, verification commands and results, remaining non-blocking findings, and the blocker if the loop stopped early.
