# Debugging SOP

Write the symptom, expected behavior, suspected owner, evidence required, and disproof condition before broad exploration.

Search source and runtime independently. Source shows intended behavior; deployed artifacts and logs show what actually ran. When evidence conflicts, identify the version, environment, proxy, cache, asynchronous handoff, or persisted state that separates them.

Do not close an investigation on a plausible code smell alone. Require a causal route from the user action or trigger to the observed result and verify the earliest incorrect state transition.
