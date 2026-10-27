# Principles

Read the entry whose **When:** line matches the moment. Each one changes a specific decision; if it changes nothing about the work in front of you, it does not apply. The entries change how you do the requested work, never how much: cleanup outside the requested change follows the Scope Test in SKILL.md and is reported, not performed.

## Delete Before Adding

**When:** before restructuring code, or before adding a feature beside a path that looks dead.
**Changes:** when the restructure is the task, remove dead code, unused options, and layers that no longer earn their place first, then build on the smaller base. When adding a feature, confirm that the old path has no callers, report it, and offer its removal as part of the change rather than building around it.
**Not this:** adding a new path beside an old one that nothing calls any more, so the next reader must work out which one is live.

## Test The Premise

**When:** two fixes for the same symptom have failed.
**Changes:** stop writing a third fix. Write down the assumption both fixes shared, such as "the cache is invalidated on write", and check it directly with a log line, a query, or a minimal reproduction.
**Not this:** a third variant of the same fix with more retries or a longer timeout.

## Redesign Instead Of Bolting On

**When:** a new requirement only fits the current design through special cases, flags, or repeated workarounds.
**Changes:** sketch the design as if the requirement had been known from the start, then move toward it. A pattern of the same workaround in unrelated places means the shape is wrong, not that more workarounds are needed.
**Not this:** a fourth `if` branch that checks for the new case in yet another caller.

## Name The Data Shape First

**When:** before writing logic with state, many branches, or a shape assumption repeated across files.
**Changes:** decide the core types and who owns each piece of state, then encode the rules in that structure: a state machine, a lookup table, a typed record, one owning module. The code that follows usually becomes obvious.
**Not this:** status strings compared in several files, each with its own idea of which transitions are allowed.

## Check At The Boundary, Trust Inside

**When:** writing validation, error handling, or an adapter for a framework, file, or network input.
**Changes:** parse and validate external data once, where it enters, into a trusted internal shape. Inside, rely on that shape instead of re-checking. Keep business rules free of transport and framework details.
**Not this:** the same null and range checks repeated in every function along the call chain.

## Keep The Reader's Load Small

**When:** following one behavior requires opening more than three files, or a wrapper has a single caller.
**Changes:** in the code you are changing, inline one-caller wrappers, collapse layers that only forward, and shrink the scope of mutable state, so the path from input to output can be read in one sitting.
**Not this:** a manager that calls a service that calls a helper, each passing the same arguments through.

## Build The Tool

**When:** the same edit is needed in many places, or a result must be reproducible by a reviewer.
**Changes:** write the script, codemod, or generator that makes the change or proves it, and give the reviewer the command that reruns it.
**Not this:** forty hand edits of one pattern, where the reviewer must trust that none was missed.

## Explain The Number

**When:** before reporting or acting on a measured result: a speedup, a regression, a throughput, or an evaluation score.
**Changes:** find what limits the number and rule out that it measured something else, such as a warm cache, a skipped step, or a different input. Report the conditions with the number. Read [measurement.md](measurement.md) before reporting a performance number.
**Not this:** "40% faster" from one run of each version on a machine that was also building something else.
