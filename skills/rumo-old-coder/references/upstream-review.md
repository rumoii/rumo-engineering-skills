# Upstream Review

## Provenance

- Repository: `https://github.com/AmazingAng/old-coder.git`
- Reviewed local commit: `a0eb529d393a1cb3ccc564e32b2104e7e75c7a29`
- Review date: 2026-08-31
- License: MIT, copyright 2026 amazingang. The original license text is preserved in `../LICENSE.upstream`.
- Reviewed capability: `skills/old-coder`; the optional `old-coder-api` companion is adapted separately as `rumo-http-api`.

## Retained Design

This adaptation retains the upstream principles that materially change agent behavior:

- the user reviews an executable SPEC before implementation and an EVIDENCE report after it;
- behavioral work follows RED, GREEN, and refactoring under green;
- checks scale with risk and converge through one final fresh gauntlet run;
- changed-line coverage, mutation, properties, real execution, supply-chain checks, and suite health are distinct evidence layers;
- home-grown checks fail closed and require a known-bad control;
- omitted checks, substitutions, checker limits, source state, and structural blind spots remain explicit;
- fresh-context verification, when selected, attacks the exact state and does not fix its own findings.

## Generic Adaptation

- The skill is named `rumo-old-coder` so the existing installers synchronize it to Codex, Claude Code, and Grok without broadening third-party skill management.
- The entrypoint is shorter and routes detailed tooling, templates, and independent verification into references for progressive disclosure.
- `rumo-coding-guidelines`, `rumo-test-evidence`, `rumo-change-verification`, and domain safety skills remain authoritative for Rumo scope, evidence boundaries, compatibility, lifecycle, database, packaging, deployment, and field claims.
- SPEC approval does not imply authorization for commits, pushes, deployments, persistent database writes, destructive actions, dependency installation, or paid/external operations.
- Checkpoint commits are not required. Repository commit and push policy remains separately controlled by `rumo-git-commit` and the user's explicit request.
- A cross-platform repository-native or Python gauntlet entry point is preferred over adding a POSIX-only shell workflow; this preserves macOS, Linux, Git Bash, WSL, and native Windows support.
- The upstream API companion is adapted as `rumo-http-api`, which owns HTTP/JSON design and operability while `rumo-interface-evolution` retains cross-format producer-consumer compatibility, rollout, migration, and rollback.
- Ordinary low-risk changes continue to use focused tests and normal verification instead of automatically paying the full evidence-first workflow cost.

## Known Boundary

This repository distributes instructions, not a universal gauntlet executable. Each product repository owns its actual test tools, aggregate command, CI integration, platform requirements, and retained evidence artifacts. The skill must inspect those owners instead of copying example commands blindly.


