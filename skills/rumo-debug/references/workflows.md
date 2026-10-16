# Investigation Workflows

## Before Exploring

Write down the symptom, the expected behavior, the suspected owner, the evidence that would confirm it, and the observation that would rule it out.

Search source and runtime separately. Source shows what was intended; deployed artifacts and logs show what ran. When they disagree, find what separates them: version, environment, proxy, cache, asynchronous handoff, or stored state.

## Routes

Pick the smallest route that can explain the symptom, and look for the earliest point where actual state diverges from expected state:

- **UI state:** render conditions, permissions, data shape, stale state, CSS and layout ownership.
- **API mismatch:** client serialization, proxy rewrites, validation, response contract, error mapping.
- **Stored state:** transaction boundaries, schema, existing data, uniqueness, ordering, cache invalidation.
- **Asynchronous work:** enqueue, ownership, retry, duplicate delivery, cancellation, timeout, consumer progress, durable result.
- **Cross-service call:** addressing, identity, protocol, producer route, consumer subscription, logs on both sides.
- **Deployment mismatch:** branch, build inputs, artifact hash, running process, configuration, restart state, browser or client cache.

Check sibling consumers only when repository or profile evidence shows a shared contract.

## API Contract Checks

For each suspect request, record method, normalized path, headers, authentication context, query and path parameters, body, validation, status, response body, and error mapping. Map each visible field to its serialized key and backend field. Follow redirects, reverse proxies, development rewrites, gateways, generated clients, and multipart or streaming handling. A frontend path is not necessarily the backend route.

Compare the captured request with source types, controller inputs, service expectations, stored fields, and assembled runtime configuration. Exercise missing, null, empty, boundary, unknown enum, duplicate, pagination, upload, download, and partial-success cases when relevant.

## Closing

Do not close on a plausible code smell. Require a causal route from the trigger to the observed result, and confirm the earliest wrong state transition.
