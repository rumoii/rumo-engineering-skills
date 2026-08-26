---
name: rumo-prose-standard
description: Use when writing, reviewing, trimming, or restoring prose in Rumo repositories, including Markdown, JavaDoc/JSDoc, code and test comments, prompts, diagnostics, logs, API errors, configuration descriptions, and product-visible UI strings. Preserve complete behavior and failure facts while removing repetition, implementation narration, review residue, and unresolvable development-session references. Use rumo-document-writing instead for formal DOCX delivery artifacts.
---

# Rumo Prose Standard

Write enough to preserve the behavior a maintainer, caller, operator, or user relies on. Remove wording only after every relevant fact survives.

## Authority And Scope

Require an explicit repository scope. A review or audit reports findings without editing; a write, fix, or trim request authorizes scoped changes.

Read the owning code, configuration, schema, or runtime evidence before judging prose. Treat generated files as derivative: edit the owner and regenerate. Do not modernize recorded fixtures, snapshots, vendored sources, archived evidence, or historical artifacts unless the user explicitly targets them.

Use `rumo-document-writing` for Word delivery documents, where layout preservation and product-document language have separate requirements.

## Preserve Complete Facts

Before editing a passage, identify its relevant propositions:

- actor and action;
- condition, timing, and ordering;
- must, may, or never semantics;
- ownership, side effects, and cleanup;
- failure mode, user consequence, and recovery;
- authorization, data scope, transaction, and compatibility;
- negative guarantee and exception.

Do not shorten a passage by dropping one of these facts. Keep non-obvious rationale when removing it could cause misuse or an incorrect future simplification; otherwise link to its durable owner.

## Standards By Surface

- **Public JavaDoc/JSDoc:** document caller-visible distinctions, failures, side effects, lifecycle, thread or async behavior, cancellation, and ownership that types do not express.
- **Code comments:** explain non-obvious constraints or reasons. Do not narrate the next statement or restate a method name.
- **Tests:** describe the behavior and condition being pinned, not that the implementation is "correct" or a walkthrough of test control flow.
- **Errors and diagnostics:** identify the failed operation, relevant target, safe corrective action, and stable error category without exposing secrets.
- **Logs:** include stable correlation fields and state transitions needed for diagnosis; avoid credentials, full sensitive payloads, and decorative prose.
- **UI strings:** use product language, name the user action and consequence, and keep implementation, repository, prompt, and generation terminology out of the interface.
- **Repository Markdown:** state current behavior. Put alternatives and durable rationale in an engineering decision rather than repeating them across READMEs.

Model-visible prompts, API errors, and product strings are behavior. Update their focused tests, snapshots, or acceptance evidence when wording changes observable output.

## Remove Development-Session Residue

Durable prose must stand at the current repository state without access to a chat, review thread, private draft, or temporary plan. Replace or remove:

- decision or audit ordinals that have no committed owner;
- "this change", "this review", "later PR", or branch-stack narration;
- reviewer-directed explanations;
- references to uncommitted plan sections;
- change stories such as "used to" or "now" on current-state surfaces;
- control-flow narration and test walkthroughs.

If a passage contains a real fact, rewrite that fact in present tense. If it contains only session metadata, delete it. Issue numbers, committed documents, standards, measured bounds, suppression reasons, and present-tense counterfactuals remain valid when they resolve and are useful.

## Verify And Report

Re-read the edited passage against its owner, search for stale terminology or duplicated statements in the changed scope, and run the checks required for the affected surface. Report the scope, categories changed, owner evidence used, and any wording whose product meaning still requires a decision.
