# Root-Cause Workflows

Choose the smallest route that can explain the symptom:

- UI state: render conditions, permissions, data shape, stale state, and CSS/layout ownership.
- API mismatch: client serialization, proxy rewrite, validation, response contract, and error mapping.
- Persisted state: transaction boundary, schema, existing data, uniqueness, ordering, and cache invalidation.
- Async work: enqueue, ownership, retry, duplicate delivery, cancellation, timeout, consumer progress, and durable result.
- Cross-service or remote call: addressing, identity, protocol, producer route, consumer subscription, and both sides' logs.
- Deployment mismatch: branch, build inputs, artifact hash, active process, configuration, service restart, and browser/client cache.

For each workflow, identify the earliest divergence between expected and actual state. Check sibling consumers only when repository or profile evidence shows a shared contract.
