# Upstream Review

## Provenance

- Repository: `https://github.com/atani/codex-insights.git`
- Reviewed commit: `6041df056184ce0b8123ca774a8a504afc3529a2`
- Review date: 2026-08-24
- License: MIT, copyright 2025 atani. The original license text is preserved in `../LICENSE.upstream`.

## Upstream Implementation

The upstream project uses two Bash entry points:

1. `codex-insights` checks for `jq` and Codex CLI, samples local Codex history and recent session records, invokes `codex exec` to produce an `insights.json` document, caches that analysis for one hour, then opens a generated report.
2. `analyze.sh` derives message, session, project, tool, keyword, and top-session metrics with `jq`, `find`, `sort`, `awk`, and `grep`, merges optional AI insights, HTML-escapes inserted values, and writes a standalone HTML report.

Its central design is sound: keep deterministic usage metrics separate from interpretive analysis, then combine both in a human-readable report.

## Retained Design

`rumo-insight` retains:

- local Codex history and session JSONL as evidence sources;
- separate deterministic collection and model interpretation;
- project, tool, session, usage, win, friction, and recommendation views;
- evidence-backed, actionable improvement suggestions.

## Intentional Changes

- A standard-library Python collector replaces the Bash and `jq` dependency so collection works on macOS, Linux, Git Bash, WSL, and native Windows PowerShell.
- The skill does not recursively call `codex exec`. The active agent interprets scoped evidence directly, avoiding a second opaque analysis run and its separate provider or cost boundary.
- Historical transcript content is treated as untrusted evidence rather than instructions. This prevents embedded prompts or tool output from controlling the analysis workflow.
- Collection starts with a one-day text-free inventory and expands only when no suitable anchor exists. Raw text is available only through an explicitly selected, bounded adjacent-turn window.
- Output language follows the user instead of being fixed to Japanese.
- Project identity retains full working-directory evidence; basenames are presentation labels only and cannot silently merge different paths.
- The collector does not use phrase dictionaries, prompt-language classification, text matching, or time-gap task segmentation. Codex semantically reconstructs one selected lifecycle from source-linked conversation evidence. Automatic Claude Code comparisons remain omitted because equivalent evidence is not normally available.
- Tool-output failure matching is labeled as a signal requiring inspection, not a confirmed failed task.
- Token totals use the latest cumulative token record per session instead of summing repeated cumulative events.
- The final result is an evidence contract rather than a mandatory HTML artifact. Persistent files and instruction edits require explicit user scope.
