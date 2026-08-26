# AI Capability Evidence Report Contract

Use this structure unless the user requests another format. The default unit is one semantically reviewed, bounded task lifecycle. A capability profile combines multiple independent lifecycles with any separately authorized asset, adoption, compliance, or baseline evidence. Do not present an inventory as an employee capability score.

## Scope And Evidence

State:

- inventory interval and timezone;
- project, session, and task-shape coverage;
- valid and excluded lifecycle counts, including the outcome mix;
- whether selected user and assistant text or detailed tool output was inspected;
- any asset, adoption, compliance, or efficiency sources placed in scope;
- source files and source-line references; and
- parse, truncation, attribution, organizational, or coverage limits.

Treat `history.jsonl` as a coverage and index source. Do not claim one-to-one alignment between its text and session messages unless the format supplies a structural identifier.

## Lifecycle Reconstruction

For each selected case, describe only what the adjacent turns establish:

1. Initial objective, input, and material boundaries.
2. Clarifications, scope changes, authorization transitions, or corrections.
3. Employee-owned tool or workflow decisions and relevant agent actions.
4. Verification, outcome, or acceptance evidence.
5. Explicit stopping boundary and unverified boundary.

Mark each material statement as `fact`, `supported interpretation`, or `NE`, and cite turn IDs and source lines. Separate `employee_input`, `agent_alignment`, `tool_or_environment`, `task_inherent`, `organizational_context`, and `ambiguous` responsibility.

## Case Ledger

Keep the ledger compact. For every valid lifecycle record:

- case ID, project or task shape, and lifecycle boundary;
- positive evidence and counter-evidence relevant to each applicable subdimension;
- employee ownership or responsibility attribution;
- confidence and source lines; and
- exclusions or evidence still needed.

Do not assign a general 0–4 maturity level to every individual successful case. The profile maturity level is a cross-case judgment using the evidence thresholds in [evaluation-rubric.md](evaluation-rubric.md). Correction-heavy or unsuccessful cases are valid evidence when their boundary and responsibility are attributable.

## Four-Dimension Capability Profile

Report the following dimensions and weights:

| Dimension | Weight | Required subdimensions |
| --- | ---: | --- |
| Task definition and input quality | 25% | task decomposition; context and data preparation; boundaries and compliance constraints |
| Execution and tool usage | 25% | tool matching and ownership; iterative correction; workflow orchestration and encapsulation |
| Evaluation and quality control | 30% | professional acceptance; safety and compliance verification; measured efficiency or quality improvement |
| Reusability and know-how amplification | 20% | experience codification; demonstrated reuse and maintenance; sharing and adoption |

For every subdimension show:

- maturity level `0–4` or `NE`;
- the corresponding 10-point equivalent when reportable;
- qualifying evidence units and denominator;
- positive evidence, counter-evidence, and alternative explanations;
- for every result below Level 3, at least one short redacted evidence excerpt with case ID, speaker, turn ID or source line, followed by the exact reason it limits the rating;
- for every `NE`, the inspected evidence boundary and the specific missing artifact, denominator, ownership fact, or observation needed to make it reportable;
- confidence; and
- the evidence needed to reach the next level.

For every dimension show its score, reportable subdimensions, missing evidence, and dispersion. Do not silently reweight a missing subdimension.

## Deduction Evidence

Make deductions independently auditable without reproducing unrestricted transcripts:

- Quote only the shortest clause that establishes the limitation, normally no more than 240 characters.
- Label each excerpt with the case ID, employee or agent speaker, turn ID or source line, and evidence status.
- Follow the excerpt with a separate interpretation sentence. Do not present the model's interpretation as part of the quote.
- When the limitation is employee input, show the employee wording and the material decomposition, context, constraint, or acceptance fact that remained unresolved before the first agent action.
- When the limitation is agent ownership, show both the employee request and the agent statement that selected or designed the tool, workflow, or verification behavior when needed to establish attribution.
- When a subdimension is `NE`, do not manufacture a negative excerpt. State which selected lifecycles and external evidence sources were inspected and exactly what was absent.
- Redact credentials, customer data, unrestricted source code, personal identifiers, and sensitive infrastructure details. A source reference does not authorize quoting the full record.
- Do not repeat the same excerpt under several deductions unless it independently establishes each claimed limitation. Prefer a compact deduction ledger when several dimensions share one evidence boundary.

## Index Summary

When coverage permits, report these separately:

1. **Personal task capability index:** Dimensions 1–3 with relative weights 31.25%, 31.25%, and 37.5%.
2. **Know-how amplification index:** Dimension 4 only.
3. **Overall employee AI capability index:** `D1*25% + D2*25% + D3*30% + D4*20%` only when all four dimensions meet the rubric's coverage rules.

Show the raw weighted result, headline result, and nine-point gate status separately. If the raw result reaches 9.0 but a gate is absent, apply the rubric's `8.9` presentation cap and identify every unmet gate. Do not generate an overall index when Dimension 4 or another required dimension is `NE`.

Numeric indexes are optional descriptive summaries. The maturity evidence, coverage, and gaps are authoritative. Never imply psychometric validity, ranking percentile, employment potential, intelligence, general productivity, code correctness, deployment success, or field acceptance.

## Strengths, Friction, And Recommendations

- Report a stable strength only when supported by at least two independent evidence units and the claimed maturity threshold.
- Present the deduction ledger before recommendations so every improvement is traceable to a quoted limitation or an explicit `NE` boundary.
- Identify whether friction belongs to employee input, agent alignment, tools or environment, the task itself, organizational context, or remains ambiguous.
- Order recommendations by expected value and effort. Name the owner, evidence addressed, smallest proposed change, and a falsifiable success criterion.
- Prefer one short task-specific input improvement over a mandatory prompt template.
- Recommend a reusable asset only when repetition justifies it. Distinguish creating the asset from proving later reuse or team adoption.
- Do not apply recommendations, edit instructions, or publish employee reports from an insight request alone.

## Stop Condition

In case mode, stop after one lifecycle is sufficiently closed and do not produce a general employee capability index. In capability-profile mode, use three valid independent lifecycles by default and expand one at a time to no more than five only when a stated coverage, diversity, or attribution gap remains. Finish the current lifecycle before honoring soft turn or character checkpoints.

Do not broaden discovery merely to fill organizational evidence gaps. If adoption records, baselines, compliance artifacts, or reusable assets are unavailable or outside scope, mark the affected subdimensions `NE` and return the personal profile that the available evidence supports.

## Limitations

State that bounded local history cannot establish population statistics or all organizational behavior; completion-oriented candidate selection can bias the sample; deterministic failure signals can include expected failures and recovered retries; cumulative tokens may cross interval boundaries; and transcript evidence alone cannot establish causation, intelligence, business value, team adoption, or real-world acceptance.
