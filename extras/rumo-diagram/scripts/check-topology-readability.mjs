#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { artifactPaths, connectorCrossingIssues, entityMaps, fitScale, mainConnectorIds, readModel, routePoints, routeSegments, selectedViews, traceMainPath } from "./topology-v2-lib.mjs";

const OVERVIEW_ELEMENT_LIMIT = 18;
const OVERVIEW_CONNECTOR_LIMIT = 18;
const OVERVIEW_DEGREE_LIMIT = 6;
const OVERVIEW_BEND_LIMIT = 4;
const OVERVIEW_DETOUR_LIMIT = 2.5;
const MAIN_TEXT_MIN = 12;
const SECONDARY_TEXT_MIN = 10;
const OVERVIEW_CONTENT_UTILIZATION_MIN = 0.55;
const DETAIL_CONTENT_UTILIZATION_MIN = 0.42;
const CONTAINER_OCCUPANCY_MIN = 0.35;

function parseArgs(argv) {
  const args = { model: "", outDir: "", base: "", view: "" };
  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--help" || value === "-h") args.help = true;
    else if (["--model", "--out-dir", "--base", "--view"].includes(value) && argv[index + 1]) args[value.slice(2).replace(/-([a-z])/g, (_, character) => character.toUpperCase())] = argv[++index];
    else throw new Error(`Unknown or incomplete argument: ${value}`);
  }
  return args;
}

function segmentDirection(first, second) {
  const dx = second.x - first.x, dy = second.y - first.y;
  if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) return "none";
  if (Math.abs(dx) < 0.5) return "vertical";
  if (Math.abs(dy) < 0.5) return "horizontal";
  return "diagonal";
}

function bendCount(connector) {
  if (connector.route.type === "bezier") return 0;
  const directions = [];
  for (let index = 1; index < connector.route.points.length; index += 1) {
    const direction = segmentDirection(connector.route.points[index - 1], connector.route.points[index]);
    if (direction !== "none" && direction !== directions.at(-1)) directions.push(direction);
  }
  return Math.max(0, directions.length - 1);
}

function length(points) {
  let total = 0;
  for (let index = 1; index < points.length; index += 1) total += Math.hypot(points[index].x - points[index - 1].x, points[index].y - points[index - 1].y);
  return total;
}

function detourRatio(connector) {
  const points = routePoints(connector), first = points[0], last = points.at(-1);
  const minimum = Math.abs(last.x - first.x) + Math.abs(last.y - first.y);
  return minimum < 1 ? 1 : length(points) / minimum;
}

function hugsBoundary(view, connector) {
  const margin = 24;
  const threshold = Math.max(160, Math.min(view.canvas.width, view.canvas.height) * 0.25);
  return routeSegments(connector).some(segment => {
    const segmentLength = Math.hypot(segment.b.x - segment.a.x, segment.b.y - segment.a.y);
    if (segmentLength < threshold) return false;
    const nearLeft = segment.a.x <= margin && segment.b.x <= margin;
    const nearRight = segment.a.x >= view.canvas.width - margin && segment.b.x >= view.canvas.width - margin;
    const nearTop = segment.a.y <= margin && segment.b.y <= margin;
    const nearBottom = segment.a.y >= view.canvas.height - margin && segment.b.y >= view.canvas.height - margin;
    return nearLeft || nearRight || nearTop || nearBottom;
  });
}

function orderedRoutePoints(connector, currentRef) {
  const points = routePoints(connector);
  return connector.from === currentRef ? points : [...points].reverse();
}

function validateMainPathLayout(view, path, errors) {
  const connectors = new Map(view.connectors.map(item => [item.id, item]));
  const refs = traceMainPath(view, path);
  let currentRef = path.startRef;
  for (const [index, connectorId] of path.connectorIds.entries()) {
    const connector = connectors.get(connectorId);
    const points = orderedRoutePoints(connector, currentRef);
    if (["stage-columns", "swimlanes"].includes(view.layout.pattern) && connector.route.type === "polyline") {
      for (let index = 1; index < points.length; index += 1) {
        if (segmentDirection(points[index - 1], points[index]) === "diagonal") errors.push(`${view.id}.${connector.id} uses a diagonal segment on a declared main path`);
      }
    }
    const axis = view.layout.primaryAxis === "left-to-right" ? "x" : "y";
    const direction = view.layout.pattern === "structure-flow-overlay" && ["return", "outcome"].includes(connector.flowPhase) ? -1 : 1;
    for (let index = 1; index < points.length; index += 1) {
      const movement = points[index][axis] - points[index - 1][axis];
      if (movement * direction < -1) errors.push(`${view.id}.${connector.id} backtracks against its ${connector.flowPhase} reading direction`);
    }
    currentRef = refs[index + 1];
  }
}

function contentUtilization(view) {
  const content = view.kind === "overview" ? [...view.placements, ...view.zones, ...(view.statusLegend?.visible ? [view.statusLegend] : [])] : view.placements;
  if (content.length === 0) return 0;
  const left = Math.min(...content.map(item => item.x));
  const top = Math.min(...content.map(item => item.y));
  const right = Math.max(...content.map(item => item.x + item.width));
  const bottom = Math.max(...content.map(item => item.y + item.height));
  const footerHeight = 72 + Math.max(1, view.mainFlow.length) * 28;
  const usableWidth = Math.max(1, view.canvas.width - 80);
  const usableHeight = Math.max(1, view.canvas.height - 100 - footerHeight);
  return Math.min(1, ((right - left) * (bottom - top)) / (usableWidth * usableHeight));
}

function containerOccupancy(view) {
  const placements = new Map(view.placements.map(item => [item.ref, item]));
  return view.zones.map(zone => {
    const members = zone.memberRefs.map(ref => placements.get(ref)).filter(Boolean);
    if (!members.length) return { id: zone.id, value: 0 };
    const left = Math.min(...members.map(item => item.x));
    const top = Math.min(...members.map(item => item.y));
    const right = Math.max(...members.map(item => item.x + item.width));
    const bottom = Math.max(...members.map(item => item.y + item.height));
    const usableHeight = Math.max(1, zone.height - 72);
    return { id: zone.id, value: Math.min(1, ((right - left) * (bottom - top)) / (zone.width * usableHeight)) };
  });
}

function largestPrimaryGap(view) {
  const axis = view.layout.primaryAxis === "left-to-right" ? "x" : "y";
  const size = view.layout.primaryAxis === "left-to-right" ? "width" : "height";
  const intervals = view.placements.map(item => [item[axis], item[axis] + item[size]]).sort((a, b) => a[0] - b[0]);
  let end = intervals[0]?.[1] || 0, maximum = 0;
  for (const [start, nextEnd] of intervals.slice(1)) {
    maximum = Math.max(maximum, start - end);
    end = Math.max(end, nextEnd);
  }
  const medianSize = view.placements.map(item => item[size]).sort((a, b) => a - b)[Math.floor(view.placements.length / 2)] || 1;
  return { value: maximum, limit: Math.max((view.canvas[size] || 0) * 0.25, medianSize * 1.75) };
}

function evaluateView(model, view) {
  const errors = [], warnings = [];
  const viewReport = view.kind === "overview" ? errors : warnings;
  const maps = entityMaps(model);
  const mainIds = mainConnectorIds(view);
  if (view.placements.length > OVERVIEW_ELEMENT_LIMIT) viewReport.push(`${view.id} has ${view.placements.length} visible elements; limit is ${OVERVIEW_ELEMENT_LIMIT}`);
  if (view.connectors.length > OVERVIEW_CONNECTOR_LIMIT) viewReport.push(`${view.id} has ${view.connectors.length} visible connectors; limit is ${OVERVIEW_CONNECTOR_LIMIT}`);

  const degree = new Map();
  for (const connector of view.connectors) {
    const report = view.kind === "overview" || mainIds.has(connector.id) ? errors : warnings;
    degree.set(connector.from, (degree.get(connector.from) || 0) + 1);
    degree.set(connector.to, (degree.get(connector.to) || 0) + 1);
    const bends = bendCount(connector);
    if (bends > OVERVIEW_BEND_LIMIT) report.push(`${view.id}.${connector.id} has ${bends} bends; limit is ${OVERVIEW_BEND_LIMIT}`);
    const ratio = detourRatio(connector);
    if (ratio > OVERVIEW_DETOUR_LIMIT) report.push(`${view.id}.${connector.id} route ratio ${ratio.toFixed(2)} exceeds ${OVERVIEW_DETOUR_LIMIT}`);
    if (hugsBoundary(view, connector)) report.push(`${view.id}.${connector.id} uses a long boundary-hugging route`);
  }
  for (const [id, count] of degree) {
    if (maps.nodes.has(id) && count > OVERVIEW_DEGREE_LIMIT) viewReport.push(`${view.id}.${id} has connector degree ${count}; limit is ${OVERVIEW_DEGREE_LIMIT}`);
  }

  const scale = fitScale(view);
  const mainSize = Math.min(model.style.typography.nodeTitle, model.style.typography.deviceLabel, model.style.typography.connectorLabel) * scale;
  const secondarySize = Math.min(model.style.typography.nodeSubtitle, model.style.typography.zoneSubtitle, model.style.typography.footer) * scale;
  if (mainSize < MAIN_TEXT_MIN) viewReport.push(`${view.id} effective main text is ${mainSize.toFixed(1)}px; minimum is ${MAIN_TEXT_MIN}px`);
  if (secondarySize < SECONDARY_TEXT_MIN) viewReport.push(`${view.id} effective secondary text is ${secondarySize.toFixed(1)}px; minimum is ${SECONDARY_TEXT_MIN}px`);

  const utilization = contentUtilization(view);
  const utilizationMinimum = view.kind === "overview" ? OVERVIEW_CONTENT_UTILIZATION_MIN : DETAIL_CONTENT_UTILIZATION_MIN;
  if (utilization < utilizationMinimum) errors.push(`${view.id} content utilization ${(utilization * 100).toFixed(1)}% is below ${(utilizationMinimum * 100).toFixed(0)}%; crop the canvas or rebalance placements`);
  for (const occupancy of containerOccupancy(view)) if (occupancy.value < CONTAINER_OCCUPANCY_MIN) errors.push(`${view.id}.${occupancy.id} container occupancy ${(occupancy.value * 100).toFixed(1)}% is below ${(CONTAINER_OCCUPANCY_MIN * 100).toFixed(0)}%`);
  const gap = largestPrimaryGap(view);
  if (view.kind === "overview" && gap.value > gap.limit) errors.push(`${view.id} has a ${gap.value.toFixed(1)}px empty band on the primary axis; limit is ${gap.limit.toFixed(1)}px`);

  errors.push(...connectorCrossingIssues(view).map(issue => `${view.id}.${issue}`));
  for (const path of view.mainPaths) validateMainPathLayout(view, path, errors);
  return { errors, warnings, scale, mainSize, secondarySize, utilization };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log("node check-topology-readability.mjs --model <json> --out-dir <dir> --base <name> [--view <id>]");
    return;
  }
  if (!args.model || !args.outDir || !args.base) throw new Error("--model, --out-dir, and --base are required");
  const model = await readModel(args.model);
  const views = selectedViews(model, args.view);
  const errors = [], warnings = [];
  for (const view of views) {
    await readFile(artifactPaths(args.outDir, args.base, view).svg, "utf8");
    const result = evaluateView(model, view);
    errors.push(...result.errors);
    warnings.push(...result.warnings);
    console.log(`${view.id}: Fit ${(result.scale * 100).toFixed(1)}%, effective main ${result.mainSize.toFixed(1)}px, secondary ${result.secondarySize.toFixed(1)}px, content ${(result.utilization * 100).toFixed(1)}%`);
  }
  if (warnings.length) {
    console.warn(`Topology readability produced ${warnings.length} detail warning(s):`);
    warnings.forEach(warning => console.warn(`- ${warning}`));
  }
  if (errors.length) {
    console.error(`Topology readability validation failed with ${errors.length} error(s):`);
    errors.forEach(error => console.error(`- ${error}`));
    process.exitCode = 1;
    return;
  }
  console.log(`Topology readability validation passed: ${views.length} view(s)`);
}

main().catch(error => { console.error(error.message || error); process.exit(1); });
