# Design Panel

Read before asking other models for competing designs. Each configured lane drafts one design for the same problem without seeing the others; you draft one too, compare them, and hand the user a recommendation. Independent drafts surface shapes a single author would not consider. The panel produces designs only, never code, and the plan is not broken into tasks until the user picks one.

## When To Run One

- **The user asks** several models for designs or options.
- **You propose one** in Plan Mode step 2 when the design is genuinely uncertain and the choice changes an interface, stored data, or the boundary between modules. Do not propose one for a choice with one obvious shape or a local change. `auto_panel` from `agent_config.py lanes design` decides the next step, as for review panels.

Run it as `rumo-review`'s [references/panel.md](../../rumo-review/references/panel.md) describes, reading design for review throughout: `lanes design` in place of `lanes review`, the design problem as the target, the brief and the files it names as what leaves the machine, a lane that returns something other than a design as a dropout, and a single-model design when every lane drops out. This file replaces three parts of it: Run step 2 with The Brief below, the review in Run step 4 with your own draft (Compare step 1), and the judging in Run step 6 and its Report with Compare and Report below. Still record every run's decision with `agent_run.py record`.

## The Brief

Write one brief for every lane, to a file outside the repository: the goal, non-goals, constraints, acceptance criteria, the entry points and existing patterns to read, and where the repository guidance lives. Withhold your own leaning and any option you already prefer. Ask each lane for a design in prose, not code:

1. How a caller uses it: two or three real call sites, written first.
2. The core data shapes and who owns each piece of state.
3. The modules, what each one knows, and its public surface.
4. The alternatives it considered and why it rejected them.

Tell the lane it is one of several drafting independently, so it should give its best design rather than a safe middle.

## Compare

1. Draft your own design to the same four headings and save it before reading any lane's draft.
2. Check every draft, yours included, against the design smells in SKILL.md Plan Mode step 2. A draft with a smell is revised or dropped.
3. Prefer the design whose smallest, simplest public surface hides the most complexity, and whose state each has one owner.
4. Pick one draft as the base. Port at most one or two strong ideas from the others, rewritten to fit the base rather than pasted in. Drafts that converge on one shape are strong agreement; drafts that diverge widely mean the brief was underspecified, so tighten it before trusting any of them.
5. Offer the user at least two structurally different options; the same shape with another parameter or library is one option. When every surviving draft converges on one shape, the second option is the strongest alternative the drafts considered and rejected, with their reasons.

## Report

Present the recommendation with its alternatives as Plan Mode step 2 options: for each, where the change lives, how data flows, what it costs, which lanes proposed it, and why it won or lost. Add a lanes table (CLI, model, effort, run ID, or dropout reason). Then return to Plan Mode step 3, and break the work down only after the user picks.
