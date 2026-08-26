# Style And Layout

Use these defaults for formal engineering review unless the user confirms a different project style.

## Design Views Before Coordinates

- Give each view one question and one reading direction.
- Use stage columns for technical processing chains.
- Use parallel swimlanes for mutually exclusive branches or independent actors.
- Use zone bands for deployment, network, and security boundaries.
- Use the overview for the primary narrative and detail views for directional or implementation facts.
- Default the overview to a business-technical closure: one visible entry, one or more complete branch paths, an explicit merge where needed, and a visible business outcome.
- For a single-feature technical architecture, default to structure plus flow: draw real system/deployment boundaries first, then overlay outbound work, target execution, result return, and final outcome.
- Keep implementation identifiers, internal interface paths, stores, SDK names, and ports in details or Markdown unless Gate 1 explicitly selects an implementation overview.
- Keep equivalent nodes the same size and reserve dimensions for the longest confirmed label before routing.

Do not solve density by reducing font size, increasing the canvas without limit, placing routes along the outer edge, lowering line width, or omitting confirmed facts. Move secondary facts into a detail view first.

## Overview Limits

The overview must fail review when it contains any of these:

- more than 18 visible placements or 18 connectors;
- degree greater than 6 for an ordinary non-group node;
- an undeclared connector crossing;
- more than 4 bends in one connector;
- route length greater than 2.5 times its shortest orthogonal distance;
- a long route that hugs a canvas boundary;
- effective main text below 12px or secondary text below 10px at Fit.

Detail views still prohibit overlap, routes through unrelated objects, undeclared crossings, and shared independent tracks. Detail density and effective-font violations are warnings that must be resolved or explicitly reported after visual review; bend and detour severity depends on whether the connector belongs to a declared main path.

For connectors declared in a detail view's `mainPaths`, excessive bends, detours, boundary hugging, diagonal stage routes, and backtracking against the primary axis are blocking. Only supporting detail connectors may retain these as explicit warnings.

Every view must use its drawable area deliberately. The overview requires at least 55% utilization; details require at least 42%. Also reject sparse containers, oversized single-child padding, and large empty bands along the primary axis. A large outer bounding box does not compensate for empty interiors.

## Relationship Aggregation

- Preserve every relationship in the fact layer.
- In the overview only, merge opposite request/response or write/read facts into one bidirectional connector when endpoints and required-device paths match.
- Use `data-relationships` to retain the source fact IDs.
- Expand directional facts in a detail view or the generated Markdown.
- Never aggregate unrelated endpoint pairs, security paths, methods that create different meanings, or relationships merely to reduce line count.

## Lines And Labels

- Keep independent connectors on independent visible tracks.
- Render declared main-path connectors darker and stronger than supporting connectors. Visual weight must match narrative importance.
- Prefer straight or orthogonal routes. Use a cubic Bezier only when a smooth bypass materially reduces crossings.
- A connector must not cross unrelated nodes, groups, labels, or devices.
- Required-device traversal must be visible and listed in ordered `viaDevices`.
- Keep paired routes distinguishable at Fit.
- Put protocol, port, C/S, and request labels next to the endpoint or device they describe.
- Give labels explicit owner boxes so overflow and collision checks are deterministic.
- Use arrowheads only for confirmed semantics, such as initiator direction or established bidirectional communication.
- Keep outbound work and returned results on separate parallel or loop-closing tracks. Do not compress an entire request/execution/result lifecycle into one bidirectional arrow.
- Use three visual weights: main-path connectors, supporting connectors, and boundary lines. Equal weight across every line is a readability failure.
- Declare the rare intentional crossing in `allowedCrossings` with the connector pair, exact point, and reason.

## Color And Typography

- Default to white, black, and neutral grays with equal RGB channels.
- Allow one non-gray accent only after the user confirms its exact color and semantic meaning.
- Apply the accent only to placements or connectors marked `emphasis: true`.
- Do not assign colors automatically by role, zone, status, or connection type.
- Do not use gradients, shadows, glow, decorative cards, vendor photos, or marketing-style composition.
- Keep primary and explanatory text black or dark neutral gray.
- In a business-technical overview, use short business stage names. Use placement display overrides rather than renaming implementation facts.
- Record each view's Fit scale and effective main/secondary font sizes during acceptance.
- Current capabilities use solid neutral lines. Planned capabilities use dashed neutral lines. A mixed view requires a visible grayscale legend; color must not carry current/planned meaning.

## Semantic Shapes

Use a restrained, consistent grayscale vocabulary:

| Visual type | Default form |
| --- | --- |
| Actor | Person outline plus label |
| Application or platform | Strong container with a header rule |
| Service | Plain rectangle |
| Storage | Cylinder outline |
| Physical medium | Device outline |
| External system | Double-line boundary |
| Business outcome | Heavy result box with a leading bar |

When a view contains at least three semantic role types, it must render at least three distinct forms. A placement may override its form only when Gate 2 explicitly confirms that abstraction.

## Zones, Groups, And Devices

- Draw zones as containment bands rather than decorative cards.
- Use a group only when the user accepts that its members share one visual role in the overview.
- Draw connectors before foreground devices and nodes so routes appear to enter them without obscuring labels.
- A bypass needs visible clearance; a declared traversal must cross the device bounds.
- Zone containment is expected. Placement-to-placement overlap is not.
- Zones represent real application, deployment, network, or security containment. Conceptual processing stages use light guide lines and headings, never filled boundary boxes.
- A single-child zone must hug its child after reserving the title area; do not leave decorative whitespace around one node.

## Explanatory Text

- Add image-contained notes only when the image must independently explain process, ports, assumptions, or contact details.
- Use aligned columns and thin rules instead of nested cards.
- Include the minimum complete narrative: initiator, major stages, real approval or acceptance steps, and final state. Render every structured `mainFlow` item; never silently truncate the footer.
- Use the localized footer title `业务主线` by default. Critical steps belong beside their connectors; the footer summarizes rather than repairs a missing route.
- Do not leak local paths, agent notes, source-research narration, or unapproved implementation identifiers.

## Semantic SVG

Every rendered item belongs to a view. Aggregated connectors expose all source facts:

```xml
<g id="overview-connector-platform-exchange"
   data-role="connector"
   data-view="overview"
   data-relationships="request-fact,response-fact"
   data-from="platform-a"
   data-to="platform-b"
   data-direction="bidirectional"
   data-via-devices="security-boundary">
  ...
</g>
```

Keep `data-view`, `data-role`, `data-ref`, `data-relationships`, `data-from`, `data-to`, `data-direction`, `data-via-devices`, `data-owner`, and `data-emphasis` aligned with the V2 model.
