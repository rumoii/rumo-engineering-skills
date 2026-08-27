---
name: rumo-browser-evidence
description: Use when asked to capture, compare, or deliver browser evidence for a UI workflow, including before-and-after screenshots, state sequences, DOM evidence, or a short interaction GIF. Record the exact source, server, backend, browser state, and viewport; distinguish real integration from mock or fixture behavior; keep capture separate from remote publication. Do not use merely because frontend code changed when no persistent visual evidence is requested.
---

# Rumo Browser Evidence

Produce a truthful, traceable visual artifact for one UI claim. Use `rumo-frontend-dev` to start or repair the local server and `rumo-frontend-ui` for implementation or visual design decisions.

## Record Provenance First

Capture before interacting:

- repository path, branch, commit, and dirty state;
- build or development mode and exact local URL;
- backend/proxy target and whether responses are real, mocked, or fixture-backed;
- browser context, login or role, product mode, and relevant feature switches;
- viewport and capture time;
- user-approved exceptions such as reuse of an existing authenticated browser profile.

Do not claim that a screenshot proves source, backend, deployment, or permission behavior not exercised by that setup.

## Isolate The Story

1. Use a fresh browser context when possible. Otherwise clear the target origin's state or disclose that existing cookies and storage were retained.
2. Select the shortest state sequence that proves one workflow: initial, action, pending when material, success or failure, and relevant detail.
3. Before every capture, wait for a concrete UI condition such as one exact label, enabled control, row state, response field, or stable error code. A fixed delay is not evidence of readiness.
4. Keep one viewport and crop across a sequence. Include enough surrounding UI to identify the product state without capturing unrelated tabs or notifications.
5. Cover empty, loading, success, error, disabled, or permission-limited states only when they are part of the requested claim.
6. Capture no passwords, tokens, personal data, customer identifiers, or unrelated environment details.

Use a dedicated Playwright or other isolated automation browser profile by default. When an existing authenticated state is genuinely required, or the user explicitly requests it, an existing user browser profile may be reused as a recorded exception. Limit access to the requested target and state: do not inspect unrelated tabs, history, password stores, extension data, or other origins. If browser automation is unavailable, report the limitation rather than presenting source inspection as visual verification.

Operate only localhost or an environment the user has explicitly identified as development or test. Ask before accessing an environment whose purpose is unclear. Production requires authorization for the exact scope and remains read-only unless the user separately authorizes a state-changing action. Let the user enter passwords, one-time codes, and other credentials in the visible browser window; never extract them from a browser profile.

## Store Artifacts Safely

Use the user-specified output directory. Otherwise write to a repository-declared ignored evidence directory or a temporary directory outside the product repository. Name files lexically and descriptively, for example `00-before.png`, `01-pending.png`, and `02-success.png`.

For a GIF, encode only frames from the same server, browser state, viewport, and scenario run. Prefer a state-based sequence over continuous recording. Use an existing repository encoder or available `ffmpeg`/`ffprobe`; do not install media software without authorization. Hold the final state long enough to read and verify the encoded GIF itself, not only its source frames.

Capture creates local artifacts only. Do not commit, push, upload, edit a merge request, or publish to an asset branch unless the user explicitly requests that external action. Reconfirm the target commit immediately before publication.

## Verify And Report

Open every final screenshot or representative GIF frame and check readability, ordering, sensitive content, text overlap, clipping, and the claimed state. Run `git status --short` and confirm that ignored or temporary evidence did not dirty product source unexpectedly.

Return the artifact paths and a provenance summary. State exactly which backend and browser state were used and which source, deployment, platform, or field claims remain unverified.
