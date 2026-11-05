# Comparing Architecture Options

Read this when a plan needs a choice between viable designs that changes an interface, stored data, or the amount of work. Keep the comparison proportional to the decision: a short table and a few sketches can be enough.

## Ground The Decision

Trace the real callers and the paths they use before proposing boundaries. Describe concrete use cases with their inputs, expected outputs, side effects, and relevant failure or recovery behavior. Include the callers affected by compatibility, such as an older consumer or a background worker, when they exist. Cite the source or runtime evidence for current behavior; label assumptions and proposed behavior separately.

Use `rumo-explain` when the missing piece is an explanation of the existing code. Use `rumo-research` only when a consequential uncertainty needs evidence beyond the inspected code, such as an unfamiliar mechanism, external contract, or unproven performance claim. If the needed skill is unavailable, state the evidence gap and resolve it within the authorized scope or keep the decision open. Routine planning does not require a research phase.

## Make Each Option Concrete

For each feasible option, show enough of the design to walk the use cases through it:

- Sketch the types or interfaces at important boundaries: caller inputs, results, relevant errors, and compatibility obligations. Use the repository's terminology and distinguish existing definitions from proposed ones. Pseudocode or a small signature is enough when it exposes the decision.
- Name the knowledge each module owns and the state it may change. Separate durable data from transient state; identify the authoritative owner, readers, and lifetime of each important piece of state.
- Trace the data from the caller through those owners and back, including the failure path that could change the choice. Show handoffs, persistence, cancellation, retries, or cleanup only where they affect the decision. Use `rumo-interface` or `rumo-lifecycle-safety` when those contracts need their checks.
- Identify the existing code to reuse, boundaries to change, and migration or rollback obligations that make the option feasible.

Present alternatives that differ structurally: where responsibility lives, who owns state, how data crosses boundaries, or which work is performed. A different library or parameter is not another architecture unless it changes those obligations. Do not invent weak alternatives to fill a fixed count. If constraints leave only one feasible design, explain the eliminated choices and the evidence rather than presenting them as viable.

## Compare Against The Constraints

Derive comparison criteria from the agreed use cases and constraints. State which are hard requirements and which permit trade-offs. Compare every option against the same criteria, using evidence or explicitly bounded estimates; mark unknowns that could change the recommendation. Useful criteria include correctness under the named failure, compatibility, ownership clarity, operational burden, implementation effort, reversibility, and measured performance where relevant. Avoid scoring categories that do not affect this decision or treating unsupported numbers as measurements.

Before recommending, check each option for these design smells:

- A layer only forwards calls and hides no knowledge or policy.
- One piece of knowledge, such as a file format or business rule, is spread across several modules.
- Modules are split by execution order, such as read, process, and write, instead of by the knowledge each owns.
- More than one module writes the same piece of state.
- Two supported paths do the same task without a required distinction.
- Several lists must be kept in step by hand.

Explain any smell the recommendation retains, the constraint that justifies it, and its consequence. Recommend the option that satisfies the hard constraints with acceptable trade-offs; state what evidence would overturn the recommendation. Another model's draft is optional input, not a prerequisite or proof that a design is correct.

## Carry The Choice Into The Plan

After selection, carry the chosen boundaries, interface sketches, state ownership, and relevant data paths into the spec or link to their existing authority. Convert unresolved assumptions into explicit questions or checks. Give implementation tasks the affected owners, dependencies, compatibility and rollout order, and acceptance evidence for the caller use cases and significant failure paths. Name the smallest experiment needed when an uncertainty prevents a reliable task estimate, and keep its authorization visible in the plan.

Use the repository's decision record convention when the rationale must outlive the plan; follow the Plan skill's Decision Record mode rather than creating a second record of the same choice.
