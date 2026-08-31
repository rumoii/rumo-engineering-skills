# HTTP API Patterns

These are constraints and decision aids, not copy-paste implementations. Prefer the target API's established, verified conventions.

## Idempotency

For a request that can create or repeat an effect, define:

- key scope: principal, tenant, operation, and endpoint;
- request fingerprint: canonical fields whose mismatch rejects key reuse;
- claim state: in progress, completed, failed-retryable, or expired;
- replay result: original status, response, and stable operation identity;
- retention window based on documented client retry behavior;
- atomicity between claiming the key and committing the side effect;
- behavior for concurrent duplicates, crashes, cancellation, and restart.

Low-stakes operations may use a bounded external store with a declared crash window. Duplicate-intolerant effects require the idempotency identity to be committed atomically with authoritative state, usually through a unique database constraint or transactionally owned record.

An idempotency key is normally unnecessary for:

- side-effect-free reads;
- a full replacement whose repeated execution has no additional effects;
- deletion of one stable resource identifier when repeated absence has defined behavior.

It remains necessary when those operations trigger email, webhooks, audit side effects, counters, relative updates, or non-ID-scoped deletion.

## Cursor Pagination

A cursor contract needs:

- a unique, stable order, commonly `(created_at, id)` or another immutable tie-breaker;
- tenant, ownership, permission, and filter predicates applied on every page;
- an opaque, integrity-checked representation when cursor contents must not be altered;
- a server-capped limit and documented default;
- an explicit next cursor or URL and completion signal;
- defined behavior for invalid, expired, cross-filter, cross-tenant, deleted, and newly inserted records.

Do not sort only by a non-unique timestamp. Do not filter unauthorized rows after selecting a page, because it leaks counts and produces short or empty pages that misstate completion.

Offset pagination is acceptable for permanently bounded collections or stable administrative data when the cost and mutation behavior are understood. It is not a safe default for a growing high-offset collection.

## Rate Limiting And Killswitches

Classify operations by real cost rather than assigning one uniform limit:

| Class | Typical examples | Relative policy |
| --- | --- | --- |
| Cheap identity read | one indexed resource by ID | higher limit |
| Search or collection | filtered list, aggregation, index | medium limit plus result bounds |
| Write | create or state transition | medium limit plus retry contract |
| Fan-out or bulk | export, notify-all, per-record external work | low limit, concurrency cap, often a durable job |

Rate-limit keys must represent the real actor and tenant boundary. Do not rely on a spoofable forwarding header without trusted proxy normalization.

Return the API's established limit metadata and `Retry-After` for throttled requests. Define whether limits are fixed-window, sliding, token-bucket, or concurrent-operation bounds only when that distinction affects clients.

Provide an operator-controlled per-consumer, per-credential, or per-tenant killswitch for external integrations, bulk work, fan-out, or other loop-amplifiable expensive operations. Record the action in audit evidence and define recovery. A global shutdown is not an adequate substitute when one integration is causing the incident. Low-cost bounded internal operations may mark this control non-applicable with a concrete reason.

## Optional Expensive Fields

Keep default responses bounded and predictable. An optional expansion mechanism should:

- accept only an allowlisted set of values;
- reject unknown expansions using the established client-error convention;
- cap combinations and nested depth;
- preserve authorization for each expanded resource;
- avoid unbounded arrays and N+1 calls;
- expose independently growing data as a paginated sub-resource;
- include expansions in cache keys, cost accounting, and rate-limit classification.

Do not add expansion syntax when the response is already cheap and bounded.

## Long-Running Operations

Use a job resource only when work genuinely cannot complete within the supported synchronous request budget. Define:

- creation idempotency and stable job identity;
- queued, running, succeeded, failed, canceled, and expired states as applicable;
- ownership, authorization, progress meaning, and result lifetime;
- polling backoff or event delivery, cancellation semantics, and retry behavior;
- recovery after worker restart and cleanup after expiry.

Do not expose internal worker state or require consumers to understand queue partitions, database rows, or process topology.


