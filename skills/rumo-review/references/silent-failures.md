# Silent Failures

Read when the review target adds or changes error handling, fallbacks, default values returned on failure, or retries. A silent failure is an operation that fails while its caller, user, or operator is led to believe it succeeded, or cannot tell which happened.

## Patterns To Find

- An empty catch, or a catch that only logs and then carries on as if the operation succeeded.
- A failure turned into a default, empty, or null return that the caller cannot tell apart from a real result.
- Optional chaining or null coalescing that skips an operation which should have failed loudly.
- A fallback taken without telling anyone, worst of all production code falling back to a mock, stub, fixture, or sample data.
- A catch broad enough to swallow errors unrelated to the one it was written for.
- Retries that run out without raising or reporting the final failure.
- An error surfaced to a caller or user as a generic message that drops the original cause, so nobody can tell which operation failed.

## Questions For Each Hit

- Which errors can this handler actually catch, beyond the one it was written for? Name them.
- Can the caller or the user tell that the operation failed?
- Did the requirement or documentation ask for this fallback, and can the user tell the fallback is in effect?
- Should the error be handled here, or propagate to a layer that can act on it?
- Does swallowing the error skip cleanup, leave partial state, or report work as done?

## Not A Finding

A best-effort path is fine when all three hold: it is deliberate, the code or documentation states why, and it leaves a visible signal such as a log at a suitable level or a metric. Examples: a cache read that falls back to the database and logs a warning, or a telemetry send whose failure must not block the main flow. When any of the three is missing, report it.

## Report

Use the finding format in SKILL.md. The trigger names the concrete error that gets swallowed, and the consequence says what the caller, user, or operator believes afterwards.
