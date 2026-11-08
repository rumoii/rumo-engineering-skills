# Status Card

A status card answers, for a user who did not watch the work: what is mine to do now, what is done and how we know, and which decisions are mine. Keep it to about 40 lines so it is read in full. Write the headings and content in the user's language.

## Template

```markdown
# <Project> status (updated <date>)

## This stage
<Goal of the current stage in one line.>
Deadline: <date> (<days left>). Review or exit conditions: <conditions, or "none set">.

## Your turn
<First line: whether any agent is running now, and where.>
1. ★ <The one thing that matters most.>
2. <Other things for the user to do.>
3. Waiting for your decision: <each open decision, one line, with what it blocks>.
Agents next: <what agents will do, and when>.

## Done, and how we know
- <item>: <evidence level>

## Decisions
- <decision>. Why: <reason>. Who: <you | ⚠ agent, unconfirmed>. <date>

## Details
<Paths to the handoff, plan, and lists, for looking things up; not required reading.>
```

## Evidence Levels

Mark each done item with the strongest level that holds, and name the check when it is automated:

- **You used it**: the user tried it themselves.
- **Checks pass**: tests, builds, or scripted runs passed; name them.
- **Code read only**: someone read the code; nothing ran.
- **Not verified**.

An item the user has not tried says so, even when checks pass. Untried behavior the user must judge belongs under "Your turn".

## Decisions

- Record why when the reason would change how the user judges the decision later.
- Who decided is either the user or an agent. An agent's decision carries ⚠ until the user confirms it; a record that does not show the user's approval counts as the agent's.
- Keep rejected options in the handoff or plan; the card names only what was chosen.

## Staying Short

- Replace stale lines instead of adding below them. The card shows the present, not a history.
- When it grows past about 40 lines, move confirmed decisions that no longer affect the current stage into the document listed under Details. Do not compress the wording to make room.
- A fact that cannot be verified now is left out or marked unverified, never copied forward.
