# Writing For Agents

Agent-facing files are instructions a model follows without asking follow-up questions. Optimize them for correct action, not for persuasion.

## Selection Text

Clients usually choose a skill from its frontmatter `name` and `description` alone, so the description must stand on its own:

- Start with the concrete situations that should trigger it, using words a user would actually type.
- Name the nearest look-alike situations that must not trigger it, or the skill to use instead.
- Keep it under the client limit (1024 characters here) and free of marketing language.
- Avoid descriptions so broad that the skill fires on ordinary questions; a skill that triggers everywhere stops carrying signal.

## Body Structure

Use this order and omit sections that do not apply:

1. Purpose in one or two sentences.
2. Modes, when one skill serves several request types, with how to pick one.
3. Workflow steps with checkpoints: what must be true before moving on.
4. Stop conditions: when to pause and ask, and what never to do.
5. Evidence and output: what the final report must contain.

Add two optional parts only where agents tend to skip steps:

- **Red flags:** observable signs that the work is going wrong.
- **Shortcuts and rebuttals:** the tempting reasons to skip a step, each paired with why it does not hold.

## Keep The Body Lean

- Aim for about 80 lines in SKILL.md. Move long checklists, templates, and domain detail into `references/`.
- Every reference link states when to read it, for example "Read X before choosing a rollback order". A reference without a loading condition is rarely read.
- Authorization rules and stop conditions stay in the body; never hide them in a reference.
- Write imperative sentences. State the rule once, in the place it applies.
- Resolve bundled scripts relative to the skill directory, never a checkout path.

## Portability

- Do not depend on one company, product, host, path, or agent client. When a step needs a specific client, label it and give a neutral alternative or a stop condition.
- Name other skills in plain text when they may not be installed alongside, and say what to do when they are absent.
- Keep private project facts in a profile, not in the skill.

## Review Checklist

- Would the description alone pick this skill for its intended requests and skip it for the look-alikes?
- Can an agent follow the workflow without guessing what "done" means at each step?
- Are authorization limits and stop conditions explicit?
- Does every reference have a loading condition?
- Is anything repeated that could be said once?
