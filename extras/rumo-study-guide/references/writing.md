# Writing Learning Units

Read this before defining the outline and drafting chapters.

## Goals And Sequence

State what the reader will do: trace an input to its output, explain a boundary,
calculate a changed example, locate evidence, or compare two cases. Replace
"understand retries" with "explain which failed operation may safely be retried".
For each goal, identify its source, explanation, worked example, similar task,
and answer criteria. Teach prerequisites before their applications.

For a sprint, start from the deadline, available time, existing skills, and target
performance. Distinguish what can realistically improve from what remains out of
reach. Use P0 for essential independent tasks, P1 for supporting explanations,
and P2 for optional depth; define these labels for this reader. Estimate time
including practice, not just reading. Budget daily sessions around an observable
output, reserve time for retelling and review, and identify what to skip if time
runs short. Estimates are planning judgments, never measured learning speed.

## Chapter Pattern

1. **Why care:** say where the reader meets this and what goes wrong without it,
   then pose the problem this chapter lets the reader solve.
2. **Explanation:** explain the mechanism in plain language, following
   [voice.md](voice.md). Draw the mechanism as a figure
   next to the paragraph it explains; keep names and arrow meanings consistent.
3. **Complete example:** show inputs, assumptions, steps, and output. Explain
   boundaries before giving a similar problem with one changed condition.
4. **Self-test:** ask before revealing. Include answer criteria, the reasoning,
   a common misunderstanding, and a link back to the exact explanation.

Use the same case across chapters when it reduces prerequisites. Put essential
meaning in text; unfolding details, hovering, or running JavaScript must not be
the only way to obtain it. End with review questions that can be attempted again
after a reader-chosen interval. Do not prescribe a universal optimal schedule.

## Evidence Records

Keep the evidence record in `report.md` next to the guide, not in the reading
text. For each key claim, record its source location and one of these labels:

| Label | Meaning |
| --- | --- |
| implemented | Observed in the recorded revision; source reading alone does not prove deployed behavior |
| inference | Supported by named evidence; state assumptions and what would confirm it |
| proposal | A suggested design or study action, not existing behavior |
| teaching example | Invented inputs, simplified models, or hand calculations |
| unchecked excerpt | A document excerpt whose underlying claim was not independently checked |
| unresolved | Missing or conflicting evidence; state the open question |

In the guide itself, say a limit in plain words only where a reader would
otherwise be misled, once, next to the claim it affects: invented numbers,
code written for teaching, or a behavior nobody has observed. A closing
disclaimer cannot repair an earlier unqualified claim. Retain dates,
conditions, and units. Call output "实际运行输出" only when it was captured from
an actual authorized run, and never fabricate output to fill a gap.

## Component Choices

Read [components.md](components.md) for markup matching the template.

| Component | Use when | Omit or simplify when |
| --- | --- | --- |
| Figure | A chapter explains parts that hand things to each other, a structure, a flow, or changing states | Never omit for a mechanism; a row of labels, a table, or a translation grid does not replace the drawing |
| Chapter self-test | Every chapter has a key action to retrieve or apply | Fold a tiny section into its parent chapter rather than inventing trivia |
| Similar task | A worked example has established the method | There is no transferable action; use an explanation question instead |
| Prediction and reveal | One changed condition has a meaningful consequence | The answer is a guess unrelated to the goal |
| Parameter experiment | A small, bounded model exposes a causal relationship | A static worked example teaches the same thing more clearly, or the model would misrepresent reality |
| Code walkthrough | Actual code or a clearly labeled teaching snippet explains behavior | The source is unavailable; do not invent repository excerpts |
| Review list | Readers will revisit core tasks across sessions | A static question list suffices; persistence must remain optional |
| Priority and time in the kicker | A dated goal forces trade-offs | General learning has no time budget; do not manufacture urgency |
| Open retelling | The goal combines several mechanisms or requires spoken explanation | A short calculation or precise answer suffices |
| Term note | A term the reader may not know appears for the first time | It is central to the lesson; explain it in the paragraph itself |
| Source link | A reader may want to open the code behind a claim or excerpt | The content is a teaching invention; say so instead of inventing a reference |

Components serve the goal; there is no minimum interaction quota. Do not add automatic scoring or AI grading boxes. Never announce mastery from
scrolling, clicking, unfolding answers, or self-reported "会" choices. Describe
saved choices as self-reports. Learning effects require reader feedback, such
as independent explanations or later transfer attempts, with their limits stated.
