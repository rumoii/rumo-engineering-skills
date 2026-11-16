# Handoff Document

A handoff document lets the next agent continue without this conversation. Fill each section from facts verified now; drop a section only when it would be empty.

```markdown
# Handoff: <task>

## Goal
One or two sentences, plus acceptance criteria.

## Decisions
What the user decided, with the reason when it matters. Mark anything still open.

## State
Repositories, branches, commits, dirty files, processes, environments.

## Verified / Not Verified
What was checked and how; what remains unproven and why.

## Next Steps
Ordered, concrete actions. Mark steps that need user approval.

## Tried And Dropped
Approaches tried and abandoned, each with why and where the evidence is. When the plan file already records them, link its section and list only what it lacks.

## Pitfalls
Traps already hit and how they were resolved.

## Resume
The exact commands or reads to get back to a known-good state.
```
