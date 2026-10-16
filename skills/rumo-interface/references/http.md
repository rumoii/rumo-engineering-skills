# HTTP/JSON Surfaces

Read when designing, changing, or reviewing an HTTP/JSON route, OpenAPI contract, request or response shape, or the security and cost behavior around it. This complements the general contract flow in SKILL.md; it is not a full security assessment.

## First Questions

- **Who calls it?** Browser, mobile app, another service, a terminal, a public integration, or an operator tool. Credentials, ergonomics, and abuse risk depend on the answer.
- **Public or internal?** Internal means every consumer is known and shipped by the team. It does not remove authorization, retry, or incident risk.
- **New or existing?** For an existing route, inventory real consumers before changing anything.
- **What resource?** Name the product resource, its identity, owner, lifecycle, and durable state. If the API feels awkward because the product concept is missing, say so instead of hiding it behind odd verbs or polling.
- **What does one call cost?** Database work, fan-out, external calls, result size, irreversible effects, and what happens when the client retries.

## Checklist

Mark each item with evidence: **pass** (inspected or executed), **fail** (with the concrete consequence), **n/a** (the surface does not exist), or **unverified** (evidence unavailable).

### Convention

Follow the API's existing naming, casing, envelope, verb, status-code, and error conventions. Use stable product nouns and opaque identifiers, never display names or positions. Do not rename a working route to make it more RESTful.

### Contract

Field names, types, nullability, enum handling, defaults, validation, ordering, status codes, error shape, pagination, and rate-limit behavior are all contract. A rename is a removal plus an addition; a stricter validator can break callers that used to work. Check strict and generated clients before assuming unknown fields are ignored.

### Compatibility With Existing Callers

Assume some caller uses generated or strict types, branches on status codes and error categories, stores identifiers or cursors, and cannot upgrade at the same moment as the server. With that caller in mind, these look harmless but break someone:

- a new value in a response enum, unless open-enum handling is proven for known clients;
- a changed default, because callers that omit the field silently get new behavior;
- a different status code or error body;
- changed ordering, page size, cursor meaning, or end-of-list signal;
- a new or tighter rate limit (measure callers, announce, return recovery hints, roll out in stages);
- a bug fix that callers have already worked around;
- a field whose meaning changes while its shape stays the same, which is the hardest to detect, so add a new field or an explicit opt-in instead.

New optional inputs must keep the old behavior when omitted. Looser validation must not weaken authorization or integrity. A new side effect, permission check, latency class, or external call can break callers even when the schema is unchanged. Before versioning, try in order: an opt-in parameter, a new field next to the old one, a new route next to the old one; version only when both contracts can be served, tested, operated, and rolled back for the whole support window. To retire a route or field, follow the deprecation steps in SKILL.md and use gateway, access-log, or per-consumer telemetry where it exists.

### Authentication

Pick credentials suited to the caller. Never put long-lived secrets in URLs, frontend bundles, mobile apps, logs, or error bodies. Each credential type needs a scope, secure transport, expiry where it applies, rotation, revocation, and a way to identify and disable it during an incident. Reuse existing identity infrastructure when it fits. An anonymous route must state how abuse and data exposure stay bounded. Knowing who the caller is does not decide what they may do.

### Authorization And Isolation

For every route, state actor, action, resource, owner, and tenant or product boundary. Load the resource, then decide on the server against the authenticated identity. Never trust caller-supplied tenant, owner, role, or resource identifiers without checking them against stored state. Apply the same rule to list, search, count, export, bulk, nested, indirect lookup, download, and error paths; fetching everything and filtering afterwards is not authorization.

### Retries And Idempotency

Classify each operation: naturally idempotent, deduplicated, compensating, deliberately at-most-once, or unsafe to repeat. When duplicate effects matter, require an idempotency key or an operation identity. Scope every key to the authenticated principal, tenant, operation, and endpoint, so the same client key from another caller or route never matches. Store the key with the request fingerprint and the original result; reject the same key with different input, and re-check authorization before replaying a stored result. Track each claim as in progress, completed, failed but retryable, or expired, and keep records at least as long as clients are documented to retry. Decide what a concurrent duplicate, a crash, a cancellation, and a restart each see. When a duplicate effect is unacceptable (money, stock, irreversible actions), commit the idempotency record atomically with the authoritative state, typically through a unique constraint or a record owned by the same transaction. Only low-stakes operations may use a separate bounded store, and then the remaining crash window must be stated. A timeout or 5xx leaves the caller unsure, so tell them how to find out what happened or repeat safely.

### Cost And Incident Control

Work out what one caller in a tight loop costs. Bound body size, page size, concurrency, execution time, result size, and expensive parameter combinations on the server. Rate-limit by caller and operation cost when volume can hurt shared capacity, and return recovery hints such as `Retry-After` with 429. For integrations, bulk work, or fan-out, give operators a per-consumer or per-tenant off switch that needs no deploy. Model truly long work as a job resource with state, cancellation, expiry, and result ownership (see `rumo-lifecycle-safety`); do not turn an ordinary read into a job because the backend is slow.

### Collections

Never return an unbounded list. Order by a unique, stable key, and make sure cursors cannot weaken tenant or permission filters. Prefer cursors for growing or frequently changing collections; small bounded admin lists may use offsets or a single capped response. Return the next cursor or link and an explicit end signal; clients must not build cursors or infer the end from a short page. Default and maximum sizes, ordering, filters, and cursor lifetime are contract.

### Response Cost

Keep the default response bounded: no hidden N+1 queries, unbounded nested arrays, or unconditional calls to other services. Put genuinely expensive optional data behind the API's existing include or expand mechanism, validate the requested expansions, and cap combinations. Use a separate paginated sub-resource when nested data grows independently. Do not introduce a generic query language unless the product already has one or the user asks for it.

### Errors And Operations

Use the existing error envelope and keep machine-readable categories that clients branch on. Distinguish malformed input, semantic errors, unauthenticated, forbidden, not found, conflict, rate limited, and server failure where the contract allows. Include a safe correlation id and a next step, never stack traces, SQL, file paths, secrets, or raw payloads. Define logs, metrics, audit events, and alerts for authorization rejections, throttling, duplicate detection, expensive operations, and partial failures when they matter.

### No Leaked Internals

Clients should not need table ids, shard layout, queue partitions, internal enum storage, worker topology, or hidden polling state, and should not assemble server URLs or cursors. When internal debt cannot be hidden compatibly, document it as a contract limitation with a migration path.

## Avoid Over-Design

No version negotiation before a real incompatible version exists. No idempotency machinery on harmless reads. No cursor pagination on a list that is permanently tiny. No expansion mechanism when every field is cheap. No rewrite of a working API for naming taste. Internal endpoints do not need public-developer polish, but they still need security, retry safety, bounded cost, and operability.

## Verification

Exercise the assembled route and serializer, not only helpers. Depending on the change, cover: unauthenticated, forbidden, cross-tenant, wrong-owner, and indirect lookups; duplicate, concurrent, timed-out, and retried requests, including same key with different body and the same key from another tenant, principal, or operation; empty, boundary, maximum, invalid-cursor, changing-collection, and stable-order pagination; 429 with recovery headers, body limits, result caps, and expensive combinations; old and new clients per the compatibility matrix; and logs, metrics, audit records, and off switches where incident control is claimed. Source tests do not prove gateway policy, generated clients, or field integrations that were not exercised.

## Review Output

Order findings by consequence: broken consumers; authentication, authorization, and isolation defects; duplicate effects, unbounded cost, throttling, and incident-control gaps; pagination, response cost, errors, and leaked internals; ergonomics only when they create a concrete burden. Cite file and line, and end with the checklist marks. If nothing verified survives, say so.
