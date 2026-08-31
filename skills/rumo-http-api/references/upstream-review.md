# Upstream Review

## Provenance

- Repository: `https://github.com/AmazingAng/old-coder.git`
- Reviewed local commit: `a0eb529d393a1cb3ccc564e32b2104e7e75c7a29`
- Review date: 2026-08-31
- Reviewed capability: `skills/old-coder-api`
- License: MIT, copyright 2026 amazingang. The original license text is preserved in `../LICENSE.upstream`.

## Retained Design

The adaptation retains the upstream decisions that materially improve HTTP/JSON work:

- establish public/internal, existing/greenfield, and product-resource scope first;
- prefer predictable established conventions over novel or stylistically pure interfaces;
- separate authentication from resource-level authorization;
- define retry safety and idempotency for side effects;
- bound call-loop blast radius through cost-aware limits and an incident killswitch;
- use stable cursor pagination for growing collections;
- keep expensive fields optional and bounded;
- hide implementation topology from the consumer;
- distinguish verified pass, failure, non-applicability, and missing evidence in reviews.

## Generic Adaptation

- The skill is named `rumo-http-api` because the capability is HTTP/JSON design and review, not the full `rumo-old-coder` assurance loop.
- Compatibility details are narrowed to HTTP/JSON and compose with `rumo-interface-evolution`, which remains authoritative for producer-consumer inventory, mixed versions, rollout, migration, deprecation, and rollback.
- Authentication advice does not prescribe one credential mechanism. The choice follows caller type, sensitivity, and existing infrastructure.
- The original unconditional cursor and rate-limit defaults are calibrated by bounded collections, operation cost, established gateway behavior, and concrete incident risk.
- Authorization explicitly includes product, tenant, license, owner, list, export, bulk, nested, and indirect lookup paths relevant to the product.
- Pagination guidance prevents post-fetch authorization filtering from weakening isolation or corrupting completion semantics.
- Operability includes body, time, concurrency, result, expansion, and external-call bounds, plus logs, metrics, audit evidence, and operator recovery.
- Long-running operations gain explicit ownership and lifecycle composition with `rumo-lifecycle-safety` rather than treating every expensive read as a background job.
- Review examples are not copied. The entrypoint defines the evidence statuses and output priority without embedding synthetic product facts.

## Known Boundary

This skill is not a full application-security review and does not replace protocol-specific guidance for gRPC/protobuf, GraphQL, WebSockets, terminal messages, Kafka, database formats, or persisted files. It also does not prove deployed gateway, identity-provider, rate-limit, or field behavior unless those components are exercised.
