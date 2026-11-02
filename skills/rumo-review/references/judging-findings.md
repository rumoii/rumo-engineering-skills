# Judging Findings

Read before sorting findings that someone else produced: an independent review pass, another model or CLI, a review bot, or a human reviewer. Read it also before reporting the findings of your own review. A finding is a claim to check against the code, not a verdict.

## Discount

- **Padding.** Reviewers asked to find problems tend to report something. When every finding is a style preference or a minor nit, say the change looks sound instead of promoting nits to fill the report.
- **Unreachable inputs.** "What if this is null, empty, or negative?" counts only when a real caller can produce that value. Trace the call sites, validation, and types; dismiss the finding with that evidence when no path reaches it.
- **Preference.** "I would structure this differently" is not a defect unless it names a concrete consequence: a bug, a broken contract, a measurable cost, or a maintenance trap the code actually creates.
- **Speculative abstraction.** A request to extract, generalize, or add an interface needs a second real use. Without one, keep the simpler code.
- **Missing context.** A reviewer working from a diff may flag code outside the change, a pattern the codebase uses on purpose, or a fix that breaks a constraint it could not see. Dismiss these with the context that settles them.
- **Old problems.** For a diff target, a problem that existed before the change is out of scope, as the evidence standard in SKILL.md sets out.
- **Tool-caught problems.** Something the repository's linter, type checker, or compiler already reports in its regular checks is not a review finding. When the repository does not run that check, report it as usual.
- **Deliberate suppressions.** A rule silenced on purpose with an inline ignore or suppression comment is not a finding. Report it when the silenced check would have caught a real defect this change introduces.

## Weigh Up

- The same issue raised independently by separate reviewers, especially different models, is stronger evidence than any single report.
- A finding that names a concrete execution path, input, or state outranks a hypothetical one.
- A finding that contradicts your own understanding of the code deserves a check before a rebuttal.
- Security, data-loss, and correctness findings get a full check even when only one reviewer raised them and the rest of its report was noise.

## Record

Give every dismissed finding its reason with file, line, test, or documentation evidence, so the decision can be checked later. Report accepted findings in the severity format of SKILL.md, naming which reviewer raised each one.
