# HTTP And JSON Compatibility

Read this before changing an endpoint that already has consumers. Use `rumo-interface-evolution` for the full producer-consumer inventory, rollout matrix, deprecation plan, migration, and rollback analysis.

Assume at least one consumer uses generated or strict types, branches on status and error categories, persists identifiers or cursors, and cannot be upgraded atomically with the server.

## Change Classification

| Change | Default classification | Required qualification |
| --- | --- | --- |
| New endpoint | additive | permission and operational limits still require verification |
| New optional request field or parameter | additive | omission must preserve previous behavior and side effects |
| New response field | usually additive | inspect known strict decoders and generated clients |
| Remove, rename, move, or change a field type | breaking | prefer parallel old and new fields or a new endpoint |
| Change field meaning without changing its shape | breaking and difficult to detect | introduce a new field or explicit opt-in behavior |
| Add a response enum value | conditionally breaking | exhaustive consumers may fail; prove open-enum behavior |
| Remove a request enum value or tighten validation | breaking | requests accepted previously now fail |
| Loosen validation | usually additive | verify it does not weaken authorization or integrity |
| Change a default | breaking | callers that omit the value receive new behavior |
| Change status code or error shape | breaking | consumers commonly branch or deserialize it |
| Change ordering, page size, cursor meaning, or completion semantics | breaking | pagination loops and persisted cursors may fail |
| Add or tighten a rate limit | operationally breaking | measure callers, announce, expose recovery metadata, stage rollout |
| Fix behavior consumers may have worked around | potentially breaking | inspect usage and provide an additive transition where needed |

Additive syntax does not guarantee compatible semantics. A new required side effect, authorization check, latency class, external call, or default expansion can break callers without changing the JSON schema.

## Consumer Discovery

Before claiming a route or field is unused, inspect and cite:

- frontend, backend, terminal, scheduler, scripts, sibling products, and supported branches;
- OpenAPI-generated clients, DTOs, deserializers, mappers, fixtures, and snapshots;
- documentation, examples, SDKs, support instructions, and exported integrations;
- gateway, access-log, audit, and per-consumer telemetry where available;
- queued, persisted, cached, or offline artifacts that outlive a deployment.

Search is discovery, not proof of absence. Dynamic clients, reflection, customer code, and copied examples may remain unobservable. Record that boundary as unverified.

## Prefer Additive Transitions

Before versioning, consider in order:

1. add an optional opt-in parameter while preserving omission behavior;
2. add a new field while continuing to populate the old field;
3. add a new endpoint beside the old endpoint;
4. introduce a version only when both contracts can be served, tested, documented, operated, and rolled back for the required lifetime.

For internal APIs, compatibility can be compressed only when every consumer is identified and can be changed in a coordinated rollout. Internal status does not remove retry, authorization, or incident risks.

## Deprecation

When removal is authorized and necessary:

1. ship and document the replacement;
2. identify and notify consumers;
3. expose the established deprecation or sunset signal;
4. measure usage by consumer;
5. rehearse the migration and rollback path;
6. remove only after the approved support window and observed usage criteria are satisfied.

Calendar age alone does not prove a surface is safe to remove.
