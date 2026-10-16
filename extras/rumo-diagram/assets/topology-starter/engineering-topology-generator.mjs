#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";

const DIAGRAM_TYPES = new Set([
  "single-feature-technical",
  "system-business",
  "business-function-technical-overview",
  "field-deployment-topology",
  "security-zone-network-topology",
  "data-interface-link",
]);
const VIEW_KINDS = new Set(["overview", "detail"]);
const AXES = new Set(["left-to-right", "top-to-bottom"]);
const ROUTES = new Set(["polyline", "bezier"]);
const DIRECTIONS = new Set(["forward", "reverse", "bidirectional", "none"]);
const DISPLAY_LEVELS = new Set(["business", "implementation", "boundary"]);
const AUDIENCE_LEVELS = new Set(["business-technical", "implementation"]);
const FACT_STATUSES = new Set(["current", "planned", "shared"]);
const VISUAL_TYPES = new Set(["actor", "application", "service", "storage", "physical-media", "external-system", "outcome"]);
const LAYOUT_PATTERNS = new Set(["structure-flow-overlay", "stage-columns", "swimlanes", "zone-bands"]);
const BOUNDARY_TYPES = new Set(["system", "deployment", "security", "network"]);
const FLOW_PHASES = new Set(["outbound", "return", "outcome", "supporting"]);
const SELECTION_TYPES = new Set(["system-configuration", "user-choice", "automatic-rule", "external-condition"]);

function parseArgs(argv) {
  const args = { model: "", outDir: ".", base: "" };
  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--help" || value === "-h") args.help = true;
    else if (value === "--model" && argv[index + 1]) args.model = argv[++index];
    else if (value === "--out-dir" && argv[index + 1]) args.outDir = argv[++index];
    else if (value === "--base" && argv[index + 1]) args.base = argv[++index];
    else throw new Error(`Unknown or incomplete argument: ${value}`);
  }
  return args;
}

function fail(code, message) {
  throw new Error(`${code}: ${message}`);
}

function text(value, field) {
  if (typeof value !== "string" || !value.trim()) fail("MODEL_FIELD", `${field} must be non-empty text`);
  return value.trim();
}

function number(value, field) {
  if (!Number.isFinite(value)) fail("MODEL_FIELD", `${field} must be a finite number`);
  return value;
}

function nonNegative(value, field) {
  number(value, field);
  if (value < 0) fail("MODEL_FIELD", `${field} must be non-negative`);
}

function positive(value, field) {
  number(value, field);
  if (value <= 0) fail("MODEL_FIELD", `${field} must be positive`);
}

function validateBox(item, field) {
  for (const key of ["x", "y"]) nonNegative(item[key], `${field}.${key}`);
  for (const key of ["width", "height"]) positive(item[key], `${field}.${key}`);
}

function textArray(value, field, minimum = 0) {
  if (!Array.isArray(value) || value.length < minimum) fail("MODEL_FIELD", `${field} must contain at least ${minimum} item(s)`);
  value.forEach((item, index) => text(item, `${field}[${index}]`));
}

function connectedSubgraph(view, connectorIds, placementRefs) {
  const connectors = new Map(view.connectors.map(item => [item.id, item]));
  const adjacency = new Map(placementRefs.map(ref => [ref, new Set()]));
  for (const id of connectorIds) {
    const connector = connectors.get(id);
    if (connector && adjacency.has(connector.from) && adjacency.has(connector.to)) {
      adjacency.get(connector.from).add(connector.to);
      adjacency.get(connector.to).add(connector.from);
    }
  }
  const start = placementRefs[0], visited = new Set(start ? [start] : []), queue = start ? [start] : [];
  while (queue.length) for (const next of adjacency.get(queue.shift()) || []) if (!visited.has(next)) { visited.add(next); queue.push(next); }
  return placementRefs.every(ref => visited.has(ref) && (placementRefs.length === 1 || adjacency.get(ref)?.size));
}

function sameArray(first, second) {
  return first.length === second.length && first.every((value, index) => value === second[index]);
}

function refRepresents(ref, factRef, groups) {
  if (ref === factRef) return true;
  return groups.get(ref)?.memberIds.includes(factRef) || false;
}

function relationshipMatchesConnector(relationship, connector, groups) {
  const forward = refRepresents(connector.from, relationship.from, groups) && refRepresents(connector.to, relationship.to, groups);
  const reverse = refRepresents(connector.from, relationship.to, groups) && refRepresents(connector.to, relationship.from, groups);
  return { forward, reverse };
}

function traceMainPath(view, path, connectorMap) {
  let current = path.startRef;
  const refs = [current];
  for (const connectorId of path.connectorIds) {
    const connector = connectorMap.get(connectorId);
    if (!connector) fail("MAIN_PATH", `${view.id}.${path.id} references unknown connector ${connectorId}`);
    let next = null;
    if ((connector.direction === "forward" || connector.direction === "bidirectional") && connector.from === current) next = connector.to;
    else if ((connector.direction === "reverse" || connector.direction === "bidirectional") && connector.to === current) next = connector.from;
    if (!next) fail("MAIN_PATH", `${view.id}.${path.id} cannot traverse ${connector.id} from ${current} in direction ${connector.direction}`);
    current = next;
    refs.push(current);
  }
  if (current !== path.endRef) fail("MAIN_PATH", `${view.id}.${path.id} ends at ${current}; expected ${path.endRef}`);
  return refs;
}

function validateConnector(connector, view, relationships, groups, placementRefs, field) {
  text(connector.id, `${field}.id`);
  if (!Array.isArray(connector.relationshipIds) || connector.relationshipIds.length === 0) fail("CONNECTOR_MAPPING", `${connector.id} requires relationshipIds`);
  text(connector.from, `${field}.from`);
  text(connector.to, `${field}.to`);
  if (!placementRefs.has(connector.from) || !placementRefs.has(connector.to)) fail("CONNECTOR_REFERENCE", `${connector.id} endpoints must be visible placements`);
  if (!DIRECTIONS.has(connector.direction)) fail("CONNECTOR_DIRECTION", `${connector.id} has unsupported direction ${connector.direction}`);
  if (!FACT_STATUSES.has(connector.status)) fail("CONNECTOR_STATUS", `${connector.id}.status must be current, planned, or shared`);
  if (!FLOW_PHASES.has(connector.flowPhase)) fail("CONNECTOR_PHASE", `${connector.id}.flowPhase is invalid`);
  if (!Array.isArray(connector.viaDevices)) fail("CONNECTOR_REFERENCE", `${connector.id}.viaDevices must be an array`);
  for (const device of connector.viaDevices) if (!placementRefs.has(device)) fail("CONNECTOR_REFERENCE", `${connector.id} via device ${device} is not visible in ${view.id}`);
  if (!connector.route || !ROUTES.has(connector.route.type) || !Array.isArray(connector.route.points)) fail("CONNECTOR_ROUTE", `${connector.id} requires a polyline or bezier route`);
  const requiredPoints = connector.route.type === "bezier" ? 4 : 2;
  if (connector.route.points.length < requiredPoints || (connector.route.type === "bezier" && connector.route.points.length !== 4)) fail("CONNECTOR_ROUTE", `${connector.id} has an invalid point count`);
  connector.route.points.forEach((point, index) => {
    number(point.x, `${connector.id}.route.points[${index}].x`);
    number(point.y, `${connector.id}.route.points[${index}].y`);
  });
  if (connector.label) {
    text(connector.label, `${connector.id}.label`);
    if (!connector.labelBox) fail("CONNECTOR_LABEL", `${connector.id} requires labelBox`);
    validateBox(connector.labelBox, `${connector.id}.labelBox`);
  }

  const mapped = connector.relationshipIds.map(id => {
    const relationship = relationships.get(id);
    if (!relationship) fail("CONNECTOR_MAPPING", `${connector.id} references unknown relationship ${id}`);
    return relationship;
  });
  if (mapped.length > 1 && view.kind !== "overview") fail("CONNECTOR_AGGREGATION", `${connector.id} aggregates relationships outside an overview`);
  if (mapped.length > 1 && connector.direction !== "bidirectional") fail("CONNECTOR_AGGREGATION", `${connector.id} aggregation must be bidirectional`);
  let hasForward = false;
  let hasReverse = false;
  for (const relationship of mapped) {
    const match = relationshipMatchesConnector(relationship, connector, groups);
    if (!match.forward && !match.reverse) fail("CONNECTOR_AGGREGATION", `${connector.id} combines relationships with incompatible endpoints`);
    hasForward ||= match.forward;
    hasReverse ||= match.reverse;
    if (!sameArray(relationship.viaDevices, connector.viaDevices)) fail("CONNECTOR_MAPPING", `${connector.id} viaDevices differ from ${relationship.id}`);
    if (relationship.status !== connector.status && relationship.status !== "shared") fail("CONNECTOR_STATUS", `${connector.id} status differs from ${relationship.id}`);
  }
  if (mapped.length > 1 && (!hasForward || !hasReverse)) fail("CONNECTOR_AGGREGATION", `${connector.id} aggregation must contain both endpoint directions`);
}

function validateModel(model) {
  if (model.schemaVersion !== 2) fail("MODEL_VERSION", "schemaVersion 2 is required; V1 models are not supported");
  for (const field of ["meta", "confirmation", "style", "acceptance"]) if (!model[field] || typeof model[field] !== "object") fail("MODEL_FIELD", `${field} is required`);
  for (const field of ["nodes", "devices", "groups", "relationships", "forbiddenRelationships", "views", "notes"]) if (!Array.isArray(model[field])) fail("MODEL_FIELD", `${field} must be an array`);
  text(model.meta.title, "meta.title");
  if (!DIAGRAM_TYPES.has(model.meta.diagramType)) fail("MODEL_TYPE", `unsupported diagramType ${model.meta.diagramType}`);
  for (const key of ["purpose", "audience", "useCase", "viewpoint"]) text(model.meta[key], `meta.${key}`);
  if (!["business-technical-closure", "implementation-overview"].includes(model.meta.overviewMode)) fail("MODEL_FIELD", "meta.overviewMode must be business-technical-closure or implementation-overview");
  for (const gate of ["positioning", "businessModel"]) {
    const confirmation = model.confirmation[gate];
    if (!confirmation || confirmation.confirmed !== true) fail("CONFIRMATION_REQUIRED", `${gate} confirmation is required before generation`);
    text(confirmation.basis, `confirmation.${gate}.basis`);
  }
  const blueprint = model.confirmation.businessModel.visualBlueprint;
  if (!blueprint || typeof blueprint !== "object") fail("CONFIRMATION_REQUIRED", "confirmation.businessModel.visualBlueprint is required; a boolean confirmation is insufficient");
  if (blueprint.overviewForm !== "structure-flow-overlay") fail("CONFIRMATION_REQUIRED", "visualBlueprint.overviewForm must be structure-flow-overlay");
  for (const field of ["firstRead", "readingDirection", "startRef", "currentPlannedPolicy", "asciiWireframe"]) text(blueprint[field], `visualBlueprint.${field}`);
  if (!["current-only", "planned-only", "comparison"].includes(blueprint.currentPlannedPolicy)) fail("CONFIRMATION_REQUIRED", "visualBlueprint.currentPlannedPolicy is invalid");
  textArray(blueprint.structureBoundaries, "visualBlueprint.structureBoundaries", 1);
  textArray(blueprint.outcomeRefs, "visualBlueprint.outcomeRefs", 1);
  textArray(blueprint.visualHierarchy, "visualBlueprint.visualHierarchy", 2);
  if (!Array.isArray(blueprint.branches)) fail("CONFIRMATION_REQUIRED", "visualBlueprint.branches must be an array");
  for (const branch of blueprint.branches) {
    for (const field of ["id", "decisionOwner", "condition", "selectionType", "splitRef", "mergeRef"]) text(branch[field], `visualBlueprint.branches.${field}`);
    if (!SELECTION_TYPES.has(branch.selectionType)) fail("CONFIRMATION_REQUIRED", `visualBlueprint branch ${branch.id} has invalid selectionType`);
    textArray(branch.pathIds, `visualBlueprint.branches.${branch.id}.pathIds`, 2);
    if (!branch.selectionEvidence || typeof branch.selectionEvidence !== "object") fail("CONFIRMATION_REQUIRED", `visualBlueprint branch ${branch.id} requires selectionEvidence`);
    text(branch.selectionEvidence.source, `visualBlueprint.branches.${branch.id}.selectionEvidence.source`);
    if (!SELECTION_TYPES.has(branch.selectionEvidence.observedType)) fail("CONFIRMATION_REQUIRED", `visualBlueprint branch ${branch.id} has invalid observed selection type`);
    if (!["none", "current", "planned", "comparison"].includes(branch.selectionEvidence.resolution)) fail("CONFIRMATION_REQUIRED", `visualBlueprint branch ${branch.id} has invalid selection conflict resolution`);
    const conflict = branch.selectionEvidence.observedType !== branch.selectionType;
    if (conflict && branch.selectionEvidence.resolution === "none") fail("CONFIRMATION_REQUIRED", `visualBlueprint branch ${branch.id} selectionType contradicts evidence without an explicit current/planned resolution`);
    if (!conflict && branch.selectionEvidence.resolution !== "none") fail("CONFIRMATION_REQUIRED", `visualBlueprint branch ${branch.id} declares a selection conflict that does not exist`);
  }
  if (!Array.isArray(blueprint.viewEstimates) || blueprint.viewEstimates.length === 0) fail("CONFIRMATION_REQUIRED", "visualBlueprint.viewEstimates must be non-empty");
  if (!['grayscale', 'grayscale-accent'].includes(model.style.mode)) fail("STYLE_MODE", "style.mode must be grayscale or grayscale-accent");
  if (model.style.mode === "grayscale" && model.style.accent !== null) fail("STYLE_ACCENT", "grayscale mode requires accent to be null");
  if (model.style.mode === "grayscale-accent") {
    if (!/^#[0-9a-f]{6}$/i.test(model.style.accent?.color || "")) fail("STYLE_ACCENT", "grayscale-accent requires one #rrggbb color");
    text(model.style.accent.meaning, "style.accent.meaning");
  }
  const typography = model.style.typography;
  for (const key of ["title", "purpose", "zoneTitle", "zoneSubtitle", "nodeTitle", "nodeSubtitle", "deviceLabel", "connectorLabel", "footer"]) positive(typography?.[key], `style.typography.${key}`);

  const globalIds = new Set();
  for (const [collection, items] of [["nodes", model.nodes], ["devices", model.devices], ["groups", model.groups], ["relationships", model.relationships]]) {
    for (const item of items) {
      text(item.id, `${collection}.id`);
      if (!/^[a-z0-9][a-z0-9-]*$/.test(item.id)) fail("MODEL_ID", `${item.id} must use lowercase letters, digits, and hyphens`);
      if (globalIds.has(item.id)) fail("DUPLICATE_ID", `duplicate model ID ${item.id}`);
      globalIds.add(item.id);
    }
  }
  for (const node of model.nodes) {
    text(node.label, `${node.id}.label`);
    text(node.role, `${node.id}.role`);
    if (!FACT_STATUSES.has(node.status)) fail("FACT_STATUS", `${node.id}.status is invalid`);
    if (!VISUAL_TYPES.has(node.visualType)) fail("VISUAL_TYPE", `${node.id}.visualType is invalid`);
  }
  for (const device of model.devices) {
    text(device.label, `${device.id}.label`);
    text(device.deviceType, `${device.id}.deviceType`);
    if (!FACT_STATUSES.has(device.status)) fail("FACT_STATUS", `${device.id}.status is invalid`);
    if (device.visualType !== "physical-media") fail("VISUAL_TYPE", `${device.id}.visualType must be physical-media`);
  }
  const entityIds = new Set([...model.nodes, ...model.devices].map(item => item.id));
  const deviceIds = new Set(model.devices.map(item => item.id));
  const groups = new Map(model.groups.map(group => [group.id, group]));
  for (const group of model.groups) {
    text(group.label, `${group.id}.label`);
    if (!FACT_STATUSES.has(group.status)) fail("FACT_STATUS", `${group.id}.status is invalid`);
    if (!Array.isArray(group.memberIds) || group.memberIds.length === 0) fail("GROUP_MEMBERS", `${group.id} requires memberIds`);
    for (const member of group.memberIds) if (!entityIds.has(member)) fail("GROUP_MEMBERS", `${group.id} references unknown member ${member}`);
  }
  const relationshipMap = new Map(model.relationships.map(item => [item.id, item]));
  for (const relationship of model.relationships) {
    for (const key of ["from", "to", "initiator", "method", "direction"]) text(relationship[key], `${relationship.id}.${key}`);
    if (!entityIds.has(relationship.from) || !entityIds.has(relationship.to) || !entityIds.has(relationship.initiator)) fail("RELATIONSHIP_REFERENCE", `${relationship.id} has an unknown endpoint or initiator`);
    if (!Array.isArray(relationship.viaDevices)) fail("RELATIONSHIP_REFERENCE", `${relationship.id}.viaDevices must be an array`);
    for (const device of relationship.viaDevices) if (!deviceIds.has(device)) fail("RELATIONSHIP_REFERENCE", `${relationship.id} references unknown device ${device}`);
    if (!["main", "supporting"].includes(relationship.narrativeRole)) fail("RELATIONSHIP_NARRATIVE", `${relationship.id}.narrativeRole must be main or supporting`);
    if (!FACT_STATUSES.has(relationship.status)) fail("FACT_STATUS", `${relationship.id}.status is invalid`);
    if (relationship.documentationOnly === true) text(relationship.documentationReason, `${relationship.id}.documentationReason`);
    if (relationship.documentationOnly === true && relationship.narrativeRole === "main") fail("RELATIONSHIP_NARRATIVE", `${relationship.id} is a main narrative relationship and cannot be documentationOnly`);
  }
  for (const rule of model.forbiddenRelationships) {
    text(rule.from, "forbiddenRelationships.from");
    text(rule.to, "forbiddenRelationships.to");
    if (model.relationships.some(item => item.from === rule.from && item.to === rule.to)) fail("FORBIDDEN_RELATIONSHIP", `${rule.from} -> ${rule.to} is forbidden`);
  }

  if (model.views.filter(view => view.kind === "overview").length !== 1) fail("VIEW_OVERVIEW", "exactly one overview view is required");
  if (model.views.length > 3) fail("VIEW_COUNT", "a model may contain one overview and at most two detail views");
  const viewIds = new Set();
  const coveredRelationships = new Set();
  const mainPathRelationships = new Set();
  let emphasized = 0;
  for (const [viewIndex, view] of model.views.entries()) {
    text(view.id, `views[${viewIndex}].id`);
    if (!/^[a-z0-9][a-z0-9-]*$/.test(view.id) || viewIds.has(view.id)) fail("VIEW_ID", `view ID ${view.id} is invalid or duplicated`);
    viewIds.add(view.id);
    if (!VIEW_KINDS.has(view.kind)) fail("VIEW_KIND", `${view.id} has unsupported kind ${view.kind}`);
    if (!AUDIENCE_LEVELS.has(view.audienceLevel)) fail("VIEW_AUDIENCE", `${view.id}.audienceLevel must be business-technical or implementation`);
    if (!view.narrative || typeof view.narrative !== "object") fail("VIEW_NARRATIVE", `${view.id}.narrative is required`);
    text(view.narrative.question, `${view.id}.narrative.question`);
    text(view.narrative.audience, `${view.id}.narrative.audience`);
    for (const key of ["title", "purpose"]) text(view[key], `${view.id}.${key}`);
    positive(view.canvas?.width, `${view.id}.canvas.width`);
    positive(view.canvas?.height, `${view.id}.canvas.height`);
    for (const key of ["width", "height"]) positive(view.reviewViewport?.[key], `${view.id}.reviewViewport.${key}`);
    for (const key of ["toolbarHeight", "statusHeight", "padding"]) nonNegative(view.reviewViewport?.[key], `${view.id}.reviewViewport.${key}`);
    if (!AXES.has(view.layout?.primaryAxis)) fail("VIEW_LAYOUT", `${view.id} requires a supported primaryAxis`);
    if (!LAYOUT_PATTERNS.has(view.layout?.pattern)) fail("VIEW_LAYOUT", `${view.id}.layout.pattern is invalid`);
    for (const field of ["zones", "stageGuides", "placements", "connectors", "mainPaths", "allowedCrossings", "mainFlow"]) if (!Array.isArray(view[field])) fail("VIEW_FIELD", `${view.id}.${field} must be an array`);
    if (view.kind === "overview" && model.meta.diagramType === "single-feature-technical" && view.layout.pattern !== "structure-flow-overlay") fail("VIEW_LAYOUT", `${view.id} single-feature technical overview must use structure-flow-overlay`);
    if (view.layout.pattern === "stage-columns" && view.zones.length) fail("VIEW_LAYOUT", `${view.id} stage-columns must use stageGuides; conceptual stages cannot be rendered as zones`);
    if (view.kind === "overview" && view.mainPaths.length === 0) fail("MAIN_PATH", `${view.id} overview requires at least one mainPath`);
    if (view.kind === "overview" && model.meta.overviewMode === "business-technical-closure" && view.audienceLevel !== "business-technical") fail("VIEW_AUDIENCE", `${view.id} must use business-technical audienceLevel for a business-technical closure overview`);

    const localIds = new Set();
    for (const zone of view.zones) {
      text(zone.id, `${view.id}.zones.id`);
      if (localIds.has(zone.id)) fail("DUPLICATE_ID", `${view.id} duplicates local ID ${zone.id}`);
      localIds.add(zone.id);
      text(zone.label, `${zone.id}.label`);
      if (!BOUNDARY_TYPES.has(zone.boundaryType)) fail("ZONE_TYPE", `${zone.id}.boundaryType is invalid`);
      if (!FACT_STATUSES.has(zone.status)) fail("FACT_STATUS", `${zone.id}.status is invalid`);
      textArray(zone.memberRefs, `${zone.id}.memberRefs`, 1);
      validateBox(zone, `${view.id}.${zone.id}`);
      emphasized += zone.emphasis === true ? 1 : 0;
    }
    for (const guide of view.stageGuides) {
      text(guide.id, `${view.id}.stageGuides.id`);
      text(guide.label, `${view.id}.${guide.id}.label`);
      nonNegative(guide.x, `${view.id}.${guide.id}.x`);
      positive(guide.width, `${view.id}.${guide.id}.width`);
    }
    const placementRefs = new Set();
    const renderedTypes = new Set();
    const factTypes = new Set();
    for (const placement of view.placements) {
      text(placement.ref, `${view.id}.placements.ref`);
      if (!entityIds.has(placement.ref) && !groups.has(placement.ref)) fail("PLACEMENT_REFERENCE", `${view.id} references unknown placement ${placement.ref}`);
      if (placementRefs.has(placement.ref)) fail("PLACEMENT_REFERENCE", `${view.id} duplicates placement ${placement.ref}`);
      placementRefs.add(placement.ref);
      validateBox(placement, `${view.id}.${placement.ref}`);
      if (!DISPLAY_LEVELS.has(placement.displayLevel)) fail("PLACEMENT_DISPLAY", `${view.id}.${placement.ref}.displayLevel must be business, implementation, or boundary`);
      if (placement.displayLabel !== undefined) text(placement.displayLabel, `${view.id}.${placement.ref}.displayLabel`);
      if (placement.displaySubtitle !== undefined && typeof placement.displaySubtitle !== "string") fail("PLACEMENT_DISPLAY", `${view.id}.${placement.ref}.displaySubtitle must be text`);
      if (view.kind === "overview" && model.meta.overviewMode === "business-technical-closure" && placement.displayLevel === "implementation") fail("PLACEMENT_DISPLAY", `${view.id}.${placement.ref} uses an implementation-level label in a business-technical overview`);
      if (deviceIds.has(placement.ref)) {
        if (!placement.labelBox) fail("DEVICE_LABEL", `${view.id}.${placement.ref} requires labelBox`);
        validateBox(placement.labelBox, `${view.id}.${placement.ref}.labelBox`);
      }
      const fact = model.nodes.find(item => item.id === placement.ref) || model.devices.find(item => item.id === placement.ref);
      if (fact) {
        factTypes.add(fact.visualType);
        const renderAs = placement.renderAs || fact.visualType;
        if (!VISUAL_TYPES.has(renderAs)) fail("VISUAL_TYPE", `${view.id}.${placement.ref}.renderAs is invalid`);
        renderedTypes.add(renderAs);
      }
      if (placement.contextOnly === true) text(placement.contextReason, `${view.id}.${placement.ref}.contextReason`);
      emphasized += placement.emphasis === true ? 1 : 0;
    }
    for (const zone of view.zones) for (const ref of zone.memberRefs) if (!placementRefs.has(ref)) fail("ZONE_MEMBER", `${view.id}.${zone.id} references invisible member ${ref}`);
    if (factTypes.size >= 3 && renderedTypes.size < 3) fail("VISUAL_TYPE", `${view.id} collapses semantic roles into fewer than three rendered shapes`);
    const connectorIds = new Set();
    for (const connector of view.connectors) {
      if (connectorIds.has(connector.id)) fail("DUPLICATE_ID", `${view.id} duplicates connector ${connector.id}`);
      connectorIds.add(connector.id);
      validateConnector(connector, view, relationshipMap, groups, placementRefs, `${view.id}.${connector.id}`);
      connector.relationshipIds.forEach(id => coveredRelationships.add(id));
      emphasized += connector.emphasis === true ? 1 : 0;
    }
    const connectedRefs = new Set();
    for (const connector of view.connectors) {
      connectedRefs.add(connector.from);
      connectedRefs.add(connector.to);
      connector.viaDevices.forEach(id => connectedRefs.add(id));
    }
    for (const placement of view.placements) if (!connectedRefs.has(placement.ref) && placement.contextOnly !== true) fail("PLACEMENT_ORPHAN", `${view.id}.${placement.ref} is an orphaned placement`);
    const visibleStatuses = new Set([...view.placements.map(placement => (model.nodes.find(item => item.id === placement.ref) || model.devices.find(item => item.id === placement.ref) || groups.get(placement.ref)).status), ...view.connectors.map(item => item.status)]);
    if (visibleStatuses.has("current") && visibleStatuses.has("planned")) {
      if (view.statusLegend?.visible !== true) fail("STATUS_LEGEND", `${view.id} mixes current and planned facts without a visible statusLegend`);
      validateBox(view.statusLegend, `${view.id}.statusLegend`);
      text(view.statusLegend.currentLabel, `${view.id}.statusLegend.currentLabel`);
      text(view.statusLegend.plannedLabel, `${view.id}.statusLegend.plannedLabel`);
    }
    const connectorMap = new Map(view.connectors.map(item => [item.id, item]));
    const pathIds = new Set();
    const tracedPaths = new Map();
    const pathConnectorIds = new Set();
    for (const path of view.mainPaths) {
      text(path.id, `${view.id}.mainPaths.id`);
      text(path.label, `${view.id}.${path.id}.label`);
      if (pathIds.has(path.id)) fail("MAIN_PATH", `${view.id} duplicates mainPath ${path.id}`);
      pathIds.add(path.id);
      text(path.startRef, `${view.id}.${path.id}.startRef`);
      text(path.endRef, `${view.id}.${path.id}.endRef`);
      if (!FACT_STATUSES.has(path.status)) fail("MAIN_PATH", `${view.id}.${path.id}.status is invalid`);
      if (!placementRefs.has(path.startRef) || !placementRefs.has(path.endRef)) fail("MAIN_PATH", `${view.id}.${path.id} startRef and endRef must be visible placements`);
      if (!Array.isArray(path.connectorIds) || path.connectorIds.length === 0) fail("MAIN_PATH", `${view.id}.${path.id} requires connectorIds`);
      if (new Set(path.connectorIds).size !== path.connectorIds.length) fail("MAIN_PATH", `${view.id}.${path.id} repeats a connector; main paths must be acyclic`);
      for (const connector of path.connectorIds) if (!connectorIds.has(connector)) fail("MAIN_PATH", `${view.id}.${path.id} references unknown connector ${connector}`);
      tracedPaths.set(path.id, traceMainPath(view, path, connectorMap));
      path.connectorIds.forEach(id => pathConnectorIds.add(id));
      for (const connectorId of path.connectorIds) connectorMap.get(connectorId).relationshipIds.forEach(id => mainPathRelationships.add(id));
    }
    text(view.narrative.startRef, `${view.id}.narrative.startRef`);
    if (!placementRefs.has(view.narrative.startRef)) fail("VIEW_NARRATIVE", `${view.id}.narrative.startRef must be a visible placement`);
    if (!Array.isArray(view.narrative.endRefs) || view.narrative.endRefs.length === 0) fail("VIEW_NARRATIVE", `${view.id}.narrative.endRefs must be non-empty`);
    for (const ref of view.narrative.endRefs) if (!placementRefs.has(ref)) fail("VIEW_NARRATIVE", `${view.id}.narrative.endRefs references invisible placement ${ref}`);
    for (const path of view.mainPaths) {
      if (path.startRef !== view.narrative.startRef) fail("VIEW_NARRATIVE", `${view.id}.${path.id} must start at narrative.startRef ${view.narrative.startRef}`);
      if (!view.narrative.endRefs.includes(path.endRef)) fail("VIEW_NARRATIVE", `${view.id}.${path.id} must end at one of narrative.endRefs`);
    }
    if (!Array.isArray(view.narrative.branchPoints)) fail("VIEW_NARRATIVE", `${view.id}.narrative.branchPoints must be an array`);
    for (const branch of view.narrative.branchPoints) {
      text(branch.id, `${view.id}.narrative.branchPoints.id`);
      for (const field of ["decisionOwner", "condition", "selectionType"]) text(branch[field], `${view.id}.${branch.id}.${field}`);
      const confirmed = blueprint.branches.find(item => item.id === branch.id);
      if (!confirmed) fail("VIEW_NARRATIVE", `${view.id}.${branch.id} is missing from the confirmed visual blueprint`);
      for (const field of ["decisionOwner", "condition", "selectionType", "splitRef", "mergeRef"]) if (branch[field] !== confirmed[field]) fail("VIEW_NARRATIVE", `${view.id}.${branch.id}.${field} differs from the confirmed visual blueprint`);
      if (!sameArray(branch.pathIds, confirmed.pathIds)) fail("VIEW_NARRATIVE", `${view.id}.${branch.id}.pathIds differ from the confirmed visual blueprint`);
      if (!placementRefs.has(branch.splitRef) || !placementRefs.has(branch.mergeRef)) fail("VIEW_NARRATIVE", `${view.id}.${branch.id} splitRef and mergeRef must be visible placements`);
      if (!Array.isArray(branch.pathIds) || branch.pathIds.length < 2) fail("VIEW_NARRATIVE", `${view.id}.${branch.id} requires at least two pathIds`);
      for (const pathId of branch.pathIds) {
        const refs = tracedPaths.get(pathId);
        if (!refs) fail("VIEW_NARRATIVE", `${view.id}.${branch.id} references unknown mainPath ${pathId}`);
        const splitIndex = refs.indexOf(branch.splitRef), mergeIndex = refs.indexOf(branch.mergeRef);
        if (splitIndex < 0 || mergeIndex <= splitIndex) fail("VIEW_NARRATIVE", `${view.id}.${branch.id} path ${pathId} does not traverse splitRef then mergeRef`);
        const path = view.mainPaths.find(item => item.id === pathId);
        const phases = new Set(path.connectorIds.map(id => connectorMap.get(id).flowPhase));
        if (view.layout.pattern === "structure-flow-overlay" && (!phases.has("outbound") || !phases.has("return") || !phases.has("outcome"))) fail("MAIN_PATH", `${view.id}.${branch.id} path ${pathId} is incomplete; each branch requires outbound, return, and outcome phases`);
      }
    }
    const flowIds = new Set();
    const flowConnectorIds = new Set();
    for (const flow of view.mainFlow) {
      text(flow.id, `${view.id}.mainFlow.id`);
      text(flow.text, `${view.id}.${flow.id}.text`);
      if (flowIds.has(flow.id)) fail("MAIN_FLOW", `${view.id} duplicates mainFlow ${flow.id}`);
      flowIds.add(flow.id);
      if (!Array.isArray(flow.placementRefs) || flow.placementRefs.length === 0) fail("MAIN_FLOW", `${view.id}.${flow.id}.placementRefs must be non-empty`);
      if (!Array.isArray(flow.connectorIds) || flow.connectorIds.length === 0) fail("MAIN_FLOW", `${view.id}.${flow.id}.connectorIds must be non-empty`);
      for (const ref of flow.placementRefs) if (!placementRefs.has(ref)) fail("MAIN_FLOW", `${view.id}.${flow.id} references invisible placement ${ref}`);
      for (const id of flow.connectorIds) {
        if (!pathConnectorIds.has(id)) fail("MAIN_FLOW", `${view.id}.${flow.id} connector ${id} is not part of a mainPath`);
        flowConnectorIds.add(id);
      }
      if (!connectedSubgraph(view, flow.connectorIds, flow.placementRefs)) fail("MAIN_FLOW", `${view.id}.${flow.id} placementRefs are not connected by its declared connectors`);
    }
    for (const id of pathConnectorIds) if (!flowConnectorIds.has(id)) fail("MAIN_FLOW", `${view.id}.${id} is a mainPath connector without a mainFlow mapping`);
    for (const crossing of view.allowedCrossings) {
      if (!Array.isArray(crossing.connectorIds) || crossing.connectorIds.length !== 2) fail("ALLOWED_CROSSING", `${view.id} allowed crossing requires two connectorIds`);
      for (const connector of crossing.connectorIds) if (!connectorIds.has(connector)) fail("ALLOWED_CROSSING", `${view.id} allowed crossing references unknown connector ${connector}`);
      number(crossing.point?.x, `${view.id}.allowedCrossings.point.x`);
      number(crossing.point?.y, `${view.id}.allowedCrossings.point.y`);
      text(crossing.reason, `${view.id}.allowedCrossings.reason`);
    }
  }
  const overview = model.views.find(view => view.kind === "overview");
  if (overview.narrative.startRef !== blueprint.startRef || !sameArray(overview.narrative.endRefs, blueprint.outcomeRefs)) fail("CONFIRMATION_REQUIRED", "overview start or outcomes differ from the confirmed visual blueprint");
  for (const ref of overview.narrative.endRefs) {
    const fact = model.nodes.find(item => item.id === ref);
    if (model.meta.overviewMode === "business-technical-closure" && fact?.visualType !== "outcome") fail("MAIN_PATH", `${overview.id}.${ref} is not an outcome node`);
  }
  const overviewZoneLabels = new Set(overview.zones.map(zone => zone.label));
  for (const boundary of blueprint.structureBoundaries) if (!overviewZoneLabels.has(boundary)) fail("CONFIRMATION_REQUIRED", `overview is missing confirmed structural boundary ${boundary}`);
  const estimates = new Map(blueprint.viewEstimates.map(item => [item.viewId, item]));
  for (const view of model.views) {
    const estimate = estimates.get(view.id);
    if (!estimate) fail("CONFIRMATION_REQUIRED", `visualBlueprint.viewEstimates is missing ${view.id}`);
    if (estimate.placements !== view.placements.length || estimate.connectors !== view.connectors.length) fail("CONFIRMATION_REQUIRED", `visualBlueprint estimate for ${view.id} differs from rendered counts`);
  }
  for (const relationship of model.relationships) {
    if (!coveredRelationships.has(relationship.id) && relationship.documentationOnly !== true) fail("RELATIONSHIP_COVERAGE", `${relationship.id} is not represented in any view`);
    if (relationship.narrativeRole === "main" && !mainPathRelationships.has(relationship.id)) fail("RELATIONSHIP_NARRATIVE", `${relationship.id} is a main narrative relationship not represented by any mainPath`);
  }
  if (model.style.mode === "grayscale" && emphasized > 0) fail("STYLE_EMPHASIS", "grayscale mode does not allow emphasized view elements");
  if (model.style.mode === "grayscale-accent" && emphasized === 0) fail("STYLE_EMPHASIS", "grayscale-accent mode requires at least one emphasized view element");
  if (!Array.isArray(model.acceptance.requiredText) || !Array.isArray(model.acceptance.forbiddenText)) fail("MODEL_FIELD", "acceptance text arrays are required");
}

function esc(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function attr(value) {
  return esc(value ?? "");
}

function routePath(route) {
  const points = route.points;
  if (route.type === "bezier") return `M${points[0].x} ${points[0].y}C${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y} ${points[3].x} ${points[3].y}`;
  return points.map((point, index) => `${index ? "L" : "M"}${point.x} ${point.y}`).join("");
}

function markerAttributes(direction, emphasized) {
  const suffix = emphasized ? "accent" : "gray";
  if (direction === "bidirectional") return `marker-start="url(#open-${suffix})" marker-end="url(#open-${suffix})"`;
  if (direction === "reverse") return `marker-start="url(#solid-${suffix})"`;
  if (direction === "none") return "";
  return `marker-end="url(#solid-${suffix})"`;
}

function facts(model) {
  return new Map([...model.nodes, ...model.devices, ...model.groups].map(item => [item.id, item]));
}

function displayText(fact, placement) {
  return {
    label: placement.displayLabel || fact.label,
    subtitle: placement.displaySubtitle ?? fact.subtitle ?? "",
  };
}

function mainFlowHeight(view) {
  return 72 + Math.max(1, view.mainFlow.length) * 28;
}

function zoneSvg(view, zone) {
  return `<g id="${attr(view.id)}-zone-${attr(zone.id)}" data-role="zone" data-view="${attr(view.id)}" data-ref="${attr(zone.id)}" data-boundary-type="${attr(zone.boundaryType)}" data-status="${attr(zone.status)}" data-members="${attr(zone.memberRefs.join(","))}" class="status-${attr(zone.status)}"><rect x="${zone.x}" y="${zone.y}" width="${zone.width}" height="${zone.height}" class="zone-box"/><text x="${zone.x + 20}" y="${zone.y + 32}" class="zone-title">${esc(zone.label)}</text>${zone.subtitle ? `<text x="${zone.x + 20}" y="${zone.y + 57}" class="zone-subtitle">${esc(zone.subtitle)}</text>` : ""}</g>`;
}

function stageGuideSvg(view, guide, index) {
  const separator = index ? `<line x1="${guide.x}" y1="120" x2="${guide.x}" y2="${view.canvas.height - mainFlowHeight(view) - 24}" class="stage-separator"/>` : "";
  return `<g id="${attr(view.id)}-stage-${attr(guide.id)}" data-role="stage-guide" data-view="${attr(view.id)}" data-ref="${attr(guide.id)}">${separator}<text x="${guide.x + 12}" y="142" class="stage-title">${esc(guide.label)}</text>${guide.subtitle ? `<text x="${guide.x + 12}" y="166" class="stage-subtitle">${esc(guide.subtitle)}</text>` : ""}</g>`;
}

function semanticShape(visualType, placement) {
  const { x, y, width, height } = placement;
  const cx = x + width / 2, cy = y + height / 2;
  if (visualType === "actor") return `<rect x="${x}" y="${y}" width="${width}" height="${height}" class="semantic-hit"/><circle cx="${x + 34}" cy="${cy - 14}" r="12" class="actor-shape"/><path d="M${x + 14} ${cy + 24}Q${x + 34} ${cy - 2} ${x + 54} ${cy + 24}" class="actor-shape"/>`;
  if (visualType === "application") return `<rect x="${x}" y="${y}" width="${width}" height="${height}" class="application-box"/><line x1="${x}" y1="${y + 26}" x2="${x + width}" y2="${y + 26}" class="application-detail"/>`;
  if (visualType === "storage") return `<path d="M${x} ${y + 16}C${x} ${y - 2} ${x + width} ${y - 2} ${x + width} ${y + 16}V${y + height - 16}C${x + width} ${y + height + 2} ${x} ${y + height + 2} ${x} ${y + height - 16}ZM${x} ${y + 16}C${x} ${y + 34} ${x + width} ${y + 34} ${x + width} ${y + 16}" class="storage-box"/>`;
  if (visualType === "physical-media") return `<path d="M${x + 12} ${y}H${x + width - 12}V${y + 20}H${x + width}V${y + height - 20}H${x + width - 12}V${y + height}H${x + 12}Z" class="media-box"/><line x1="${x + width - 12}" y1="${cy - 8}" x2="${x + width}" y2="${cy - 8}" class="media-detail"/><line x1="${x + width - 12}" y1="${cy + 8}" x2="${x + width}" y2="${cy + 8}" class="media-detail"/>`;
  if (visualType === "external-system") return `<rect x="${x}" y="${y}" width="${width}" height="${height}" class="external-box"/><rect x="${x + 7}" y="${y + 7}" width="${width - 14}" height="${height - 14}" class="external-inner"/>`;
  if (visualType === "outcome") return `<rect x="${x}" y="${y}" width="${width}" height="${height}" class="outcome-box"/><rect x="${x}" y="${y}" width="10" height="${height}" class="outcome-bar"/>`;
  return `<rect x="${x}" y="${y}" width="${width}" height="${height}" class="service-box"/>`;
}

function placementSvg(model, view, placement, factMap) {
  const fact = factMap.get(placement.ref);
  const display = displayText(fact, placement);
  const isDevice = model.devices.some(item => item.id === placement.ref);
  const isGroup = model.groups.some(item => item.id === placement.ref);
  const role = isDevice ? "device" : isGroup ? "group" : "node";
  const centerX = placement.x + placement.width / 2;
  const emphasized = Boolean(placement.emphasis);
  const visualType = placement.renderAs || fact.visualType || "service";
  if (isDevice) {
    const centerY = placement.y + placement.height / 2, label = placement.labelBox;
    return `<g id="${attr(view.id)}-placement-${attr(placement.ref)}" data-role="device" data-view="${attr(view.id)}" data-ref="${attr(placement.ref)}" data-device-type="${attr(fact.deviceType)}" data-visual-type="${attr(visualType)}" data-status="${attr(fact.status)}" data-display-level="${attr(placement.displayLevel)}" data-context-only="${Boolean(placement.contextOnly)}" data-emphasis="${emphasized}" class="status-${attr(fact.status)} ${placement.contextOnly ? "context-only" : ""}"><rect x="${placement.x}" y="${placement.y}" width="${placement.width}" height="${placement.height}" class="service-box"/><path d="M${placement.x} ${centerY - 18}H${placement.x + placement.width}M${placement.x} ${centerY + 18}H${placement.x + placement.width}M${centerX - 16} ${placement.y}V${centerY - 18}M${centerX + 16} ${centerY - 18}V${centerY + 18}M${centerX - 16} ${centerY + 18}V${placement.y + placement.height}" class="application-detail"/><g id="${attr(view.id)}-label-${attr(placement.ref)}" data-role="device-label" data-view="${attr(view.id)}" data-owner="${attr(placement.ref)}"><text x="${label.x + label.width / 2}" y="${label.y + label.height / 2 + 6}" text-anchor="middle" class="device-label">${esc(display.label)}</text></g></g>`;
  }
  const hasSubtitle = Boolean(display.subtitle);
  const actorOffset = visualType === "actor" ? 24 : 0;
  const labelX = centerX + actorOffset;
  const labelY = placement.y + placement.height / 2 + (hasSubtitle ? -4 : 8);
  const shape = isGroup ? `<rect x="${placement.x}" y="${placement.y}" width="${placement.width}" height="${placement.height}" class="group-box"/>` : semanticShape(visualType, placement);
  return `<g id="${attr(view.id)}-placement-${attr(placement.ref)}" data-role="${role}" data-view="${attr(view.id)}" data-ref="${attr(placement.ref)}" data-node-role="${attr(fact.role || "group")}" data-visual-type="${attr(visualType)}" data-status="${attr(fact.status)}" data-display-level="${attr(placement.displayLevel)}" data-context-only="${Boolean(placement.contextOnly)}" data-emphasis="${emphasized}" class="status-${attr(fact.status)} ${placement.contextOnly ? "context-only" : ""} ${emphasized ? "emphasis" : ""}">${shape}<text x="${labelX}" y="${labelY}" text-anchor="middle" class="node-title">${esc(display.label)}</text>${hasSubtitle ? `<text x="${labelX}" y="${labelY + 28}" text-anchor="middle" class="node-subtitle">${esc(display.subtitle)}</text>` : ""}</g>`;
}

function connectorSvg(view, connector, mainIds) {
  const emphasized = Boolean(connector.emphasis);
  const isMain = mainIds.has(connector.id);
  const label = connector.label ? `<g id="${attr(view.id)}-label-${attr(connector.id)}" data-role="connector-label" data-view="${attr(view.id)}" data-owner="${attr(connector.id)}"><rect x="${connector.labelBox.x}" y="${connector.labelBox.y}" width="${connector.labelBox.width}" height="${connector.labelBox.height}" class="label-box"/><text x="${connector.labelBox.x + connector.labelBox.width / 2}" y="${connector.labelBox.y + connector.labelBox.height / 2 + 6}" text-anchor="middle" class="connector-label">${esc(connector.label)}</text></g>` : "";
  return `<g id="${attr(view.id)}-connector-${attr(connector.id)}" data-role="connector" data-view="${attr(view.id)}" data-ref="${attr(connector.id)}" data-relationships="${attr(connector.relationshipIds.join(","))}" data-from="${attr(connector.from)}" data-to="${attr(connector.to)}" data-direction="${attr(connector.direction)}" data-via-devices="${attr(connector.viaDevices.join(","))}" data-status="${attr(connector.status)}" data-flow-phase="${attr(connector.flowPhase)}" data-main-path="${isMain}" data-emphasis="${emphasized}"><path d="${routePath(connector.route)}" class="connector-line ${isMain ? "connector-main" : "connector-supporting"} status-${attr(connector.status)} phase-${attr(connector.flowPhase)} ${emphasized ? "connector-accent" : ""}" ${markerAttributes(connector.direction, emphasized)}/>${label}</g>`;
}

function statusLegendSvg(view) {
  const legend = view.statusLegend;
  if (!legend?.visible) return "";
  const lineX = legend.x + 18, textX = legend.x + 88;
  return `<g id="${attr(view.id)}-status-legend" data-role="status-legend" data-view="${attr(view.id)}"><rect x="${legend.x}" y="${legend.y}" width="${legend.width}" height="${legend.height}" class="legend-box"/><line x1="${lineX}" y1="${legend.y + 26}" x2="${lineX + 52}" y2="${legend.y + 26}" class="legend-current"/><text x="${textX}" y="${legend.y + 32}" class="legend-text">${esc(legend.currentLabel)}</text><line x1="${lineX}" y1="${legend.y + 58}" x2="${lineX + 52}" y2="${legend.y + 58}" class="legend-planned"/><text x="${textX}" y="${legend.y + 64}" class="legend-text">${esc(legend.plannedLabel)}</text></g>`;
}

function svg(model, view) {
  const { width, height } = view.canvas;
  const type = model.style.typography;
  const accent = model.style.accent?.color || "#000000";
  const flowStart = height - mainFlowHeight(view);
  const factMap = facts(model);
  const mainIds = new Set(view.mainPaths.flatMap(path => path.connectorIds));
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" data-view="${attr(view.id)}" role="img" aria-labelledby="diagram-title diagram-description">
  <title id="diagram-title">${esc(view.title)}</title>
  <desc id="diagram-description">${esc(view.purpose)}</desc>
  <defs>
    <marker id="solid-gray" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto"><path d="M1 1L11 6L1 11Z" fill="#333333"/></marker>
    <marker id="open-gray" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1 1L11 6L1 11Z" fill="#ffffff" stroke="#666666" stroke-width="1.5"/></marker>
    <marker id="solid-accent" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto"><path d="M1 1L11 6L1 11Z" fill="${accent}"/></marker>
    <marker id="open-accent" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1 1L11 6L1 11Z" fill="#ffffff" stroke="${accent}" stroke-width="1.5"/></marker>
    <style>*{box-sizing:border-box;letter-spacing:0}text{font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;fill:#111111}.canvas-title{font-size:${type.title}px;font-weight:700}.canvas-purpose{font-size:${type.purpose}px;fill:#222222}.zone-box{fill:#fafafa;stroke:#777777;stroke-width:1.5}.zone-title,.stage-title{font-size:${type.zoneTitle}px;font-weight:700}.zone-subtitle,.stage-subtitle{font-size:${type.zoneSubtitle}px;fill:#333333}.stage-separator{stroke:#cccccc;stroke-width:1}.service-box,.application-box,.storage-box,.media-box,.external-box,.external-inner,.outcome-box,.actor-shape{fill:#ffffff;stroke:#333333;stroke-width:2}.application-box{stroke-width:3}.application-detail,.media-detail{stroke:#555555;stroke-width:1.5}.storage-box{fill:#fafafa}.external-inner{fill:none;stroke-width:1}.outcome-box{stroke-width:3}.outcome-bar{fill:#333333}.actor-shape{fill:none;stroke-width:2.5}.semantic-hit{fill:#ffffff;stroke:none}.group-box{fill:#f7f7f7;stroke:#555555;stroke-width:2}.node-title{font-size:${type.nodeTitle}px;font-weight:700}.node-subtitle{font-size:${type.nodeSubtitle}px;fill:#222222}.connector-line{fill:none}.connector-main{stroke:#222222;stroke-width:4}.connector-supporting{stroke:#777777;stroke-width:2}.connector-line.status-planned{stroke:#666666;stroke-dasharray:10 7}.status-planned .service-box,.status-planned .application-box,.status-planned .storage-box,.status-planned .media-box,.status-planned .external-box,.status-planned .external-inner,.status-planned .outcome-box,.status-planned .actor-shape,.status-planned .zone-box{stroke:#666666;stroke-dasharray:8 6}.connector-line.phase-return{stroke-width:3.5}.connector-line.phase-supporting{stroke-width:2}.connector-accent{stroke:${accent}}.label-box{fill:#ffffff;stroke:#999999;stroke-width:1}.connector-label{font-size:${type.connectorLabel}px;font-weight:700}.context-only{opacity:.55}.legend-box{fill:#ffffff;stroke:#999999;stroke-width:1}.legend-current{stroke:#222222;stroke-width:4}.legend-planned{stroke:#666666;stroke-width:3;stroke-dasharray:10 7}.legend-text{font-size:${type.connectorLabel}px}.footer-rule{stroke:#bbbbbb;stroke-width:1}.footer-title{font-size:${type.footer + 2}px;font-weight:700}.footer-text{font-size:${type.footer}px}</style>
  </defs>
  <rect width="${width}" height="${height}" fill="#ffffff"/>
  <text x="60" y="58" class="canvas-title">${esc(view.title)}</text>
  <text x="60" y="88" class="canvas-purpose">${esc(view.purpose)}</text>
  ${view.zones.map(zone => zoneSvg(view, zone)).join("\n  ")}
  ${view.stageGuides.map((guide, index) => stageGuideSvg(view, guide, index)).join("\n  ")}
  ${view.connectors.map(connector => connectorSvg(view, connector, mainIds)).join("\n  ")}
  ${view.placements.map(placement => placementSvg(model, view, placement, factMap)).join("\n  ")}
  ${statusLegendSvg(view)}
  <line x1="60" y1="${flowStart}" x2="${width - 60}" y2="${flowStart}" class="footer-rule"/>
  <text x="60" y="${flowStart + 34}" class="footer-title">业务主线</text>
  ${view.mainFlow.map((item, index) => `<text x="190" y="${flowStart + 34 + index * 28}" class="footer-text" data-role="main-flow" data-ref="${attr(item.id)}">${index + 1}. ${esc(item.text)}</text>`).join("\n  ")}
</svg>`;
}

function markdown(model) {
  const factsRows = [...model.nodes.map(item => [item.id, item.label, item.role, item.visualType, item.status]), ...model.devices.map(item => [item.id, item.label, item.deviceType, item.visualType, item.status]), ...model.groups.map(item => [item.id, item.label, `group: ${item.memberIds.join(", ")}`, "container", item.status])].map(row => `| ${row.join(" | ")} |`).join("\n");
  const relationshipRows = model.relationships.map(item => `| ${item.id} | ${item.from} | ${item.to} | ${item.initiator} | ${item.method} | ${item.direction} | ${item.status} | ${item.narrativeRole} | ${item.viaDevices.join(", ") || "none"} |`).join("\n");
  const viewSections = model.views.map(view => {
    const connectors = view.connectors.map(item => `| ${item.id} | ${item.from} | ${item.to} | ${item.direction} | ${item.status} | ${item.flowPhase} | ${item.relationshipIds.join(", ")} |`).join("\n");
    return `### ${view.title}\n\n- View ID: \`${view.id}\`\n- Kind: \`${view.kind}\`\n- Audience level: \`${view.audienceLevel}\`\n- Question: ${view.narrative.question}\n- Layout: \`${view.layout.pattern}\`, \`${view.layout.primaryAxis}\`\n- Canvas: \`${view.canvas.width} x ${view.canvas.height}\`\n- Visible elements/connectors: ${view.placements.length}/${view.connectors.length}\n\n| Connector | From | To | Direction | Status | Phase | Relationship facts |\n| --- | --- | --- | --- | --- | --- | --- |\n${connectors}\n\n业务主线:\n${view.mainFlow.map((item, index) => `${index + 1}. ${item.text} [placements: ${item.placementRefs.join(", ")}; connectors: ${item.connectorIds.join(", ")}]`).join("\n")}`;
  }).join("\n\n");
  const forbidden = model.forbiddenRelationships.length ? model.forbiddenRelationships.map(item => `- \`${item.from} -> ${item.to}\`: ${item.reason}`).join("\n") : "- None.";
  return `# ${model.meta.title}\n\n${model.meta.purpose}\n\n## Confirmed positioning\n\n- Diagram type: \`${model.meta.diagramType}\`\n- Overview mode: \`${model.meta.overviewMode}\`\n- Audience: ${model.meta.audience}\n- Use case: ${model.meta.useCase}\n- Viewpoint: \`${model.meta.viewpoint}\`\n- Positioning basis: ${model.confirmation.positioning.basis}\n- Business-model and visual-blueprint basis: ${model.confirmation.businessModel.basis}\n- First read: ${model.confirmation.businessModel.visualBlueprint.firstRead}\n- Current/planned policy: \`${model.confirmation.businessModel.visualBlueprint.currentPlannedPolicy}\`\n\n## Fact model\n\n| ID | Label | Role/type or members | Visual type | Status |\n| --- | --- | --- | --- | --- |\n${factsRows}\n\n## Relationship facts\n\n| ID | From | To | Initiator | Method | Direction | Status | Narrative role | Required devices |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n${relationshipRows}\n\n## Views\n\n${viewSections}\n\n## Forbidden relationships\n\n${forbidden}\n\n## Evidence and boundaries\n\n- Evidence: ${model.meta.evidenceSources.join("; ")}\n- In scope: ${model.meta.scope.include.join("; ")}\n- Out of scope: ${model.meta.scope.exclude.join("; ")}\n\n## Notes\n\n${model.notes.map(item => `- ${item}`).join("\n")}\n`;
}

function preview(model, base) {
  const views = model.views.map(view => ({ id: view.id, title: view.title, file: `./${base}-${view.id}.svg`, width: view.canvas.width, height: view.canvas.height }));
  const encodedViews = JSON.stringify(views).replaceAll("<", "\\u003c");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:"><title>${esc(base)} preview</title><style>*{box-sizing:border-box;letter-spacing:0}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#eeeeee;color:#111111;font-family:Arial,sans-serif}#toolbar{height:54px;display:flex;align-items:center;gap:8px;padding:8px 12px;background:#ffffff;border-bottom:1px solid #aaaaaa}#tabs{display:flex;gap:6px;margin-right:auto}.tab.active{background:#333333;color:#ffffff;border-color:#333333}button{height:34px;padding:0 12px;border:1px solid #999999;border-radius:3px;background:#ffffff;color:#111111;cursor:pointer}button:hover{background:#eeeeee}.tab.active:hover{background:#333333}#stage{position:absolute;inset:54px 0 26px;overflow:hidden;cursor:grab;touch-action:none}#stage.dragging{cursor:grabbing}#viewport{position:absolute;left:0;top:0;transform-origin:0 0}#viewport svg{display:block}#status{position:absolute;left:0;right:0;bottom:0;height:26px;padding:5px 12px;background:#ffffff;border-top:1px solid #aaaaaa;font-size:12px}</style></head><body><div id="toolbar"><div id="tabs"></div><button id="zoom-out">-</button><button id="zoom-in">+</button><button id="fit">Fit</button><button id="export-svg">Export SVG</button><button id="export-png">Export PNG</button></div><main id="stage"><div id="viewport"></div></main><div id="status">Loading...</div><script>const views=${encodedViews},stage=document.querySelector("#stage"),viewport=document.querySelector("#viewport"),tabs=document.querySelector("#tabs"),status=document.querySelector("#status");let current=views[0],source="",scale=1,tx=0,ty=0,drag=false,lastX=0,lastY=0;function apply(){viewport.style.transform="translate("+tx+"px,"+ty+"px) scale("+scale+")";status.textContent=current.title+" · "+Math.round(scale*100)+"% · "+current.width+" x "+current.height}function fit(){const p=20;scale=Math.min((stage.clientWidth-p*2)/current.width,(stage.clientHeight-p*2)/current.height);tx=(stage.clientWidth-current.width*scale)/2;ty=(stage.clientHeight-current.height*scale)/2;apply()}function zoom(f,x=stage.clientWidth/2,y=stage.clientHeight/2){const next=Math.max(.1,Math.min(4,scale*f)),wx=(x-tx)/scale,wy=(y-ty)/scale;tx=x-wx*next;ty=y-wy*next;scale=next;apply()}function save(blob,name){const anchor=document.createElement("a");anchor.href=URL.createObjectURL(blob);anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(anchor.href),2000)}async function load(view){current=view;const response=await fetch(view.file);if(!response.ok)throw Error("SVG load failed: "+response.status);source=await response.text();viewport.innerHTML=source;viewport.style.width=view.width+"px";viewport.style.height=view.height+"px";document.querySelectorAll(".tab").forEach(button=>button.classList.toggle("active",button.dataset.view===view.id));fit()}for(const view of views){const button=document.createElement("button");button.className="tab";button.dataset.view=view.id;button.textContent=view.title;button.onclick=()=>load(view).catch(error=>{status.textContent=error.message;console.error(error)});tabs.appendChild(button)}document.querySelector("#zoom-out").onclick=()=>zoom(.8);document.querySelector("#zoom-in").onclick=()=>zoom(1.25);document.querySelector("#fit").onclick=fit;document.querySelector("#export-svg").onclick=()=>save(new Blob([source],{type:"image/svg+xml;charset=utf-8"}),"${esc(base)}-"+current.id+".svg");document.querySelector("#export-png").onclick=()=>{const url=URL.createObjectURL(new Blob([source],{type:"image/svg+xml;charset=utf-8"})),image=new Image();image.onload=()=>{const canvas=document.createElement("canvas");canvas.width=current.width;canvas.height=current.height;const context=canvas.getContext("2d");context.fillStyle="#ffffff";context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0);URL.revokeObjectURL(url);canvas.toBlob(blob=>blob&&save(blob,"${esc(base)}-"+current.id+".png"),"image/png")};image.src=url};stage.addEventListener("wheel",event=>{event.preventDefault();const rect=stage.getBoundingClientRect();zoom(event.deltaY<0?1.12:.89,event.clientX-rect.left,event.clientY-rect.top)},{passive:false});stage.addEventListener("pointerdown",event=>{drag=true;lastX=event.clientX;lastY=event.clientY;stage.classList.add("dragging");stage.setPointerCapture(event.pointerId)});stage.addEventListener("pointermove",event=>{if(!drag)return;tx+=event.clientX-lastX;ty+=event.clientY-lastY;lastX=event.clientX;lastY=event.clientY;apply()});stage.addEventListener("pointerup",event=>{drag=false;stage.classList.remove("dragging");stage.releasePointerCapture(event.pointerId)});window.addEventListener("resize",fit);load(current).catch(error=>{status.textContent=error.message;console.error(error)})</script></body></html>`;
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log("node engineering-topology-generator.mjs --model <json> --out-dir <dir> --base <name>");
    return;
  }
  if (!args.model) fail("ARGUMENT", "--model is required");
  const modelPath = resolve(args.model);
  const model = JSON.parse(await readFile(modelPath, "utf8"));
  validateModel(model);
  const base = args.base || basename(modelPath, ".json").replace(/-model$/, "") || "engineering-topology";
  const outDir = resolve(args.outDir);
  await mkdir(outDir, { recursive: true });
  const outputs = [
    writeFile(join(outDir, `${base}.md`), markdown(model), "utf8"),
    writeFile(join(outDir, `${base}-preview.html`), preview(model, base), "utf8"),
    ...model.views.map(view => writeFile(join(outDir, `${base}-${view.id}.svg`), svg(model, view), "utf8")),
  ];
  await Promise.all(outputs);
  console.log(`Generated Markdown, tabbed preview, and ${model.views.length} SVG view(s) from ${modelPath}`);
}

main().catch(error => {
  console.error(error.message || error);
  process.exit(1);
});
