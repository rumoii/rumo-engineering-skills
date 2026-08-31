---
name: rumo-http-api
description: Use when designing, adding, changing, or reviewing a Rumo HTTP/JSON endpoint, route, OpenAPI contract, request or response shape, authentication and authorization boundary, idempotency behavior, rate limit, pagination contract, or expensive response field. Do not use as the primary compatibility guide for Kafka, gRPC/protobuf, GraphQL, WebSockets, terminal protocols, or persisted formats.
license: MIT
---

# HTTP API

Design HTTP/JSON surfaces that are predictable for consumers, safe under retries and hostile call volume, explicit about security boundaries, and operable during incidents. Prefer the established API convention over stylistic purity. A conventional HTTP RPC route is better than a breaking REST rewrite.

This is not a substitute for a full application-security review, threat model, or infrastructure assessment.

This skill owns HTTP-specific contract and operability decisions. Apply `rumo-interface-evolution` to existing endpoints and any change involving compatibility, producer-consumer inventory, mixed versions, rollout order, migration, deprecation, or rollback. Apply `rumo-old-coder` when the user requests the high-assurance SPEC and gauntlet workflow; put this skill's verified gates into that SPEC instead of running a parallel process.

For review-only requests, remain read-only and report only evidence-backed findings. A missing published guarantee means consumers cannot rely on a behavior; it does not prove that the server lacks an undocumented implementation.

## Establish Scope

Before proposing or editing a route, identify:

1. **Public or internal:** internal means the team can identify and ship every consumer; it does not remove authorization, retry, or incident risks.
2. **Existing or greenfield:** for an existing surface, read [references/compatibility.md](references/compatibility.md) and inspect real producers, consumers, schemas, SDKs, routes, logs, and deployment topology.
3. **Resource model:** name the product resource, its identity, owner, lifecycle, and durable state. Do not hide a missing product concept behind awkward HTTP verbs or polling choreography.
4. **Caller and environment:** browser, mobile, server-to-server, terminal, internal service, public integration, or operator tool; credential and usability choices depend on this.
5. **Cost and side effects:** database work, fan-out, external calls, unbounded results, irreversible effects, and retry ambiguity.

If the product model is the source of the awkwardness, say so. Do not make the API appear simple by leaking hidden jobs, tables, shards, or internal identifiers to consumers.

## Evaluate The Gates

Use `PASS` only with inspected or executed evidence, `FAIL` with a concrete consumer or incident consequence, `N-A` only when the surface does not exist, and `UNVERIFIED` when relevant evidence is unavailable.

### 1. Predictable Convention

- Use the API's established resource, RPC, naming, casing, envelope, verb, and status-code conventions.
- Prefer stable product nouns and opaque identifiers. Do not expose display names or positional indexes as identity.
- A surprising shape requires a concrete product or compatibility reason.
- Do not rename an established route merely to make it more RESTful.

### 2. Compatibility

- Treat field names, types, nullability, enum behavior, defaults, validation, ordering, status codes, error shape, pagination, and rate-limit behavior as contract.
- Prefer additive evolution. A renamed field is removal plus addition; a stricter validator can break requests that worked previously.
- Do not assume unknown JSON fields are safe for every known client; inspect generated and strict consumers.
- Use `rumo-interface-evolution` to define the old/new matrix, expand-migrate-contract order, deprecation, rollback cutoff, and mixed-version evidence.

### 3. Authentication

- Select credentials for the caller type and sensitivity. Never place long-lived bearer secrets in URLs, browser bundles, mobile applications, logs, or error payloads.
- For every credential type, define scope, secure transport, expiry where applicable, rotation, revocation, incident identification, and disablement.
- Reuse established workload identity, mTLS, gateway, session, or service-token infrastructure when it satisfies the actual boundary.
- Mark authentication `N-A` only for an intentionally anonymous operation and state how abuse and data exposure remain bounded.
- Authentication identifies a principal; it does not authorize the requested resource or action.

### 4. Authorization And Isolation

- State actor, action, resource, owner, product, tenant, and license boundary for every route.
- Resolve the resource, then enforce authorization server-side against the authenticated principal.
- Never trust caller-supplied tenant, owner, role, product, scope, or resource IDs without checking them against authoritative state.
- Apply the same boundary to list, search, count, export, bulk, nested, indirect lookup, download, and error paths. Filtering unauthorized rows after fetching is not an authorization boundary.
- Mark authorization `N-A` only when the resource and operation are intentionally public, with the reason and exposure stated.

### 5. Retry Safety And Idempotency

- Classify the operation as naturally idempotent, deduplicated, compensating, intentionally at-most-once, or unsafe to retry.
- For action-creating or relative updates, define an idempotency key or intrinsic operation identity when duplicate effects matter.
- Store request identity and the original outcome; the same key with different input must be rejected.
- For durable or irreversible effects, claim the key atomically with the effect or state the remaining crash window.
- A client timeout or `5xx` is ambiguous unless the contract tells the caller how to discover or safely repeat the outcome.

Read [references/patterns.md](references/patterns.md) for implementation constraints.

### 6. Blast Radius And Incident Control

- Calculate the cost of one caller in a tight loop, including database scans, fan-out, external calls, object storage, queues, and per-record work.
- Bound body size, page size, concurrency, execution time, result size, and expensive combinations at the authoritative server layer.
- Rate-limit by caller and operation cost when request volume can threaten shared capacity or fairness. Return the API's documented recovery metadata, including `Retry-After` on `429` when applicable.
- For external integrations, bulk work, fan-out, or other loop-amplifiable expensive operations, provide a per-consumer, per-tenant, or per-credential killswitch that operators can use without deploying code.
- For truly long-running work, model a durable job resource with explicit state, cancellation, expiry, and result ownership, and apply `rumo-lifecycle-safety`. Do not turn an ordinary read into an asynchronous job merely because the backend implementation is inconvenient.

### 7. Collections And Pagination

- Never return a potentially unbounded collection.
- Use a unique, stable ordering key. Cursor state must not weaken tenant or permission predicates.
- Prefer cursor pagination for growing or mutation-prone collections; bounded administrative lists may use offset or a single capped response.
- Return the next cursor or URL and an explicit completion signal. Clients must not construct cursors or infer completion from accidental page length.
- Treat default size, maximum size, ordering, filtering semantics, and cursor validity as contract.

### 8. Response Cost

- Keep the default response bounded and predictable. Avoid hidden N+1 queries, unbounded nested arrays, and unconditional cross-service calls.
- Put genuinely expensive optional fields behind an established include or expansion mechanism, validate requested expansions, and cap combinations.
- Prefer a separate paginated sub-resource when included data can grow independently.
- Do not introduce GraphQL or a generic query language unless the product already owns it or the user explicitly requests that design.

### 9. Errors And Operability

- Follow the API's existing status-code and error-envelope convention. Preserve machine-readable categories that consumers branch on.
- Distinguish invalid syntax, invalid semantics, authentication failure, authorization failure, absence, conflict, rate limiting, and server failure where the established contract supports it.
- Include safe correlation identifiers and recovery guidance without leaking secrets, internal stack traces, SQL, filesystem paths, or unrestricted payloads.
- Define logs, metrics, audit events, and alerts for authorization rejection, throttling, duplicate detection, expensive operations, and partial failure when those states matter operationally.

### 10. No Implementation Leakage

- Consumers should not need to know table IDs, shard layout, queue partitions, internal enum storage, worker topology, or hidden polling state.
- Do not make clients walk storage-linked identifiers or reconstruct server URLs and cursors.
- When implementation debt cannot be hidden compatibly, state it as a contract limitation and define the supported migration path.

## Avoid Over-Design

- Do not create version negotiation before a real incompatible version exists.
- Do not add idempotency machinery to harmless reads or naturally idempotent operations without side effects.
- Do not force cursor pagination onto a permanently bounded list.
- Do not add expansion mechanisms when every field is cheap and bounded.
- Do not rewrite a working API for naming aesthetics.
- Do not claim every internal endpoint needs public-developer ergonomics; do preserve security, retry safety, bounded cost, and operability.

## Verify The Surface

Use `rumo-test-evidence` to map each claim to the lowest layer that can falsify it. Depending on the change, exercise:

- the assembled production route and serializer, not only helper methods;
- unauthenticated, unauthorized, cross-tenant, wrong-owner, and indirect lookup cases;
- duplicate, concurrent, timed-out, retried, and same-key/different-payload requests;
- empty, boundary, maximum, invalid cursor, mutated collection, and stable-order pagination;
- `429`, recovery headers, body limits, result caps, and expensive combinations;
- old and new clients or representations defined by `rumo-interface-evolution`;
- logs, metrics, audit records, and killswitch behavior where incident control is claimed.

Use `rumo-change-verification` before declaring the implementation ready. Source checks do not prove a gateway, deployed policy, generated client, or field integration that was not exercised.

## Review Output

Order findings by consequence rather than taste:

1. breaking consumer behavior;
2. authentication, authorization, and isolation defects;
3. duplicate effects, unbounded cost, throttling, and incident-control gaps;
4. pagination, response cost, errors, and implementation leakage;
5. ergonomics only when they create a concrete consumer burden.

Cite repository file and line evidence. End with a gate summary using `PASS`, `FAIL`, `N-A`, or `UNVERIFIED`. If no verified finding survives, say so plainly.

## Maintenance And Provenance

This skill adapts the MIT-licensed `old-coder-api` workflow. Read [references/upstream-review.md](references/upstream-review.md) when maintaining the adaptation or comparing it with upstream. The original license is preserved in [LICENSE.upstream](LICENSE.upstream).
