#!/usr/bin/env node

import { access, readFile } from "node:fs/promises";
import { artifactPaths, entityMaps, mainConnectorIds, readModel, selectedViews } from "./topology-v2-lib.mjs";

function parseArgs(argv) {
  const args = { model: "", outDir: "", base: "", requirePng: false, view: "" };
  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--help" || value === "-h") args.help = true;
    else if (value === "--require-png") args.requirePng = true;
    else if (["--model", "--out-dir", "--base", "--view"].includes(value) && argv[index + 1]) args[value.slice(2).replace(/-([a-z])/g, (_, character) => character.toUpperCase())] = argv[++index];
    else throw new Error(`Unknown or incomplete argument: ${value}`);
  }
  return args;
}

function escapeRegExp(value) { return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function attrValue(source, name) { return source.match(new RegExp(`\\b${escapeRegExp(name)}=["']([^"']*)["']`))?.[1] || ""; }
function allIds(svg) { return [...svg.matchAll(/\bid=["']([^"']+)["']/g)].map(match => match[1]); }
function rootTag(svg) { return svg.match(/<svg\b[^>]*>/i)?.[0] || ""; }
function normalizeHex(value) {
  const lower = value.toLowerCase();
  if (lower.length === 4) return `#${lower[1]}${lower[1]}${lower[2]}${lower[2]}${lower[3]}${lower[3]}`;
  return lower.length === 9 ? lower.slice(0, 7) : lower;
}
function neutral(value) { const hex = normalizeHex(value); return hex[1] === hex[3] && hex[3] === hex[5]; }

function validateSvgRoot(view, svg, errors) {
  const root = rootTag(svg);
  if (!root) return errors.push(`${view.id}: SVG root is missing`);
  const width = Number(attrValue(root, "width"));
  const height = Number(attrValue(root, "height"));
  const viewBox = attrValue(root, "viewBox").trim().replace(/\s+/g, " ");
  if (width !== view.canvas.width || height !== view.canvas.height) errors.push(`${view.id}: SVG is ${width}x${height}; expected ${view.canvas.width}x${view.canvas.height}`);
  if (viewBox !== `0 0 ${view.canvas.width} ${view.canvas.height}`) errors.push(`${view.id}: unexpected viewBox ${viewBox}`);
  if (attrValue(root, "data-view") !== view.id) errors.push(`${view.id}: root data-view does not match`);
  const duplicates = allIds(svg).filter((id, index, values) => values.indexOf(id) !== index);
  for (const id of new Set(duplicates)) errors.push(`${view.id}: duplicate SVG id ${id}`);
}

function semanticTag(svg, id) {
  return svg.match(new RegExp(`<g\\b[^>]*\\bid=["']${escapeRegExp(id)}["'][^>]*>`, "i"))?.[0] || "";
}

function validateSemanticParity(model, view, svg, errors) {
  const maps = entityMaps(model);
  for (const zone of view.zones) {
    const tag = semanticTag(svg, `${view.id}-zone-${zone.id}`);
    if (!tag) errors.push(`${view.id}: missing zone ${zone.id}`);
    else {
      const expected = { "data-view": view.id, "data-role": "zone", "data-boundary-type": zone.boundaryType, "data-status": zone.status, "data-members": zone.memberRefs.join(",") };
      for (const [name, value] of Object.entries(expected)) if (attrValue(tag, name) !== value) errors.push(`${view.id}.${zone.id}: ${name} differs from model`);
    }
  }
  for (const guide of view.stageGuides) if (!semanticTag(svg, `${view.id}-stage-${guide.id}`)) errors.push(`${view.id}: missing stage guide ${guide.id}`);
  for (const placement of view.placements) {
    const tag = semanticTag(svg, `${view.id}-placement-${placement.ref}`);
    const role = maps.devices.has(placement.ref) ? "device" : maps.groups.has(placement.ref) ? "group" : "node";
    const fact = maps.nodes.get(placement.ref) || maps.devices.get(placement.ref) || maps.groups.get(placement.ref);
    if (!tag) errors.push(`${view.id}: missing placement ${placement.ref}`);
    else {
      if (attrValue(tag, "data-view") !== view.id || attrValue(tag, "data-ref") !== placement.ref || attrValue(tag, "data-role") !== role) errors.push(`${view.id}: placement ${placement.ref} semantic attributes differ`);
      if (attrValue(tag, "data-display-level") !== placement.displayLevel) errors.push(`${view.id}: placement ${placement.ref} display level differs`);
      if (attrValue(tag, "data-visual-type") !== (placement.renderAs || fact.visualType || "service")) errors.push(`${view.id}: placement ${placement.ref} visual type differs`);
      if (attrValue(tag, "data-status") !== fact.status) errors.push(`${view.id}: placement ${placement.ref} status differs`);
      if (attrValue(tag, "data-context-only") !== String(Boolean(placement.contextOnly))) errors.push(`${view.id}: placement ${placement.ref} contextOnly differs`);
      if (attrValue(tag, "data-emphasis") !== String(Boolean(placement.emphasis))) errors.push(`${view.id}: placement ${placement.ref} emphasis differs`);
    }
  }
  const mainIds = mainConnectorIds(view);
  for (const connector of view.connectors) {
    const tag = semanticTag(svg, `${view.id}-connector-${connector.id}`);
    if (!tag) {
      errors.push(`${view.id}: missing connector ${connector.id}`);
      continue;
    }
    const expected = {
      "data-role": "connector", "data-view": view.id, "data-ref": connector.id,
      "data-relationships": connector.relationshipIds.join(","), "data-from": connector.from,
      "data-to": connector.to, "data-direction": connector.direction,
      "data-via-devices": connector.viaDevices.join(","), "data-emphasis": String(Boolean(connector.emphasis)),
      "data-status": connector.status, "data-flow-phase": connector.flowPhase,
      "data-main-path": String(mainIds.has(connector.id)),
    };
    for (const [name, value] of Object.entries(expected)) if (attrValue(tag, name) !== value) errors.push(`${view.id}.${connector.id}: ${name} differs from model`);
  }
  for (const flow of view.mainFlow) {
    if (!svg.includes(`data-role="main-flow" data-ref="${flow.id}"`)) errors.push(`${view.id}: missing rendered mainFlow ${flow.id}`);
  }
  if (view.statusLegend?.visible && !svg.includes(`id="${view.id}-status-legend" data-role="status-legend"`)) errors.push(`${view.id}: missing status legend`);
}

function validateColors(model, view, svg, errors) {
  if (/<(?:linearGradient|radialGradient|filter)\b|\bfilter\s*=|(?:filter|box-shadow|text-shadow)\s*:/i.test(svg)) errors.push(`${view.id}: gradients, filters, and shadows are forbidden`);
  if (/\b(?:rgb|rgba|hsl|hsla)\s*\(/i.test(svg)) errors.push(`${view.id}: functional color syntax is forbidden`);
  const declared = model.style.mode === "grayscale-accent" ? normalizeHex(model.style.accent.color) : null;
  const colors = new Set([...svg.matchAll(/#[0-9a-f]{3,8}\b/gi)].map(match => match[0].toLowerCase()));
  for (const color of colors) {
    if (![4, 7].includes(color.length)) {
      errors.push(`${view.id}: unsupported color ${color}`);
      continue;
    }
    const normalized = normalizeHex(color);
    if (!neutral(normalized) && normalized !== declared) errors.push(`${view.id}: undeclared non-neutral color ${color}`);
  }
}

function validatePng(view, png, errors) {
  if (png.length < 24 || png.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a") return errors.push(`${view.id}: invalid PNG signature`);
  const width = png.readUInt32BE(16), height = png.readUInt32BE(20);
  if (width !== view.canvas.width || height !== view.canvas.height) errors.push(`${view.id}: PNG is ${width}x${height}; expected ${view.canvas.width}x${view.canvas.height}`);
}

async function fileExists(path) {
  try { await access(path); return true; } catch { return false; }
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log("node check-topology-artifacts.mjs --model <json> --out-dir <dir> --base <name> [--require-png] [--view <id>]");
    return;
  }
  if (!args.model || !args.outDir || !args.base) throw new Error("--model, --out-dir, and --base are required");
  const model = await readModel(args.model);
  const views = selectedViews(model, args.view);
  const sharedPaths = artifactPaths(args.outDir, args.base, views[0]);
  const [markdown, preview] = await Promise.all([readFile(sharedPaths.markdown, "utf8"), readFile(sharedPaths.preview, "utf8")]);
  const errors = [];
  const allSources = [markdown, preview];
  const svgByView = new Map(await Promise.all(model.views.map(async view => [view.id, await readFile(artifactPaths(args.outDir, args.base, view).svg, "utf8")])));
  allSources.push(...svgByView.values());

  for (const relationship of model.relationships) if (!markdown.includes(relationship.id)) errors.push(`Markdown is missing relationship ${relationship.id}`);
  for (const view of model.views) if (!preview.includes(`${args.base}-${view.id}.svg`)) errors.push(`preview is missing view ${view.id}`);
  for (const view of views) {
    const paths = artifactPaths(args.outDir, args.base, view);
    const svg = svgByView.get(view.id);
    validateSvgRoot(view, svg, errors);
    validateSemanticParity(model, view, svg, errors);
    validateColors(model, view, svg, errors);
    const pngExists = await fileExists(paths.png);
    if (args.requirePng && !pngExists) errors.push(`${view.id}: required PNG is missing`);
    if (pngExists) validatePng(view, await readFile(paths.png), errors);
  }
  const combined = allSources.join("\n");
  for (const required of model.acceptance.requiredText) if (!combined.includes(required)) errors.push(`required text missing: ${required}`);
  for (const forbidden of model.acceptance.forbiddenText) if (combined.includes(forbidden)) errors.push(`forbidden text found: ${forbidden}`);

  if (errors.length) {
    console.error(`Topology artifact validation failed with ${errors.length} error(s):`);
    errors.forEach(error => console.error(`- ${error}`));
    process.exitCode = 1;
    return;
  }
  console.log(`Topology artifact validation passed: ${views.length} view(s), ${model.relationships.length} fact relationship(s)`);
}

main().catch(error => { console.error(error.message || error); process.exit(1); });
