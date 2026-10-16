#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { artifactPaths, bottom, collinearOverlap, connectorCrossingIssues, displayText, entityMaps, estimatedTextWidth, overlaps, pointOnBoundary, readModel, right, routePoints, routeSegments, segmentIntersectsBox, segmentsIntersect, selectedViews, TRACK_OVERLAP_LIMIT } from "./topology-v2-lib.mjs";

const TEXT_PADDING = 14;
const LABEL_PADDING = 3;
const MIN_TERMINAL_SEGMENT = 14;
const SINGLE_CHILD_PADDING_MAX = 56;
const ZONE_HEADER_HEIGHT = 72;

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

function distance(first, second) { return Math.hypot(second.x - first.x, second.y - first.y); }

function placementBox(placement, kind) {
  return { id: placement.ref, kind, x: placement.x, y: placement.y, width: placement.width, height: placement.height };
}

function containsBox(container, child) {
  return child.x >= container.x && child.y >= container.y && right(child) <= right(container) && bottom(child) <= bottom(container);
}

function borderSegments(box) {
  const x2 = right(box), y2 = bottom(box);
  return [
    { a: { x: box.x, y: box.y }, b: { x: x2, y: box.y } },
    { a: { x: x2, y: box.y }, b: { x: x2, y: y2 } },
    { a: { x: x2, y: y2 }, b: { x: box.x, y: y2 } },
    { a: { x: box.x, y: y2 }, b: { x: box.x, y: box.y } },
  ];
}

function validateCanvas(view, obstacles, labels, errors) {
  const flowStart = view.canvas.height - (72 + Math.max(1, view.mainFlow.length) * 28);
  for (const item of [...obstacles, ...labels, ...view.zones.map(zone => ({ id: zone.id, kind: "zone", ...zone }))]) {
    if (item.x < 0 || item.y < 0 || right(item) > view.canvas.width || bottom(item) > view.canvas.height) errors.push(`${view.id}.${item.id} exceeds the canvas`);
    if (item.kind !== "zone" && bottom(item) > flowStart - 12) errors.push(`${view.id}.${item.id} intrudes into the main-flow footer`);
  }
  for (const connector of view.connectors) {
    if (routePoints(connector).some(point => point.x < 0 || point.y < 0 || point.x > view.canvas.width || point.y > view.canvas.height)) errors.push(`${view.id}.${connector.id} route exceeds the canvas`);
    if (routePoints(connector).some(point => point.y > flowStart - 12)) errors.push(`${view.id}.${connector.id} route intrudes into the main-flow footer`);
  }
}

function validateContainment(view, obstacles, errors) {
  const byId = new Map(obstacles.map(item => [item.id, item]));
  for (const zone of view.zones) {
    const members = zone.memberRefs.map(ref => byId.get(ref)).filter(Boolean);
    for (const member of members) if (!containsBox(zone, member)) errors.push(`${view.id}.${member.id} is outside declared boundary ${zone.id}`);
    if (members.length === 1) {
      const member = members[0];
      const gaps = {
        left: member.x - zone.x,
        right: right(zone) - right(member),
        top: member.y - (zone.y + ZONE_HEADER_HEIGHT),
        bottom: bottom(zone) - bottom(member),
      };
      for (const [side, gap] of Object.entries(gaps)) if (gap > SINGLE_CHILD_PADDING_MAX) errors.push(`${view.id}.${zone.id} has ${gap.toFixed(1)}px ${side} padding around its only child; maximum is ${SINGLE_CHILD_PADDING_MAX}px`);
    }
  }
}

function validatePlacementOverlap(view, obstacles, errors) {
  for (let first = 0; first < obstacles.length; first += 1) {
    for (let second = first + 1; second < obstacles.length; second += 1) {
      if (overlaps(obstacles[first], obstacles[second], 0.5)) errors.push(`${view.id}.${obstacles[first].id} overlaps ${obstacles[second].id}`);
    }
  }
}

function validateText(model, view, labels, errors) {
  const maps = entityMaps(model);
  const typography = model.style.typography;
  for (const zone of view.zones) {
    if (estimatedTextWidth(zone.label, typography.zoneTitle) > zone.width - TEXT_PADDING * 2) errors.push(`${view.id}.${zone.id} title overflows its boundary`);
    if (zone.subtitle && estimatedTextWidth(zone.subtitle, typography.zoneSubtitle) > zone.width - TEXT_PADDING * 2) errors.push(`${view.id}.${zone.id} subtitle overflows its boundary`);
  }
  for (const guide of view.stageGuides) {
    if (estimatedTextWidth(guide.label, typography.zoneTitle) > guide.width - TEXT_PADDING * 2) errors.push(`${view.id}.${guide.id} title overflows its stage guide`);
    if (guide.subtitle && estimatedTextWidth(guide.subtitle, typography.zoneSubtitle) > guide.width - TEXT_PADDING * 2) errors.push(`${view.id}.${guide.id} subtitle overflows its stage guide`);
  }
  for (const placement of view.placements) {
    const fact = maps.nodes.get(placement.ref) || maps.groups.get(placement.ref) || maps.devices.get(placement.ref);
    const display = displayText(fact, placement);
    if (maps.devices.has(placement.ref)) {
      if (estimatedTextWidth(display.label, typography.deviceLabel) > placement.labelBox.width - TEXT_PADDING) errors.push(`${view.id}.${placement.ref} label overflows labelBox`);
      continue;
    }
    if (estimatedTextWidth(display.label, typography.nodeTitle) > placement.width - TEXT_PADDING * 2) errors.push(`${view.id}.${placement.ref} label overflows its box`);
    if (display.subtitle && estimatedTextWidth(display.subtitle, typography.nodeSubtitle) > placement.width - TEXT_PADDING * 2) errors.push(`${view.id}.${placement.ref} subtitle overflows its box`);
  }
  for (const connector of view.connectors) {
    if (connector.label && estimatedTextWidth(connector.label, typography.connectorLabel) > connector.labelBox.width - TEXT_PADDING * 2) errors.push(`${view.id}.${connector.id} label overflows labelBox`);
  }
  for (let first = 0; first < labels.length; first += 1) {
    for (let second = first + 1; second < labels.length; second += 1) {
      if (overlaps(labels[first], labels[second])) errors.push(`${view.id}.${labels[first].id} overlaps ${labels[second].id}`);
    }
  }
}

function validateLabels(view, obstacles, labels, errors) {
  for (const label of labels) {
    for (const obstacle of obstacles) {
      if (obstacle.id !== label.owner && overlaps(label, obstacle, -LABEL_PADDING)) errors.push(`${view.id}.${label.id} intrudes into ${obstacle.id}`);
    }
  }
}

function validateConnectors(view, obstacles, labels, errors, warnings) {
  for (const connector of view.connectors) {
    const points = connector.route.points;
    const segments = routeSegments(connector);
    if (points.length > 1 && distance(points[0], points[1]) < MIN_TERMINAL_SEGMENT) errors.push(`${view.id}.${connector.id} has a short first segment`);
    if (points.length > 1 && distance(points.at(-2), points.at(-1)) < MIN_TERMINAL_SEGMENT) errors.push(`${view.id}.${connector.id} has a short final segment`);
    const source = obstacles.find(item => item.id === connector.from);
    const target = obstacles.find(item => item.id === connector.to);
    if (!source || !pointOnBoundary(source, points[0])) errors.push(`${view.id}.${connector.id} route does not start on ${connector.from} boundary`);
    if (!target || !pointOnBoundary(target, points.at(-1))) errors.push(`${view.id}.${connector.id} route does not end on ${connector.to} boundary`);
    for (const obstacle of obstacles) {
      if (obstacle.id === connector.from || obstacle.id === connector.to) continue;
      const crosses = segments.some(segment => segmentIntersectsBox(segment, obstacle, 2));
      if (crosses && !connector.viaDevices.includes(obstacle.id)) errors.push(`${view.id}.${connector.id} crosses unrelated ${obstacle.id}`);
    }
    for (const deviceId of connector.viaDevices) {
      const device = obstacles.find(item => item.id === deviceId);
      if (!device || !segments.some(segment => segmentIntersectsBox(segment, device, 0))) errors.push(`${view.id}.${connector.id} does not traverse required device ${deviceId}`);
    }
    for (const obstacle of obstacles) {
      if (segments.some(segment => borderSegments(obstacle).some(border => collinearOverlap(segment, border) > TRACK_OVERLAP_LIMIT))) errors.push(`${view.id}.${connector.id} overlaps ${obstacle.id} border`);
    }
    for (const label of labels) {
      if (label.owner !== connector.id && segments.some(segment => segmentIntersectsBox(segment, label, 2))) errors.push(`${view.id}.${connector.id} crosses unrelated ${label.id}`);
    }
    if (connector.route.type === "bezier") warnings.push(`${view.id}.${connector.id}: sampled Bezier route requires visual review near obstacles`);
  }
  for (let first = 0; first < view.connectors.length; first += 1) {
    for (let second = first + 1; second < view.connectors.length; second += 1) {
      let longest = 0;
      for (const a of routeSegments(view.connectors[first])) for (const b of routeSegments(view.connectors[second])) longest = Math.max(longest, collinearOverlap(a, b));
      if (longest > TRACK_OVERLAP_LIMIT) errors.push(`${view.id}.${view.connectors[first].id} shares ${longest.toFixed(1)}px of route with ${view.connectors[second].id}`);
    }
  }
  errors.push(...connectorCrossingIssues(view).map(issue => `${view.id}.${issue}`));
}

function validateSvgIdentity(view, svg, errors) {
  for (const placement of view.placements) {
    if (!svg.includes(`id="${view.id}-placement-${placement.ref}"`)) errors.push(`${view.id}: SVG is missing placement ${placement.ref}`);
  }
  for (const connector of view.connectors) {
    if (!svg.includes(`id="${view.id}-connector-${connector.id}"`)) errors.push(`${view.id}: SVG is missing connector ${connector.id}`);
  }
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log("node check-svg-geometry.mjs --model <json> --out-dir <dir> --base <name> [--view <id>]");
    return;
  }
  if (!args.model || !args.outDir || !args.base) throw new Error("--model, --out-dir, and --base are required");
  const model = await readModel(args.model);
  const views = selectedViews(model, args.view);
  const maps = entityMaps(model);
  const allErrors = [], allWarnings = [];
  for (const view of views) {
    const svg = await readFile(artifactPaths(args.outDir, args.base, view).svg, "utf8");
    const obstacles = view.placements.map(placement => placementBox(placement, maps.devices.has(placement.ref) ? "device" : maps.groups.has(placement.ref) ? "group" : "node"));
    const labels = [
      ...view.placements.filter(item => maps.devices.has(item.ref)).map(item => ({ id: `${item.ref}-label`, owner: item.ref, ...item.labelBox })),
      ...view.connectors.filter(item => item.label).map(item => ({ id: `${item.id}-label`, owner: item.id, ...item.labelBox })),
      ...(view.statusLegend?.visible ? [{ id: "status-legend", owner: "status-legend", ...view.statusLegend }] : []),
    ];
    const errors = [], warnings = [];
    validateCanvas(view, obstacles, labels, errors);
    validateContainment(view, obstacles, errors);
    validatePlacementOverlap(view, obstacles, errors);
    validateText(model, view, labels, errors);
    validateLabels(view, obstacles, labels, errors);
    validateConnectors(view, obstacles, labels, errors, warnings);
    validateSvgIdentity(view, svg, errors);
    allErrors.push(...errors);
    allWarnings.push(...warnings);
  }
  if (allErrors.length) {
    console.error(`SVG geometry validation failed with ${allErrors.length} error(s):`);
    allErrors.forEach(error => console.error(`- ${error}`));
    process.exitCode = 1;
  } else console.log(`SVG geometry validation passed: ${views.length} view(s)`);
  if (allWarnings.length) {
    console.warn(`SVG geometry validation produced ${allWarnings.length} warning(s):`);
    allWarnings.forEach(warning => console.warn(`- ${warning}`));
  }
}

main().catch(error => { console.error(error.message || error); process.exit(1); });
