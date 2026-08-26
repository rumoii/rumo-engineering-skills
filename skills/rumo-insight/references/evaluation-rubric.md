# Employee AI Capability Evidence Rubric

Use this rubric only after Codex has reconstructed bounded task lifecycles and identified any separate asset, adoption, compliance, or baseline evidence needed for the requested capability claim. It evaluates observable AI-enabled work behavior, not intelligence, general productivity, personality, or employment potential.

## Evidence Status

- **Fact:** directly present in a selected user message, assistant message, lifecycle event, tool record, verification result, reusable asset, adoption record, or supplied baseline.
- **Supported interpretation:** the selected evidence supports the reading and material alternatives are discussed.
- **Not evidenced (`NE`):** the opportunity, ownership, applicability, or result cannot be established.

Do not convert `NE` into zero. Assign `0` only when the behavior was applicable and is visibly absent, contradictory, or harmful.

## Capability Dimensions

| Dimension | Weight | Subdimensions | Required evidence boundary |
| --- | ---: | --- | --- |
| Task definition and input quality | 25% | task decomposition; context and data preparation; boundaries and compliance constraints | Evaluate information available before the first agent action. Later clarification is collaboration evidence, not retroactive input credit. |
| Execution and tool usage | 25% | tool matching and ownership; iterative correction; workflow orchestration and encapsulation | Credit the employee only for tools or workflow choices they selected, configured, constrained, corrected, or deliberately accepted. Do not credit autonomous agent choices automatically. |
| Evaluation and quality control | 30% | professional acceptance; safety and compliance verification; measured efficiency or quality improvement | A successful command is not business acceptance. Efficiency claims require a baseline, comparable prior task, controlled estimate, or another explicit denominator. |
| Reusability and know-how amplification | 20% | experience codification; demonstrated reuse and maintenance; sharing and adoption | Creating a prompt, document, or skill proves codification only. Higher ratings require use outside the original case and evidence of maintenance or adoption. |

### Dimension 1: Task Definition And Input Quality

- **Task decomposition:** converts a complex or ambiguous objective into workable units, priorities, dependencies, or decision points proportionate to the task.
- **Context and data preparation:** supplies the repository, environment, source material, structured data, domain facts, and reliability caveats actually needed.
- **Boundaries and compliance constraints:** states scope exclusions, authorization boundaries, protected data, prohibited actions, compatibility obligations, and acceptance boundaries before execution when they are material.

Prompt length, formatting, templates, and vocabulary are not quality measures by themselves. A short continuation may be strong within a stable lifecycle and weak for handoff or reuse; score the actual context boundary.

### Dimension 2: Execution And Tool Usage

- **Tool matching and ownership:** selects or meaningfully governs the appropriate model, tool, module, agent, data source, or execution mode for the work.
- **Iterative correction:** detects material mismatch, hallucination, logic error, or missing evidence and supplies a correction that changes subsequent behavior.
- **Workflow orchestration and encapsulation:** sequences AI and non-AI steps, preserves state and authorization boundaries, and turns an effective current-task method into an executable procedure when repetition justifies it.

Workflow encapsulation in this dimension concerns reliable execution of the current method. Durable reuse outside the originating task belongs to Dimension 4 and must not be double-counted as organizational impact.

### Dimension 3: Evaluation And Quality Control

- **Professional acceptance:** independently checks the deliverable against business, engineering, or domain standards and distinguishes source, tests, Git state, artifacts, deployment, and field acceptance where relevant.
- **Safety and compliance verification:** prevents or identifies data leakage, privacy, security, licensing, copyright, regulatory, and authorization risks using task-proportionate controls.
- **Measured efficiency or quality improvement:** compares delivery time, rework, defect rate, evidence coverage, or another relevant outcome against an explicit baseline or comparable task.

Do not infer an efficiency gain from token counts, tool volume, a fast completion, or the employee's subjective impression alone. If no usable denominator exists, mark this subdimension `NE`.

### Dimension 4: Reusability And Know-How Amplification

- **Experience codification:** converts domain knowledge into a maintained prompt, checklist, skill, agent, script, evaluator, or other structured reusable asset.
- **Demonstrated reuse and maintenance:** the asset is used in at least one independent later lifecycle and is corrected, versioned, or maintained from real feedback when needed.
- **Sharing and adoption:** another person, team, or governed workflow uses the asset, or there is equivalent evidence that it replaced or materially improved a shared SOP.

Do not infer adoption from repository presence, documentation, publication, a successful commit, or the creator invoking the asset once. When team-level evidence is outside the authorized or available scope, report the personal capability profile and mark the organizational evidence `NE`.

## Maturity Scale

Rate each applicable subdimension on this five-level scale. The 10-point equivalent is for aggregation and presentation only.

Do not numerically score each successful case as Level 3 or 4 and then average those case scores. The case ledger records positive evidence, counter-evidence, responsibility, and applicability. Assign one profile maturity level to each subdimension only after comparing the qualifying evidence units against the thresholds below. In case mode, describe the observed behavior without producing a general maturity index.

| Level | Label | Observable meaning | 10-point equivalent |
| ---: | --- | --- | ---: |
| 0 | absent or harmful | Applicable behavior is missing, contradictory, unsafe, or repeatedly prevents a valid outcome. | 0.0 |
| 1 | assisted | The behavior appears only after substantial agent or human rescue and is not independently reliable. | 2.5 |
| 2 | functional | The employee can complete one bounded task, but the behavior is local, incomplete, late, or dependent on the current context. | 5.0 |
| 3 | repeatable | The behavior is explicit, proportionate, and consistent across independent tasks or task shapes. | 7.5 |
| 4 | amplifying | The behavior is standardized, measurably improves outcomes, or enables reliable reuse beyond the originating task. | 10.0 |

Level 4 is not a more polished Level 3. It requires the subdimension-specific evidence of measurable impact, durable reuse, or organizational amplification. Do not award it solely because several sampled tasks were successful.

## Calibration Anchors

- **One completed task:** a clear request, useful correction, and successful acceptance in one bounded lifecycle can support Level 2. It does not establish repeatability, reuse, measured impact, or adoption.
- **Repeatable individual practice:** consistent behavior across at least three applicable independent lifecycles and more than one task shape can support Level 3. Repeated personal success alone does not establish Level 4 or a score above 9.
- **Amplifying practice:** a standardized method or asset is reused beyond its creation case, produces an evidenced improvement, and is adopted by another person, team, or governed workflow. This can support Level 4 in the relevant subdimensions; it does not automatically make every dimension Level 4.
- **Repository presence only:** a committed prompt, skill, script, or document supports experience codification but not reuse, maintenance, adoption, or business impact without separate evidence.

## Evidence Thresholds

- Use three valid independent task lifecycles as the normal general capability-profile sample and represent at least two projects or task shapes when available. Add at most two more lifecycles only to resolve a stated coverage, diversity, or attribution gap.
- Require at least three applicable independent lifecycles before rating a lifecycle-based subdimension at Level 3.
- Require evidence from at least two independent task shapes plus the stated impact or reuse evidence before rating a subdimension at Level 4.
- Correction effectiveness may have fewer applicable cases because many successful tasks need no correction. Show its denominator and confidence instead of manufacturing correction opportunities.
- For asset, adoption, or efficiency subdimensions, use the actual qualifying evidence units and show them separately from lifecycle counts.
- Exclude self-analysis tasks, synthetic tests, platform-control exchanges, trivial factual questions, materially truncated cases, and cases whose employee/agent responsibility cannot be separated.
- Support every profile rating below Level 3 with at least one short redacted excerpt that establishes the limitation and its attribution. For `NE`, report the inspected scope and missing evidence instead of treating absence from a bounded transcript as contrary employee behavior.

## Score Calculation

1. Convert every reportable subdimension rating to its 10-point equivalent: `level / 4 * 10`.
2. Calculate each dimension score as the unweighted mean of its reportable subdimensions. Do not silently reweight a missing subdimension.
3. Calculate the **personal task capability index** from Dimensions 1–3 only, renormalized to their relative weights: 31.25%, 31.25%, and 37.5%. Report it only when every included dimension has at least two reportable subdimensions and the lifecycle minimum is met.
4. Report the **know-how amplification index** as the Dimension 4 score. Do not merge it into personal task capability.
5. Calculate the **overall employee AI capability index** as `D1*25% + D2*25% + D3*30% + D4*20%` only when all four dimensions are reportable and every dimension has at least two reportable subdimensions.
6. Keep maturity levels, evidence units, exclusions, dispersion, and confidence visible beside every numeric index. The decimal does not increase the underlying evidence precision.

If Dimension 4 is `NE`, return the personal task capability index and an organizational evidence gap. Do not renormalize the overall index around the missing organizational dimension.

## Nine-Point Gate

An overall index of `9.0` or higher is permitted only when all of the following are established:

- the weighted raw result is at least `9.0`;
- at least three dimensions score `8.75` or higher;
- Dimension 4 scores at least `7.5`;
- at least one structured asset is reused in an independent lifecycle beyond its creation case;
- at least one other person, team, or governed shared workflow has adopted a reusable asset or AI-enabled method;
- at least one efficiency or quality improvement has an explicit baseline or comparable denominator;
- the sample covers at least two projects or task shapes; and
- no unresolved high-severity safety, privacy, authorization, licensing, or compliance breach is present in the scored evidence.

If the raw calculation exceeds `9.0` but a gate is missing, report the raw result, cap the headline overall index below `9.0`, and name the unmet gate. Use `8.9` as the presentation cap; do not alter the underlying dimension scores.

Award `10.0` only when all twelve subdimensions are reportable at Level 4 and every nine-point gate is satisfied. A mature individual contributor who consistently completes difficult tasks but lacks organizational reuse or measured impact should normally fall in the `7.0–8.9` range, not above it.

## Responsibility Attribution

Classify material friction as:

- `employee_input`: required information, constraint, decision, or acceptance rule was absent or contradictory;
- `agent_alignment`: the request was sufficiently clear but the agent acted outside it or failed to retain it;
- `tool_or_environment`: permission, network, timeout, dependency, model, or runtime behavior;
- `task_inherent`: discovery or uncertainty intrinsic to the task;
- `organizational_context`: ownership, policy, baseline, reuse, or adoption evidence was unavailable to the employee or outside the task scope;
- `ambiguous`: selected evidence cannot distinguish the causes.

Recommend an employee behavior change only when the selected evidence supports `employee_input`. Do not penalize the employee for autonomous agent choices, environment failures, missing organizational opportunity, or evidence that the analysis was not authorized to inspect.

## Interpretation Bands

Use bands only as summaries after showing the underlying maturity evidence:

- `0.0–2.4`: absent or unsafe;
- `2.5–4.9`: assisted;
- `5.0–6.9`: functional;
- `7.0–8.9`: repeatable and mature;
- `9.0–10.0`: amplifying, with the nine-point gate satisfied.

These bands are descriptive calibration aids, not validated psychometric norms or employee-ranking percentiles.
