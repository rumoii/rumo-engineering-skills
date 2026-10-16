# Artifact And Validation

Use this reference after model confirmation and after each material fact, view, or wording revision.

## Deliverables

Keep one stable base name:

- `<base>-model.json`: confirmed V2 fact and view source;
- `<base>-generator.mjs`: generic renderer;
- `<base>.md`: unified facts, view mappings, assumptions, and evidence boundary;
- `<base>-preview.html`: tabbed local preview with zoom, pan, Fit, and per-view export;
- `<base>-<view-id>.svg`: editable semantic vector for each view;
- `<base>-<view-id>.png`: fixed-resolution review image for each view.

Do not create a separate rules file, duplicate relationship matrix, legacy model, migration script, or single-view compatibility artifact.

## Validation Order

Run the dependency-free pipeline in this order:

```text
node <skill-dir>/scripts/check-topology-artifacts.mjs --model <model.json> --out-dir <dir> --base <name>
node <skill-dir>/scripts/check-svg-geometry.mjs --model <model.json> --out-dir <dir> --base <name>
node <skill-dir>/scripts/check-topology-readability.mjs --model <model.json> --out-dir <dir> --base <name>
node <skill-dir>/scripts/render-svg-png.mjs --svg <base>-<view-id>.svg --out <base>-<view-id>.png
node <skill-dir>/scripts/check-topology-artifacts.mjs --model <model.json> --out-dir <dir> --base <name> --require-png
```

Use `--view <id>` for a focused recheck, but run all views before delivery.

## Artifact Check

`check-topology-artifacts.mjs` verifies:

- schema 2 only and both confirmation gates;
- a structured confirmed visual blueprint, including first-read structure, complete branches, selector evidence, current/planned resolution, semantic types, wireframe, and view estimates;
- confirmed overview mode, per-view audience level, structured narrative, directional main paths, and structured main-flow mappings;
- one overview and at most two details;
- fact IDs, group membership, relationship endpoints, forbidden relationships, and documentation-only reasons;
- relationship coverage and valid overview-only aggregation;
- main relationships cannot be documentation-only and must appear in a main path;
- no orphaned placement in any view unless it is explicitly `contextOnly` with a reason;
- main-flow placements form a connected subgraph through the declared main-flow connectors;
- every alternative branch includes outbound, return, and outcome phases and reaches a real outcome node;
- current/planned status remains aligned from facts through connectors, paths, SVG semantics, and the visible legend;
- stage columns use stage guides rather than false system or deployment zones;
- per-view SVG presence, dimensions, viewBox, unique IDs, and semantic parity;
- `data-view`, `data-relationships`, endpoints, direction, required devices, display level, main-path membership, and emphasis;
- every structured main-flow item rendered in the SVG and retained in Markdown;
- unified Markdown relationship coverage and preview view registration;
- required and forbidden text;
- pure grayscale or exactly one declared accent;
- no gradient, filter, shadow, glow, or undeclared color syntax;
- per-view PNG signature and dimensions when `--require-png` is used.

## Geometry Check

`check-svg-geometry.mjs` treats these as hard failures in overview and detail views:

- placement, label, route, or zone outside the canvas;
- placement overlap;
- a placement outside its declared structural boundary;
- a single-child boundary with more than the permitted title-adjusted padding;
- estimated title, subtitle, device-label, or connector-label overflow;
- label-to-label or label-to-placement collision;
- connector not starting or ending at the declared placement boundary;
- connector through an unrelated placement or label;
- declared required device not actually traversed;
- long overlap with a placement border;
- independent connectors sharing a visible collinear track;
- short terminal segments;
- undeclared connector crossings;
- missing semantic SVG placements or connectors.

Straight and orthogonal routes are checked exactly. Cubic Bezier paths are sampled and always produce a visual-review warning near obstacles.

## Readability Check

`check-topology-readability.mjs` prints each view's Fit percentage and effective main/secondary font sizes.

Overview hard failures:

- more than 18 placements or connectors;
- ordinary-node degree greater than 6;
- more than 4 bends per connector;
- route/minimum-orthogonal-distance ratio greater than 2.5;
- long boundary-hugging route;
- effective main text below 12px or secondary text below 10px;
- undeclared crossing or discontinuous declared main path.
- directionally invalid, prematurely terminated, or incompletely mapped main path;
- content utilization below 55% of the drawable canvas;
- sparse boundary occupancy or a large empty band along the primary axis;
- three or more semantic roles collapsed into fewer than three rendered forms;
- a current/planned comparison without its grayscale status legend.

Detail density and effective-font conditions produce warnings. Bend, detour, boundary-hugging, diagonal-stage, and axis-backtracking conditions fail when they affect a declared main-path connector and warn when they affect only a supporting connector. Undeclared crossings, invalid main paths, and low content utilization always fail.

When a check fails, fix in this order:

1. move secondary facts from the overview into a detail view;
2. aggregate only valid opposite-direction facts for the same endpoints and device path;
3. replace accepted repeated overview members with one semantic group;
4. change stage, lane, or zone placement;
5. reroute locally with fewer bends and shorter paths.

Do not reduce font size, stretch the canvas indefinitely, route along the perimeter, hide facts, or weaken thresholds.

## Regression Suite

Run after changing the model, generator, or any checker:

```text
node <skill-dir>/scripts/test-topology-skill.mjs
```

The suite covers a valid structure-flow overlay, semantic shapes, structured confirmation, evidence/intent selection conflicts, complete and broken branches, executor-versus-outcome closure, all-view orphan rejection, declared context nodes, connected main-flow mappings, semantic-form collapse, stage/zone misuse, status legends, status parity, sparse containers, 55% overview utilization, empty bands, density, supporting-detail warnings, and grayscale enforcement.

## Browser Acceptance

Serve the preview on localhost. When Playwright is available, use its dedicated profile and check:

1. every tab loads the expected view;
2. initial Fit status and effective font values are recorded;
3. 25%, 50%, and 100% zoom, pan, and Fit work;
4. per-view SVG and PNG export works and dimensions match the model;
5. text bounds, routes, arrowheads, labels, and required-device traversal are clear;
6. console errors and failed or unexpected requests are absent;
7. exported SVG content matches the generated SVG and the final PNG is visually inspected.
8. a reviewer can identify the system structure and final outcome within five seconds;
9. every main path is traceable without reading the footer;
10. actor, service, medium, storage, external system, and outcome remain distinguishable without subtitles.

Static success does not prove that the diagram communicates the intended story. Browser and PNG review remain required.

## Reporting Boundaries

Report separately:

- positioning, business model, and visual blueprint confirmed by the user;
- facts supported by code or configuration evidence;
- artifacts generated;
- artifact, geometry, and readability checks;
- Fit scale, effective font sizes, browser behavior, and PNG review;
- product integration, deployment, or field behavior not exercised.
