import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

export const EPSILON = 0.5;
export const TRACK_OVERLAP_LIMIT = 14;
export const DISPLAY_LEVELS = new Set(["business", "implementation", "boundary"]);
export const AUDIENCE_LEVELS = new Set(["business-technical", "implementation"]);
export const FACT_STATUSES = new Set(["current", "planned", "shared"]);
export const VISUAL_TYPES = new Set(["actor", "application", "service", "storage", "physical-media", "external-system", "outcome"]);
export const LAYOUT_PATTERNS = new Set(["structure-flow-overlay", "stage-columns", "swimlanes", "zone-bands"]);
export const BOUNDARY_TYPES = new Set(["system", "deployment", "security", "network"]);
export const FLOW_PHASES = new Set(["outbound", "return", "outcome", "supporting"]);
export const SELECTION_TYPES = new Set(["system-configuration", "user-choice", "automatic-rule", "external-condition"]);

export function fail(message) {
  throw new Error(message);
}

export async function readModel(path) {
  const model = JSON.parse(await readFile(resolve(path), "utf8"));
  validateModelV2(model);
  return model;
}

export function sameArray(first, second) {
  return first.length === second.length && first.every((value, index) => value === second[index]);
}

export function entityMaps(model) {
  return {
    nodes: new Map(model.nodes.map(item => [item.id, item])),
    devices: new Map(model.devices.map(item => [item.id, item])),
    groups: new Map(model.groups.map(item => [item.id, item])),
    relationships: new Map(model.relationships.map(item => [item.id, item])),
  };
}

export function displayText(fact, placement) {
  return {
    label: placement.displayLabel || fact.label,
    subtitle: placement.displaySubtitle ?? fact.subtitle ?? "",
  };
}

export function mainConnectorIds(view) {
  return new Set(view.mainPaths.flatMap(path => path.connectorIds));
}

export function traceMainPath(view, path) {
  const connectors = new Map(view.connectors.map(item => [item.id, item]));
  let current = path.startRef;
  const refs = [current];
  for (const connectorId of path.connectorIds) {
    const connector = connectors.get(connectorId);
    if (!connector) fail(`${view.id}.${path.id} references unknown connector ${connectorId}`);
    let next = null;
    if ((connector.direction === "forward" || connector.direction === "bidirectional") && connector.from === current) next = connector.to;
    else if ((connector.direction === "reverse" || connector.direction === "bidirectional") && connector.to === current) next = connector.from;
    if (!next) fail(`${view.id}.${path.id} cannot traverse ${connector.id} from ${current} in direction ${connector.direction}`);
    current = next;
    refs.push(current);
  }
  if (current !== path.endRef) fail(`${view.id}.${path.id} ends at ${current}; expected ${path.endRef}`);
  return refs;
}

function assertText(value, field) {
  if (typeof value !== "string" || value.trim() === "") fail(`${field} must be non-empty text`);
}

function assertNumber(value, field, minimum = 0) {
  if (!Number.isFinite(value) || value < minimum) fail(`${field} must be a number >= ${minimum}`);
}

function assertBox(value, field) {
  if (!value || typeof value !== "object") fail(`${field} must be a box`);
  assertNumber(value.x, `${field}.x`);
  assertNumber(value.y, `${field}.y`);
  assertNumber(value.width, `${field}.width`, 1);
  assertNumber(value.height, `${field}.height`, 1);
}

function assertStringArray(value, field, minimum = 0) {
  if (!Array.isArray(value) || value.length < minimum) fail(`${field} must contain at least ${minimum} item(s)`);
  value.forEach((item, index) => assertText(item, `${field}[${index}]`));
}

function effectiveVisualType(fact, placement) {
  return placement.renderAs || fact.visualType;
}

function connectedSubgraph(view, connectorIds, placementRefs) {
  const connectors = new Map(view.connectors.map(item => [item.id, item]));
  const adjacency = new Map(placementRefs.map(ref => [ref, new Set()]));
  for (const id of connectorIds) {
    const connector = connectors.get(id);
    if (!connector) continue;
    if (adjacency.has(connector.from) && adjacency.has(connector.to)) {
      adjacency.get(connector.from).add(connector.to);
      adjacency.get(connector.to).add(connector.from);
    }
  }
  const start = placementRefs[0], visited = new Set(start ? [start] : []), queue = start ? [start] : [];
  while (queue.length) {
    for (const next of adjacency.get(queue.shift()) || []) if (!visited.has(next)) { visited.add(next); queue.push(next); }
  }
  return placementRefs.every(ref => visited.has(ref) && (placementRefs.length === 1 || adjacency.get(ref)?.size));
}

function refRepresents(ref, entity, groups) {
  return ref === entity || (groups.has(ref) && groups.get(ref).memberIds.includes(entity));
}

export function relationshipMatchesConnector(relationship, connector, groups) {
  const direct = refRepresents(connector.from, relationship.from, groups) && refRepresents(connector.to, relationship.to, groups);
  const reverse = refRepresents(connector.from, relationship.to, groups) && refRepresents(connector.to, relationship.from, groups);
  if (connector.direction === "bidirectional") return direct || reverse;
  if (connector.direction === "reverse") return reverse;
  return direct;
}

export function validateModelV2(model) {
  if (model.schemaVersion !== 2) fail("schemaVersion 2 is required; V1 models are not supported");
  for (const field of ["meta", "confirmation", "style", "acceptance"]) {
    if (!model[field] || typeof model[field] !== "object") fail(`model.${field} is required`);
  }
  for (const field of ["nodes", "devices", "groups", "relationships", "forbiddenRelationships", "views", "notes"]) {
    if (!Array.isArray(model[field])) fail(`model.${field} must be an array`);
  }
  for (const gate of ["positioning", "businessModel"]) {
    if (model.confirmation?.[gate]?.confirmed !== true) fail(`${gate} confirmation is required before generation`);
    assertText(model.confirmation[gate].basis, `confirmation.${gate}.basis`);
  }
  const blueprint = model.confirmation.businessModel.visualBlueprint;
  if (!blueprint || typeof blueprint !== "object") fail("confirmation.businessModel.visualBlueprint is required; a boolean confirmation is insufficient");
  if (blueprint.overviewForm !== "structure-flow-overlay") fail("visualBlueprint.overviewForm must be structure-flow-overlay for the default single-feature technical overview");
  for (const field of ["firstRead", "readingDirection", "startRef", "currentPlannedPolicy", "asciiWireframe"]) assertText(blueprint[field], `visualBlueprint.${field}`);
  if (!new Set(["current-only", "planned-only", "comparison"]).has(blueprint.currentPlannedPolicy)) fail("visualBlueprint.currentPlannedPolicy must be current-only, planned-only, or comparison");
  assertStringArray(blueprint.structureBoundaries, "visualBlueprint.structureBoundaries", 1);
  assertStringArray(blueprint.outcomeRefs, "visualBlueprint.outcomeRefs", 1);
  assertStringArray(blueprint.visualHierarchy, "visualBlueprint.visualHierarchy", 2);
  if (!Array.isArray(blueprint.branches)) fail("visualBlueprint.branches must be an array");
  for (const branch of blueprint.branches) {
    for (const field of ["id", "decisionOwner", "condition", "selectionType", "splitRef", "mergeRef"]) assertText(branch[field], `visualBlueprint.branches.${field}`);
    if (!SELECTION_TYPES.has(branch.selectionType)) fail(`visualBlueprint branch ${branch.id} has invalid selectionType`);
    assertStringArray(branch.pathIds, `visualBlueprint.branches.${branch.id}.pathIds`, 2);
    if (!branch.selectionEvidence || typeof branch.selectionEvidence !== "object") fail(`visualBlueprint branch ${branch.id} requires selectionEvidence`);
    assertText(branch.selectionEvidence.source, `visualBlueprint.branches.${branch.id}.selectionEvidence.source`);
    if (!SELECTION_TYPES.has(branch.selectionEvidence.observedType)) fail(`visualBlueprint branch ${branch.id} has invalid observed selection type`);
    if (!new Set(["none", "current", "planned", "comparison"]).has(branch.selectionEvidence.resolution)) fail(`visualBlueprint branch ${branch.id} has invalid selection conflict resolution`);
    const conflict = branch.selectionEvidence.observedType !== branch.selectionType;
    if (conflict && branch.selectionEvidence.resolution === "none") fail(`visualBlueprint branch ${branch.id} selectionType contradicts evidence without an explicit current/planned resolution`);
    if (!conflict && branch.selectionEvidence.resolution !== "none") fail(`visualBlueprint branch ${branch.id} declares a selection conflict that does not exist`);
    if (conflict && blueprint.currentPlannedPolicy !== "comparison" && branch.selectionEvidence.resolution !== blueprint.currentPlannedPolicy.replace("-only", "")) fail(`visualBlueprint branch ${branch.id} selection resolution is incompatible with currentPlannedPolicy`);
  }
  if (!Array.isArray(blueprint.viewEstimates) || blueprint.viewEstimates.length === 0) fail("visualBlueprint.viewEstimates must be non-empty");
  for (const estimate of blueprint.viewEstimates) {
    assertText(estimate.viewId, "visualBlueprint.viewEstimates.viewId");
    assertNumber(estimate.placements, `visualBlueprint.viewEstimates.${estimate.viewId}.placements`);
    assertNumber(estimate.connectors, `visualBlueprint.viewEstimates.${estimate.viewId}.connectors`);
  }
  if (!new Set(["business-technical-closure", "implementation-overview"]).has(model.meta.overviewMode)) fail("meta.overviewMode must be business-technical-closure or implementation-overview");
  if (!new Set(["current", "planned", "comparison"]).has(model.meta.viewpoint)) fail("meta.viewpoint must be current, planned, or comparison");
  if (!new Set(["grayscale", "grayscale-accent"]).has(model.style.mode)) fail("style.mode must be grayscale or grayscale-accent");
  if (model.style.mode === "grayscale" && model.style.accent !== null) fail("grayscale mode requires accent to be null");
  if (model.style.mode === "grayscale-accent") {
    if (!/^#[0-9a-f]{6}$/i.test(model.style.accent?.color || "")) fail("grayscale-accent requires one #rrggbb accent");
    assertText(model.style.accent?.meaning, "style.accent.meaning");
  }
  for (const key of ["title", "purpose", "zoneTitle", "zoneSubtitle", "nodeTitle", "nodeSubtitle", "deviceLabel", "connectorLabel", "footer"]) {
    assertNumber(model.style.typography?.[key], `style.typography.${key}`, 1);
  }

  const allIds = new Set();
  for (const [collection, kind] of [[model.nodes, "node"], [model.devices, "device"], [model.groups, "group"], [model.relationships, "relationship"]]) {
    for (const item of collection) {
      assertText(item.id, `${kind}.id`);
      if (allIds.has(item.id)) fail(`duplicate fact id: ${item.id}`);
      allIds.add(item.id);
    }
  }
  const maps = entityMaps(model);
  const endpoints = new Set([...maps.nodes.keys(), ...maps.groups.keys()]);
  for (const node of model.nodes) {
    assertText(node.label, `${node.id}.label`);
    if (!FACT_STATUSES.has(node.status)) fail(`${node.id}.status must be current, planned, or shared`);
    if (!VISUAL_TYPES.has(node.visualType)) fail(`${node.id}.visualType is invalid`);
  }
  for (const device of model.devices) {
    assertText(device.label, `${device.id}.label`);
    if (!FACT_STATUSES.has(device.status)) fail(`${device.id}.status must be current, planned, or shared`);
    if (device.visualType !== "physical-media") fail(`${device.id}.visualType must be physical-media`);
  }
  for (const group of model.groups) {
    assertText(group.label, `${group.id}.label`);
    if (!FACT_STATUSES.has(group.status)) fail(`${group.id}.status must be current, planned, or shared`);
    if (!Array.isArray(group.memberIds) || group.memberIds.length === 0) fail(`${group.id}.memberIds must be non-empty`);
    for (const member of group.memberIds) if (!maps.nodes.has(member)) fail(`${group.id} references unknown node ${member}`);
  }
  for (const relationship of model.relationships) {
    for (const field of ["from", "to", "initiator", "method", "direction"]) assertText(relationship[field], `${relationship.id}.${field}`);
    if (!endpoints.has(relationship.from) || !endpoints.has(relationship.to) || !endpoints.has(relationship.initiator)) fail(`${relationship.id} has an unknown endpoint or initiator`);
    if (!Array.isArray(relationship.viaDevices)) fail(`${relationship.id}.viaDevices must be an array`);
    for (const device of relationship.viaDevices) if (!maps.devices.has(device)) fail(`${relationship.id} references unknown device ${device}`);
    if (!new Set(["main", "supporting"]).has(relationship.narrativeRole)) fail(`${relationship.id}.narrativeRole must be main or supporting`);
    if (!FACT_STATUSES.has(relationship.status)) fail(`${relationship.id}.status must be current, planned, or shared`);
    if (relationship.documentationOnly === true) assertText(relationship.documentationReason, `${relationship.id}.documentationReason`);
    if (relationship.documentationOnly === true && relationship.narrativeRole === "main") fail(`${relationship.id} is a main narrative relationship and cannot be documentationOnly`);
  }
  for (const forbidden of model.forbiddenRelationships) {
    if (model.relationships.some(item => item.from === forbidden.from && item.to === forbidden.to)) fail(`forbidden relationship exists: ${forbidden.from} -> ${forbidden.to}`);
  }

  if (model.views.filter(view => view.kind === "overview").length !== 1) fail("exactly one overview view is required");
  if (model.views.length > 3) fail("a model may contain one overview and at most two detail views");
  const viewIds = new Set();
  const covered = new Set();
  const mainPathRelationships = new Set();
  let emphasized = 0;
  for (const view of model.views) {
    assertText(view.id, "view.id");
    if (viewIds.has(view.id)) fail(`duplicate view id: ${view.id}`);
    viewIds.add(view.id);
    if (!new Set(["overview", "detail"]).has(view.kind)) fail(`${view.id}.kind must be overview or detail`);
    if (!AUDIENCE_LEVELS.has(view.audienceLevel)) fail(`${view.id}.audienceLevel must be business-technical or implementation`);
    if (!view.narrative || typeof view.narrative !== "object") fail(`${view.id}.narrative is required`);
    assertText(view.narrative.question, `${view.id}.narrative.question`);
    assertText(view.narrative.audience, `${view.id}.narrative.audience`);
    assertBox({ x: 0, y: 0, ...view.canvas }, `${view.id}.canvas`);
    assertNumber(view.reviewViewport?.width, `${view.id}.reviewViewport.width`, 1);
    assertNumber(view.reviewViewport?.height, `${view.id}.reviewViewport.height`, 1);
    for (const key of ["toolbarHeight", "statusHeight", "padding"]) assertNumber(view.reviewViewport?.[key], `${view.id}.reviewViewport.${key}`);
    for (const field of ["zones", "stageGuides", "placements", "connectors", "mainPaths", "allowedCrossings", "mainFlow"]) {
      if (!Array.isArray(view[field])) fail(`${view.id}.${field} must be an array`);
    }
    if (!LAYOUT_PATTERNS.has(view.layout?.pattern)) fail(`${view.id}.layout.pattern is invalid`);
    if (view.kind === "overview" && model.meta.diagramType === "single-feature-technical" && view.layout.pattern !== "structure-flow-overlay") fail(`${view.id} single-feature technical overview must use structure-flow-overlay`);
    if (view.layout.pattern === "stage-columns" && view.zones.length) fail(`${view.id} stage-columns must use stageGuides; conceptual stages cannot be rendered as zones`);
    if (view.kind === "overview" && view.mainPaths.length === 0) fail(`${view.id} overview requires at least one mainPath`);
    if (view.kind === "overview" && model.meta.overviewMode === "business-technical-closure" && view.audienceLevel !== "business-technical") fail(`${view.id} must use business-technical audienceLevel for a business-technical closure overview`);
    const zoneIds = new Set();
    for (const zone of view.zones) {
      assertText(zone.id, `${view.id}.zone.id`);
      if (zoneIds.has(zone.id)) fail(`${view.id} duplicates zone ${zone.id}`);
      zoneIds.add(zone.id);
      assertText(zone.label, `${view.id}.${zone.id}.label`);
      if (!BOUNDARY_TYPES.has(zone.boundaryType)) fail(`${view.id}.${zone.id}.boundaryType is invalid; stage labels are not boundaries`);
      if (!FACT_STATUSES.has(zone.status)) fail(`${view.id}.${zone.id}.status must be current, planned, or shared`);
      assertStringArray(zone.memberRefs, `${view.id}.${zone.id}.memberRefs`, 1);
      assertBox(zone, `${view.id}.${zone.id}`);
    }
    for (const guide of view.stageGuides) {
      assertText(guide.id, `${view.id}.stageGuides.id`);
      assertText(guide.label, `${view.id}.${guide.id}.label`);
      assertNumber(guide.x, `${view.id}.${guide.id}.x`);
      assertNumber(guide.width, `${view.id}.${guide.id}.width`, 1);
    }
    const placementRefs = new Set();
    const effectiveTypes = new Set();
    for (const placement of view.placements) {
      if (!maps.nodes.has(placement.ref) && !maps.devices.has(placement.ref) && !maps.groups.has(placement.ref)) fail(`${view.id} references unknown placement ${placement.ref}`);
      if (placementRefs.has(placement.ref)) fail(`${view.id} duplicates placement ${placement.ref}`);
      placementRefs.add(placement.ref);
      assertBox(placement, `${view.id}.${placement.ref}`);
      if (!DISPLAY_LEVELS.has(placement.displayLevel)) fail(`${view.id}.${placement.ref}.displayLevel must be business, implementation, or boundary`);
      if (placement.displayLabel !== undefined) assertText(placement.displayLabel, `${view.id}.${placement.ref}.displayLabel`);
      if (placement.displaySubtitle !== undefined && typeof placement.displaySubtitle !== "string") fail(`${view.id}.${placement.ref}.displaySubtitle must be text`);
      if (view.kind === "overview" && model.meta.overviewMode === "business-technical-closure" && placement.displayLevel === "implementation") fail(`${view.id}.${placement.ref} uses an implementation-level label in a business-technical overview`);
      if (maps.devices.has(placement.ref)) assertBox(placement.labelBox, `${view.id}.${placement.ref}.labelBox`);
      const fact = maps.nodes.get(placement.ref) || maps.groups.get(placement.ref) || maps.devices.get(placement.ref);
      if (placement.renderAs !== undefined && !VISUAL_TYPES.has(placement.renderAs)) fail(`${view.id}.${placement.ref}.renderAs is invalid`);
      if (!maps.groups.has(placement.ref)) effectiveTypes.add(effectiveVisualType(fact, placement));
      if (placement.contextOnly === true) assertText(placement.contextReason, `${view.id}.${placement.ref}.contextReason`);
      emphasized += placement.emphasis === true ? 1 : 0;
    }
    for (const zone of view.zones) for (const ref of zone.memberRefs) if (!placementRefs.has(ref)) fail(`${view.id}.${zone.id} references invisible member ${ref}`);
    const factTypes = new Set(view.placements.filter(item => !maps.groups.has(item.ref)).map(item => (maps.nodes.get(item.ref) || maps.devices.get(item.ref)).visualType));
    if (factTypes.size >= 3 && effectiveTypes.size < 3) fail(`${view.id} collapses ${factTypes.size} semantic roles into fewer than three rendered shapes`);
    const connectorIds = new Set();
    for (const connector of view.connectors) {
      assertText(connector.id, `${view.id}.connector.id`);
      if (connectorIds.has(connector.id)) fail(`${view.id} duplicates connector ${connector.id}`);
      connectorIds.add(connector.id);
      if (!placementRefs.has(connector.from) || !placementRefs.has(connector.to)) fail(`${view.id}.${connector.id} endpoints must be visible placements`);
      if (!Array.isArray(connector.relationshipIds) || connector.relationshipIds.length === 0) fail(`${view.id}.${connector.id} requires relationshipIds`);
      if (!Array.isArray(connector.viaDevices)) fail(`${view.id}.${connector.id}.viaDevices must be an array`);
      for (const device of connector.viaDevices) if (!placementRefs.has(device) || !maps.devices.has(device)) fail(`${view.id}.${connector.id} references invisible or non-device ${device}`);
      if (!new Set(["forward", "reverse", "bidirectional", "none"]).has(connector.direction)) fail(`${view.id}.${connector.id} has invalid direction`);
      if (!FACT_STATUSES.has(connector.status)) fail(`${view.id}.${connector.id}.status must be current, planned, or shared`);
      if (!FLOW_PHASES.has(connector.flowPhase)) fail(`${view.id}.${connector.id}.flowPhase is invalid`);
      if (!connector.route || !new Set(["polyline", "bezier"]).has(connector.route.type)) fail(`${view.id}.${connector.id} has invalid route type`);
      const requiredPoints = connector.route.type === "bezier" ? 4 : 2;
      if (!Array.isArray(connector.route.points) || connector.route.points.length < requiredPoints || (connector.route.type === "bezier" && connector.route.points.length !== 4)) fail(`${view.id}.${connector.id} has invalid route points`);
      for (const [index, point] of connector.route.points.entries()) {
        assertNumber(point.x, `${view.id}.${connector.id}.route.points[${index}].x`);
        assertNumber(point.y, `${view.id}.${connector.id}.route.points[${index}].y`);
      }
      if (connector.label) assertBox(connector.labelBox, `${view.id}.${connector.id}.labelBox`);
      const relationships = connector.relationshipIds.map(id => {
        const relationship = maps.relationships.get(id);
        if (!relationship) fail(`${view.id}.${connector.id} references unknown relationship ${id}`);
        if (!relationshipMatchesConnector(relationship, connector, maps.groups)) fail(`${view.id}.${connector.id} illegally aggregates relationship ${id} across different endpoints`);
        if (!sameArray(relationship.viaDevices, connector.viaDevices)) fail(`${view.id}.${connector.id} device path differs from relationship ${id}`);
        covered.add(id);
        return relationship;
      });
      if (relationships.some(item => item.status !== connector.status && item.status !== "shared")) fail(`${view.id}.${connector.id} status differs from its relationship facts`);
      if (relationships.length > 1) {
        if (view.kind !== "overview") fail(`${view.id}.${connector.id} aggregates relationships outside an overview`);
        if (connector.direction !== "bidirectional") fail(`${view.id}.${connector.id} aggregates multiple facts but is not bidirectional`);
        const endpointPairs = new Set(relationships.map(item => [item.from, item.to].sort().join("::")));
        if (endpointPairs.size !== 1) fail(`${view.id}.${connector.id} cannot aggregate relationships with different endpoint pairs`);
        const forward = relationships.some(item => refRepresents(connector.from, item.from, maps.groups) && refRepresents(connector.to, item.to, maps.groups));
        const reverse = relationships.some(item => refRepresents(connector.from, item.to, maps.groups) && refRepresents(connector.to, item.from, maps.groups));
        if (!forward || !reverse) fail(`${view.id}.${connector.id} aggregation must contain both endpoint directions`);
      }
      emphasized += connector.emphasis === true ? 1 : 0;
    }
    const connectedRefs = new Set();
    for (const connector of view.connectors) {
      connectedRefs.add(connector.from);
      connectedRefs.add(connector.to);
      connector.viaDevices.forEach(id => connectedRefs.add(id));
    }
    for (const placement of view.placements) if (!connectedRefs.has(placement.ref) && placement.contextOnly !== true) fail(`${view.id}.${placement.ref} is an orphaned placement`);
    const visibleStatuses = new Set([
      ...view.placements.map(item => (maps.nodes.get(item.ref) || maps.devices.get(item.ref) || maps.groups.get(item.ref)).status),
      ...view.connectors.map(item => item.status),
    ]);
    const mixedStatus = visibleStatuses.has("current") && visibleStatuses.has("planned");
    if (mixedStatus) {
      if (view.statusLegend?.visible !== true) fail(`${view.id} mixes current and planned facts without a visible statusLegend`);
      assertBox(view.statusLegend, `${view.id}.statusLegend`);
      assertText(view.statusLegend.currentLabel, `${view.id}.statusLegend.currentLabel`);
      assertText(view.statusLegend.plannedLabel, `${view.id}.statusLegend.plannedLabel`);
    }
    const pathIds = new Set();
    const tracedPaths = new Map();
    const pathConnectorIds = new Set();
    for (const path of view.mainPaths) {
      assertText(path.id, `${view.id}.mainPaths.id`);
      assertText(path.label, `${view.id}.${path.id}.label`);
      if (pathIds.has(path.id)) fail(`${view.id} duplicates mainPath ${path.id}`);
      pathIds.add(path.id);
      assertText(path.startRef, `${view.id}.${path.id}.startRef`);
      assertText(path.endRef, `${view.id}.${path.id}.endRef`);
      if (!FACT_STATUSES.has(path.status)) fail(`${view.id}.${path.id}.status must be current, planned, or shared`);
      if (!placementRefs.has(path.startRef) || !placementRefs.has(path.endRef)) fail(`${view.id}.${path.id} startRef and endRef must be visible placements`);
      if (!Array.isArray(path.connectorIds) || path.connectorIds.length === 0) fail(`${view.id}.${path.id} requires connectorIds`);
      if (new Set(path.connectorIds).size !== path.connectorIds.length) fail(`${view.id}.${path.id} repeats a connector; main paths must be acyclic`);
      for (const id of path.connectorIds) if (!connectorIds.has(id)) fail(`${view.id}.${path.id} references unknown connector ${id}`);
      const refs = traceMainPath(view, path);
      tracedPaths.set(path.id, refs);
      path.connectorIds.forEach(id => pathConnectorIds.add(id));
      for (const connectorId of path.connectorIds) {
        const connector = view.connectors.find(item => item.id === connectorId);
        connector.relationshipIds.forEach(id => mainPathRelationships.add(id));
      }
    }
    assertText(view.narrative.startRef, `${view.id}.narrative.startRef`);
    if (!placementRefs.has(view.narrative.startRef)) fail(`${view.id}.narrative.startRef must be a visible placement`);
    if (!Array.isArray(view.narrative.endRefs) || view.narrative.endRefs.length === 0) fail(`${view.id}.narrative.endRefs must be non-empty`);
    for (const ref of view.narrative.endRefs) if (!placementRefs.has(ref)) fail(`${view.id}.narrative.endRefs references invisible placement ${ref}`);
    for (const path of view.mainPaths) {
      if (path.startRef !== view.narrative.startRef) fail(`${view.id}.${path.id} must start at narrative.startRef ${view.narrative.startRef}`);
      if (!view.narrative.endRefs.includes(path.endRef)) fail(`${view.id}.${path.id} must end at one of narrative.endRefs`);
    }
    if (!Array.isArray(view.narrative.branchPoints)) fail(`${view.id}.narrative.branchPoints must be an array`);
    for (const branch of view.narrative.branchPoints) {
      assertText(branch.id, `${view.id}.narrative.branchPoints.id`);
      for (const field of ["decisionOwner", "condition", "selectionType"]) assertText(branch[field], `${view.id}.${branch.id}.${field}`);
      if (!SELECTION_TYPES.has(branch.selectionType)) fail(`${view.id}.${branch.id}.selectionType is invalid`);
      const confirmedBranch = blueprint.branches.find(item => item.id === branch.id);
      if (!confirmedBranch) fail(`${view.id}.${branch.id} is missing from the confirmed visual blueprint`);
      for (const field of ["decisionOwner", "condition", "selectionType", "splitRef", "mergeRef"]) if (branch[field] !== confirmedBranch[field]) fail(`${view.id}.${branch.id}.${field} differs from the confirmed visual blueprint`);
      if (!sameArray(branch.pathIds, confirmedBranch.pathIds)) fail(`${view.id}.${branch.id}.pathIds differ from the confirmed visual blueprint`);
      if (!placementRefs.has(branch.splitRef) || !placementRefs.has(branch.mergeRef)) fail(`${view.id}.${branch.id} splitRef and mergeRef must be visible placements`);
      if (!Array.isArray(branch.pathIds) || branch.pathIds.length < 2) fail(`${view.id}.${branch.id} requires at least two pathIds`);
      for (const pathId of branch.pathIds) {
        const refs = tracedPaths.get(pathId);
        if (!refs) fail(`${view.id}.${branch.id} references unknown mainPath ${pathId}`);
        const splitIndex = refs.indexOf(branch.splitRef), mergeIndex = refs.indexOf(branch.mergeRef);
        if (splitIndex < 0 || mergeIndex <= splitIndex) fail(`${view.id}.${branch.id} path ${pathId} does not traverse splitRef then mergeRef`);
        const path = view.mainPaths.find(item => item.id === pathId);
        const phases = new Set(path.connectorIds.map(id => view.connectors.find(item => item.id === id).flowPhase));
        if (view.layout.pattern === "structure-flow-overlay" && (!phases.has("outbound") || !phases.has("return") || !phases.has("outcome"))) fail(`${view.id}.${branch.id} path ${pathId} is incomplete; each branch requires outbound, return, and outcome phases`);
      }
    }
    const flowIds = new Set();
    const flowConnectorIds = new Set();
    for (const flow of view.mainFlow) {
      assertText(flow.id, `${view.id}.mainFlow.id`);
      assertText(flow.text, `${view.id}.${flow.id}.text`);
      if (flowIds.has(flow.id)) fail(`${view.id} duplicates mainFlow ${flow.id}`);
      flowIds.add(flow.id);
      if (!Array.isArray(flow.placementRefs) || flow.placementRefs.length === 0) fail(`${view.id}.${flow.id}.placementRefs must be non-empty`);
      if (!Array.isArray(flow.connectorIds) || flow.connectorIds.length === 0) fail(`${view.id}.${flow.id}.connectorIds must be non-empty`);
      for (const ref of flow.placementRefs) if (!placementRefs.has(ref)) fail(`${view.id}.${flow.id} references invisible placement ${ref}`);
      for (const id of flow.connectorIds) {
        if (!pathConnectorIds.has(id)) fail(`${view.id}.${flow.id} connector ${id} is not part of a mainPath`);
        flowConnectorIds.add(id);
      }
      if (!connectedSubgraph(view, flow.connectorIds, flow.placementRefs)) fail(`${view.id}.${flow.id} placementRefs are not connected by its declared connectors`);
    }
    for (const id of pathConnectorIds) if (!flowConnectorIds.has(id)) fail(`${view.id}.${id} is a mainPath connector without a mainFlow mapping`);
    for (const crossing of view.allowedCrossings) {
      if (!Array.isArray(crossing.connectorIds) || crossing.connectorIds.length !== 2) fail(`${view.id} allowed crossing requires two connectorIds`);
      for (const id of crossing.connectorIds) if (!connectorIds.has(id)) fail(`${view.id} allowed crossing references unknown connector ${id}`);
      assertNumber(crossing.point?.x, `${view.id}.allowedCrossings.point.x`);
      assertNumber(crossing.point?.y, `${view.id}.allowedCrossings.point.y`);
      assertText(crossing.reason, `${view.id}.allowedCrossings.reason`);
    }
  }
  const overview = model.views.find(view => view.kind === "overview");
  if (overview.narrative.startRef !== blueprint.startRef) fail("overview startRef differs from the confirmed visual blueprint");
  if (!sameArray(overview.narrative.endRefs, blueprint.outcomeRefs)) fail("overview outcomes differ from the confirmed visual blueprint");
  const overviewZoneLabels = new Set(overview.zones.map(zone => zone.label));
  for (const boundary of blueprint.structureBoundaries) if (!overviewZoneLabels.has(boundary)) fail(`overview is missing confirmed structural boundary ${boundary}`);
  for (const ref of overview.narrative.endRefs) {
    const fact = maps.nodes.get(ref);
    if (model.meta.overviewMode === "business-technical-closure" && fact?.visualType !== "outcome") fail(`${overview.id}.${ref} is a closure outcome but is not rendered as an outcome`);
  }
  const estimates = new Map(blueprint.viewEstimates.map(item => [item.viewId, item]));
  for (const view of model.views) {
    const estimate = estimates.get(view.id);
    if (!estimate) fail(`visualBlueprint.viewEstimates is missing ${view.id}`);
    if (estimate.placements !== view.placements.length || estimate.connectors !== view.connectors.length) fail(`visualBlueprint estimate for ${view.id} differs from the rendered placement/connector count`);
  }
  for (const relationship of model.relationships) {
    if (!covered.has(relationship.id) && relationship.documentationOnly !== true) fail(`${relationship.id} is not represented in any view`);
    if (relationship.narrativeRole === "main" && !mainPathRelationships.has(relationship.id)) fail(`${relationship.id} is a main narrative relationship not represented by any mainPath`);
  }
  if (model.style.mode === "grayscale" && emphasized > 0) fail("grayscale mode does not allow emphasized view elements");
  if (model.style.mode === "grayscale-accent" && emphasized === 0) fail("grayscale-accent mode requires at least one emphasized view element");
  if (!Array.isArray(model.acceptance.requiredText) || !Array.isArray(model.acceptance.forbiddenText)) fail("acceptance text arrays are required");
}

export function selectedViews(model, viewId) {
  if (!viewId) return model.views;
  const view = model.views.find(item => item.id === viewId);
  if (!view) fail(`unknown view: ${viewId}`);
  return [view];
}

export function artifactPaths(outDir, base, view) {
  const root = resolve(outDir);
  return {
    markdown: join(root, `${base}.md`),
    preview: join(root, `${base}-preview.html`),
    svg: join(root, `${base}-${view.id}.svg`),
    png: join(root, `${base}-${view.id}.png`),
  };
}

export function right(box) { return box.x + box.width; }
export function bottom(box) { return box.y + box.height; }
export function overlaps(first, second, inset = 0) {
  return first.x < right(second) - inset && right(first) > second.x + inset && first.y < bottom(second) - inset && bottom(first) > second.y + inset;
}
export function containsPoint(box, point, inset = 0) {
  return point.x > box.x + inset && point.x < right(box) - inset && point.y > box.y + inset && point.y < bottom(box) - inset;
}
export function pointOnBoundary(box, point, tolerance = 2) {
  const vertical = (Math.abs(point.x - box.x) <= tolerance || Math.abs(point.x - right(box)) <= tolerance) && point.y >= box.y - tolerance && point.y <= bottom(box) + tolerance;
  const horizontal = (Math.abs(point.y - box.y) <= tolerance || Math.abs(point.y - bottom(box)) <= tolerance) && point.x >= box.x - tolerance && point.x <= right(box) + tolerance;
  return vertical || horizontal;
}

export function cubicPoint(points, t) {
  const inverse = 1 - t;
  return {
    x: inverse ** 3 * points[0].x + 3 * inverse ** 2 * t * points[1].x + 3 * inverse * t ** 2 * points[2].x + t ** 3 * points[3].x,
    y: inverse ** 3 * points[0].y + 3 * inverse ** 2 * t * points[1].y + 3 * inverse * t ** 2 * points[2].y + t ** 3 * points[3].y,
  };
}

export function routePoints(connector) {
  if (connector.route.type !== "bezier") return connector.route.points;
  return Array.from({ length: 49 }, (_, index) => cubicPoint(connector.route.points, index / 48));
}

export function routeSegments(connector) {
  const points = routePoints(connector);
  return points.slice(1).map((point, index) => ({ a: points[index], b: point }));
}

function orientation(a, b, c) {
  const value = (b.y - a.y) * (c.x - b.x) - (b.x - a.x) * (c.y - b.y);
  return Math.abs(value) <= EPSILON ? 0 : value > 0 ? 1 : 2;
}
function onSegment(a, b, c) {
  return b.x <= Math.max(a.x, c.x) + EPSILON && b.x >= Math.min(a.x, c.x) - EPSILON && b.y <= Math.max(a.y, c.y) + EPSILON && b.y >= Math.min(a.y, c.y) - EPSILON;
}
export function segmentsIntersect(first, second) {
  const o1 = orientation(first.a, first.b, second.a);
  const o2 = orientation(first.a, first.b, second.b);
  const o3 = orientation(second.a, second.b, first.a);
  const o4 = orientation(second.a, second.b, first.b);
  if (o1 !== o2 && o3 !== o4) return true;
  return (o1 === 0 && onSegment(first.a, second.a, first.b)) || (o2 === 0 && onSegment(first.a, second.b, first.b)) || (o3 === 0 && onSegment(second.a, first.a, second.b)) || (o4 === 0 && onSegment(second.a, first.b, second.b));
}

export function collinearOverlap(first, second) {
  const h1 = Math.abs(first.a.y - first.b.y) <= EPSILON;
  const h2 = Math.abs(second.a.y - second.b.y) <= EPSILON;
  const v1 = Math.abs(first.a.x - first.b.x) <= EPSILON;
  const v2 = Math.abs(second.a.x - second.b.x) <= EPSILON;
  if (h1 && h2 && Math.abs(first.a.y - second.a.y) <= EPSILON) return Math.max(0, Math.min(Math.max(first.a.x, first.b.x), Math.max(second.a.x, second.b.x)) - Math.max(Math.min(first.a.x, first.b.x), Math.min(second.a.x, second.b.x)));
  if (v1 && v2 && Math.abs(first.a.x - second.a.x) <= EPSILON) return Math.max(0, Math.min(Math.max(first.a.y, first.b.y), Math.max(second.a.y, second.b.y)) - Math.max(Math.min(first.a.y, first.b.y), Math.min(second.a.y, second.b.y)));
  return 0;
}

export function segmentIntersectsBox(segment, box, inset = 2) {
  if (containsPoint(box, segment.a, inset) || containsPoint(box, segment.b, inset)) return true;
  const x1 = box.x + inset, y1 = box.y + inset, x2 = right(box) - inset, y2 = bottom(box) - inset;
  const sides = [
    { a: { x: x1, y: y1 }, b: { x: x2, y: y1 } }, { a: { x: x2, y: y1 }, b: { x: x2, y: y2 } },
    { a: { x: x2, y: y2 }, b: { x: x1, y: y2 } }, { a: { x: x1, y: y2 }, b: { x: x1, y: y1 } },
  ];
  return sides.some(side => segmentsIntersect(segment, side));
}

function intersectionPoint(first, second) {
  const x1 = first.a.x, y1 = first.a.y, x2 = first.b.x, y2 = first.b.y;
  const x3 = second.a.x, y3 = second.a.y, x4 = second.b.x, y4 = second.b.y;
  const denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
  if (Math.abs(denominator) <= EPSILON) return null;
  return {
    x: ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator,
    y: ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator,
  };
}

function near(first, second, tolerance = 3) {
  return Math.hypot(first.x - second.x, first.y - second.y) <= tolerance;
}

export function connectorCrossingIssues(view) {
  const issues = [];
  for (let firstIndex = 0; firstIndex < view.connectors.length; firstIndex += 1) {
    for (let secondIndex = firstIndex + 1; secondIndex < view.connectors.length; secondIndex += 1) {
      const first = view.connectors[firstIndex], second = view.connectors[secondIndex];
      const allowed = view.allowedCrossings.find(item => item.connectorIds.includes(first.id) && item.connectorIds.includes(second.id));
      const sharedEndpoints = [first.from, first.to].filter(id => id === second.from || id === second.to);
      let found = null;
      for (const a of routeSegments(first)) {
        for (const b of routeSegments(second)) {
          if (!segmentsIntersect(a, b) || collinearOverlap(a, b) > EPSILON) continue;
          const point = intersectionPoint(a, b);
          if (!point) continue;
          const atSharedTerminal = sharedEndpoints.length > 0 && [first.route.points[0], first.route.points.at(-1)].some(item => near(item, point)) && [second.route.points[0], second.route.points.at(-1)].some(item => near(item, point));
          if (atSharedTerminal) continue;
          if (allowed && near(allowed.point, point, 5)) continue;
          found = point;
          break;
        }
        if (found) break;
      }
      if (found) issues.push(`${first.id} crosses ${second.id} at ${found.x.toFixed(1)},${found.y.toFixed(1)} without an allowedCrossing`);
    }
  }
  return issues;
}

export function estimatedTextWidth(value, fontSize) {
  return [...String(value)].reduce((sum, character) => sum + (/[^\x00-\xff]/.test(character) ? fontSize : fontSize * 0.58), 0);
}

export function fitScale(view) {
  const viewport = view.reviewViewport;
  const availableWidth = viewport.width - 2 * viewport.padding;
  const availableHeight = viewport.height - viewport.toolbarHeight - viewport.statusHeight - 2 * viewport.padding;
  return Math.min(availableWidth / view.canvas.width, availableHeight / view.canvas.height);
}
