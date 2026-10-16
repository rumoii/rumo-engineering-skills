# Review And Fix Loop

Use only when the user explicitly asks to review, fix, and repeat until no blocking finding remains. Every pass applies the review standard in SKILL.md; this file adds the repeat-and-repair control. It does not authorize commits or pushes.

## Target

Settle one target before starting: uncommitted changes (default after a fix), a base branch, a commit, or a custom instruction. Record repository, branch, and worktree status. With several repositories, run a separate loop for each.

## Review Backends

Prefer the most direct independent review surface; all of them feed the same loop:

1. When `codex app-server` is available, read [codex-app-server.md](codex-app-server.md) and run `scripts/app_server_review.py`. It gives an independent review thread and a machine-readable exit code.
2. Otherwise, or after two app-server attempts end without a valid review result, use the client's built-in review command if it has one (client-specific: for example `/review` in Codex or `/code-review` in Claude Code).
3. Otherwise, review in the current session following SKILL.md.

## Cycle

1. Review the target.
2. Sort findings:
   - **Must fix:** P0, P1, P2, correctness bugs, data-loss or security issues, broken builds or tests, and findings explicitly marked as blocking.
   - **Consider:** P3, style, maintainability, unclear risk.
   - **Not actionable:** false positives (record why with file, line, or test evidence), items already fixed, items without enough evidence.
3. Fix only the must-fix items, inside the reviewed change.
4. Add the smallest regression test when a finding concerns behavior, data contracts, permissions, concurrency, or error handling.
5. Run focused verification: the exact tests, compile or lint, `git diff --check`; widen only when the blast radius requires it.
6. Review the same target again.

An unlabeled finding that clearly blocks acceptance counts as must fix. Do not loop on P3 or style unless the user asked for full polish. "Until the review is empty" means "until no blocking findings remain"; review tools often print summaries or suggestions forever.

## Stop Conditions

Stop and report instead of continuing when:

- the latest review has no must-fix items (list remaining consider items separately);
- the same finding returns after two fix attempts and the evidence is ambiguous;
- a fix needs a product decision, contract change, data migration, deployment, credentials, or changes to unrelated work;
- verification fails for a reason outside the change and cannot be isolated;
- five cycles have run in one repository.

## Safety

Preserve unrelated changes and never revert them. Re-read files before editing if the worktree changed during the loop. Tie every edit to a concrete finding.

## Report

The target and number of cycles, fixed must-fix findings, verification commands and results, remaining non-blocking findings, and the blocker if the loop stopped early.
