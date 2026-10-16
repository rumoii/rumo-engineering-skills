# Minimum Evidence By Changed Surface

Start from the narrowest command that would fail for the regression, then widen only for a real dependency or shared contract.

| Changed surface | Evidence to consider |
| --- | --- |
| UI component or page logic | focused tests or lint, the affected frontend build, browser check of visible behavior |
| Shared UI component or runtime config | every known consumer, generated config validation, the affected application build |
| Service implementation | module compile and focused tests; callers too when an interface changed |
| DTO, API, serialization, or permission contract | producer and consumer paths, failure cases, compatibility with existing data |
| SQL, schema, or migration | query or migration validation, existing-data behavior, transaction and rollback path, affected service tests |
| Queue, cache, task, or session lifecycle | producer and consumer route, retry and duplicate handling, durable side effects, convergence after failure |
| Packaging or deployment script | built artifact contents, selected profile, plan or dry run, target paths, backup and rollback, post-action check |
| Shared skill | frontmatter and catalog validation, referenced files exist, helper-script tests, cross-platform command review, `git diff --check` |
| Documentation or generated file | owner check, render or build when applicable, forbidden-path scan, visual inspection |

Fakes, mocks, and unit tests do not prove an external or field boundary. Source checks do not prove built or deployed artifacts. Package checks do not prove a real platform, terminal, external runtime, or customer environment unless that environment was exercised.
