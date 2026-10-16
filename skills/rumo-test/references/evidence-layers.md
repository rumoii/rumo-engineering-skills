# Evidence Layers And Risks

## Layers

Choose the lowest layer that can show the claim is false, then add layers only for what assembly or environment adds.

| Layer | Can show | Cannot show |
| --- | --- | --- |
| Static checks | types, syntax, declared rules, formatting and dependency invariants | runtime behavior |
| Unit | isolated decisions, transformations, state transitions, invalid input handling | framework wiring, external services |
| Module integration | real framework configuration and cooperating components | packaged or deployed topology |
| Assembled application | routes, dependency injection, serialization, permissions, proxy and persistence paths | release artifacts, target environments |
| Browser or terminal workflow | visible end-to-end behavior through the backend actually used | other roles, platforms, modes, or customer setups |
| Built artifact inspection | packaged files, images, dependencies, entry points, generated output | that deployment or business behavior works |
| Deployed environment | startup, configuration, health, API and log behavior on that target | customer field acceptance |
| Field acceptance | the named customer hardware, software, data, and workflow | environments not tested |

Snapshots suit stable protocol, document, prompt, or UI output that someone can review semantically. Never normalize away the behavior that changed just to keep a snapshot green.

## Risk Checklist

Consider, for the affected behavior:

- valid and invalid input; empty, minimum, maximum, duplicate, stale, and out-of-order values;
- permission, tenant, product, license, and ownership separation;
- timeout, cancellation, retry, partial failure, cleanup, and restart;
- old and new API, schema, configuration, message, and stored-data compatibility;
- locale, timezone, encoding, precision, filesystem, CPU architecture, Windows versus Linux, and offline differences;
- packaging, generated files, migrations, defaults, and deployment order.

Assert on what matters: the authoritative state, durable side effects, emitted protocol values, user-visible output, completed cleanup, and the absence of forbidden behavior.

## Sizing The Plan

Do not default to the whole repository suite, and do not drop a focused test because CI runs broadly later. Add a broader build or workflow only when module assembly, generated output, packaging, or environment configuration creates behavior the focused checks cannot see.
