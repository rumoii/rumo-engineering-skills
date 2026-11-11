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

1. **Question:** pose the problem this chapter lets the reader solve.
2. **Explanation:** explain the mechanism in plain language. Put a useful figure
   next to the paragraph it explains; keep names and arrow meanings consistent.
3. **Complete example:** show inputs, assumptions, steps, and output. Explain
   boundaries before giving a similar problem with one changed condition.
4. **Self-test:** ask before revealing. Include answer criteria, the reasoning,
   a common misunderstanding, and a link back to the exact explanation.

Use the same case across chapters when it reduces prerequisites. Put essential
meaning in text; unfolding details, hovering, or running JavaScript must not be
the only way to obtain it. End with review questions that can be attempted again
after a reader-chosen interval. Do not prescribe a universal optimal schedule.

## Evidence Labels

Keep labels local to the claim; a disclaimer at the end cannot correct an
unqualified claim earlier. Retain dates, conditions, units, and scope.

| Label in a Chinese guide | Meaning and required qualification |
| --- | --- |
| 已实现 | Observed implementation at the recorded revision; source inspection alone does not prove deployed behavior |
| 推断 | An interpretation supported by named evidence; state assumptions and what would confirm it |
| 建议 | A proposed design or study action, not existing behavior or a proven outcome |
| 教学示例，非实测 | Invented inputs, simplified models, or hand calculations; do not present them as field measurements |
| 摘录未核对 | A document excerpt whose underlying code or external claim was not independently checked |
| 未查明 | Missing or conflicting evidence; state the question left open |

Use "实际运行输出" only for output captured from an actual authorized run,
with input and runtime context. Running a teaching model still does not turn
its values into production measurements. Never fabricate output to fill a gap.

## Component Choices

Read [components.md](components.md) for markup matching the template.

| Component | Use when | Omit or simplify when |
| --- | --- | --- |
| Chapter self-test | Every chapter has a key action to retrieve or apply | Fold a tiny section into its parent chapter rather than inventing trivia |
| Similar task | A worked example has established the method | There is no transferable action; use an explanation question instead |
| Prediction and reveal | One changed condition has a meaningful consequence | The answer is a guess unrelated to the goal |
| Parameter experiment | A small, bounded model exposes a causal relationship | A static worked example teaches the same thing more clearly, or the model would misrepresent reality |
| Code walkthrough | Actual code or a clearly labeled teaching snippet explains behavior | The source is unavailable; do not invent repository excerpts |
| Review list | Readers will revisit core tasks across sessions | A static question list suffices; persistence must remain optional |
| Priority and time tags | A dated goal forces trade-offs | General learning has no time budget; do not manufacture urgency |
| Open retelling | The goal combines several mechanisms or requires spoken explanation | A short calculation or precise answer suffices |
| Term hint | An unfamiliar secondary term interrupts reading | It is central to the lesson; explain it directly at first use |
| Source annotation | A claim depends on a specific source location | The content is a teaching invention; label it instead of inventing a reference |

Keep component switches as reader preferences, not a minimum interaction quota.
Do not add automatic scoring or AI grading boxes. Never announce mastery from
scrolling, clicking, unfolding answers, or self-reported "会" choices. Describe
saved choices as self-reports. Learning effects require reader feedback, such
as independent explanations or later transfer attempts, with their limits stated.
