# Fresh-Context Independent Verification

Use this protocol only when Tier 3 assurance justifies an independent adversarial pass and the user or owning policy permits it. It is not an executable gauntlet layer and does not replace human SPEC approval.

## Inputs

Give the verifier exactly these task-specific inputs before the blind phase:

1. the user task contract plus every explicitly approved scope change;
2. the approved SPEC;
3. the repository at an exact source state;
4. the gauntlet entry point.

Do not provide the builder conversation, proposed defenses, draft EVIDENCE, suspected defects, or intended answer. The verifier may inspect implementation and tests freely.

## Two Phases

### Blind Phase

The verifier records the source state, reruns the gauntlet, and attacks:

1. whether the environment executes the claimed source rather than stale or editable-installed code;
2. SPEC completeness against the approved task contract;
3. tests that may pass vacuously, over-mock logic, or key implementation to fixtures;
4. new mutants and concrete divergent inputs not chosen by the builder;
5. every home-grown checker's known-bad path and claimed coverage;
6. mapping in both directions: requirements without falsification and tests without approved requirements.

The attack list is required even when no finding survives.

### Comparison Phase

Only after freezing the blind record, provide draft EVIDENCE. Compare source state, commands, numbers, omissions, mappings, and confidence claims. A mismatch suspends the corresponding claim until it is reconciled.

## Findings And Rounds

- Behavioral finding: implementation is wrong or a required checker cannot fail. Fix it, then use a new verifier context against the new exact source state.
- Description or mapping finding: code is correct but SPEC, comments, or EVIDENCE overclaim. Correct and disclose it; a new round is not automatically required.
- A material or disputed classification belongs to the user, not the builder.

Cap at two rounds unless the user explicitly approves more. The cap controls cost; it does not convert unresolved findings into success.

## Verdicts

- `passed`: verification completed against the final source state with no unresolved behavioral finding.
- `failed`: a behavioral finding remains.
- `blocked`: verification could not complete because required inputs, tools, or fresh context were unavailable.
- `not performed`: accepted only as an explicit confidence downgrade.

A verdict belongs to one exact source state. Any later implementation or checker edit makes independent verification `not performed` for the new state until it is verified again. Record earlier rounds as history without inheriting their verdict.

The verifier fixes nothing. SPEC gaps return to the user; implementation findings return to the normal SPEC, RED, GREEN, gauntlet, and evidence loop.
