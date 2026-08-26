#!/usr/bin/env node

import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const generator = join(rootDir, "assets", "topology-starter", "engineering-topology-generator.mjs");
const starterModel = join(rootDir, "assets", "topology-starter", "topology-model.json");
const artifactChecker = join(rootDir, "scripts", "check-topology-artifacts.mjs");
const geometryChecker = join(rootDir, "scripts", "check-svg-geometry.mjs");
const readabilityChecker = join(rootDir, "scripts", "check-topology-readability.mjs");

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function output(result) { return `${result.stdout || ""}\n${result.stderr || ""}`; }
function run(script, args) { return spawnSync(process.execPath, [script, ...args], { encoding: "utf8" }); }
function expectPass(name, result) { if (result.status !== 0) throw new Error(`${name} should pass:\n${output(result)}`); }
function expectFail(name, result, fragment) { if (result.status === 0 || !output(result).includes(fragment)) throw new Error(`${name} should fail with "${fragment}":\n${output(result)}`); }
function expectWarning(name, result, fragment) { if (result.status !== 0 || !output(result).includes(fragment)) throw new Error(`${name} should warn with "${fragment}":\n${output(result)}`); }

async function generate(root, name, model) {
  const outDir = join(root, name), modelPath = join(outDir, `${name}-model.json`);
  await mkdir(outDir, { recursive: true });
  await writeFile(modelPath, JSON.stringify(model, null, 2), "utf8");
  return { result: run(generator, ["--model", modelPath, "--out-dir", outDir, "--base", name]), outDir, modelPath, name };
}

function check(script, files, extra = []) { return run(script, ["--model", files.modelPath, "--out-dir", files.outDir, "--base", files.name, ...extra]); }

async function expectPipeline(root, name, model) {
  const files = await generate(root, name, model);
  expectPass(`${name} generation`, files.result);
  expectPass(`${name} artifacts`, check(artifactChecker, files));
  expectPass(`${name} geometry`, check(geometryChecker, files));
  expectPass(`${name} readability`, check(readabilityChecker, files));
  return files;
}

function addOverviewSupportingNode(model, index) {
  const view = model.views[0], id = `extra-${index}`, relationshipId = `rel-extra-${index}`, connectorId = `edge-extra-${index}`;
  const y = 135 + index * 38;
  model.nodes.push({ id, label: `Extra ${index}`, subtitle: "Supporting", role: "service", visualType: "service", status: "shared" });
  model.relationships.push({ id: relationshipId, from: "business-outcome", to: id, initiator: "business-outcome", method: "supporting", direction: "forward", narrativeRole: "supporting", status: "shared", viaDevices: [] });
  view.placements.push({ ref: id, displayLevel: "business", x: 40, y, width: 140, height: 32 });
  view.connectors.push({ id: connectorId, relationshipIds: [relationshipId], from: "business-outcome", to: id, direction: "forward", status: "shared", flowPhase: "supporting", viaDevices: [], route: { type: "polyline", points: [{ x: 290, y: 525 }, { x: 240, y: 525 }, { x: 240, y: y + 16 }, { x: 180, y: y + 16 }] }, emphasis: false });
  const estimate = model.confirmation.businessModel.visualBlueprint.viewEstimates.find(item => item.viewId === "overview");
  estimate.placements += 1;
  estimate.connectors += 1;
}

async function main() {
  const tempRoot = await mkdtemp(join(tmpdir(), "rumo-topology-v2-tests-"));
  const base = JSON.parse(await readFile(starterModel, "utf8"));
  const passed = [];
  try {
    const valid = await expectPipeline(tempRoot, "valid-structure-overlay", clone(base));
    const svg = await readFile(join(valid.outDir, "valid-structure-overlay-overview.svg"), "utf8");
    for (const value of ["data-visual-type=\"actor\"", "data-visual-type=\"physical-media\"", "data-visual-type=\"external-system\"", "data-visual-type=\"outcome\"", "业务主线"]) if (!svg.includes(value)) throw new Error(`valid SVG is missing ${value}`);
    passed.push("valid structure-flow overlay and semantic shapes");

    const v1 = clone(base); v1.schemaVersion = 1;
    expectFail("V1 rejection", (await generate(tempRoot, "v1", v1)).result, "schemaVersion 2 is required");
    passed.push("V1 rejection");

    const positioning = clone(base); positioning.confirmation.positioning.confirmed = false;
    expectFail("positioning gate", (await generate(tempRoot, "positioning", positioning)).result, "positioning confirmation is required");
    const business = clone(base); business.confirmation.businessModel.confirmed = false;
    expectFail("business gate", (await generate(tempRoot, "business", business)).result, "businessModel confirmation is required");
    const booleanOnly = clone(base); delete booleanOnly.confirmation.businessModel.visualBlueprint;
    expectFail("blueprint gate", (await generate(tempRoot, "boolean-only", booleanOnly)).result, "visualBlueprint is required");
    passed.push("structured dual confirmation gates");

    const selectionConflict = clone(base);
    const confirmedBranch = selectionConflict.confirmation.businessModel.visualBlueprint.branches[0];
    confirmedBranch.selectionType = "user-choice";
    confirmedBranch.selectionEvidence.resolution = "none";
    selectionConflict.views[0].narrative.branchPoints[0].selectionType = "user-choice";
    expectFail("selection conflict", (await generate(tempRoot, "selection-conflict", selectionConflict)).result, "selectionType contradicts evidence");
    passed.push("evidence and intended selection conflict");

    const incomplete = clone(base);
    incomplete.views[0].mainPaths.find(item => item.id === "controlled-path").connectorIds.splice(-2, 1);
    expectFail("incomplete branch", (await generate(tempRoot, "incomplete-branch", incomplete)).result, "cannot traverse ov-result-outcome");
    passed.push("incomplete parallel branch");

    const falseClosure = clone(base);
    falseClosure.confirmation.businessModel.visualBlueprint.outcomeRefs = ["target-execution"];
    falseClosure.confirmation.businessModel.visualBlueprint.branches = [];
    falseClosure.views[0].narrative.endRefs = ["target-execution"];
    falseClosure.views[0].narrative.branchPoints = [];
    for (const path of falseClosure.views[0].mainPaths) { path.endRef = "target-execution"; path.connectorIds = path.connectorIds.slice(0, -2); }
    falseClosure.views[0].mainFlow = falseClosure.views[0].mainFlow.slice(0, 2);
    expectFail("execution is not outcome", (await generate(tempRoot, "false-closure", falseClosure)).result, "is not an outcome node");
    passed.push("execution cannot masquerade as outcome");

    const orphanDetail = clone(base);
    orphanDetail.nodes.push({ id: "orphan-detail", label: "Orphan", subtitle: "No relation", role: "service", visualType: "service", status: "shared" });
    orphanDetail.views[1].placements.push({ ref: "orphan-detail", displayLevel: "implementation", x: 50, y: 520, width: 150, height: 70 });
    expectFail("detail orphan", (await generate(tempRoot, "detail-orphan", orphanDetail)).result, "is an orphaned placement");
    passed.push("detail orphan rejection");

    const context = clone(orphanDetail);
    Object.assign(context.views[1].placements.at(-1), { contextOnly: true, contextReason: "Reference context only" });
    context.confirmation.businessModel.visualBlueprint.viewEstimates.find(item => item.viewId === "implementation-detail").placements += 1;
    await expectPipeline(tempRoot, "valid-context", context);
    passed.push("declared context-only placement");

    const falseFlow = clone(base);
    falseFlow.views[0].mainFlow[2].placementRefs.push("standard-medium");
    expectFail("false mainFlow", (await generate(tempRoot, "false-main-flow", falseFlow)).result, "placementRefs are not connected");
    passed.push("mainFlow connected-subgraph mapping");

    const collapsed = clone(base);
    for (const placement of collapsed.views[0].placements) placement.renderAs = "service";
    expectFail("collapsed visual roles", (await generate(tempRoot, "collapsed-roles", collapsed)).result, "collapses semantic roles");
    passed.push("semantic role shape diversity");

    const fakeZones = clone(base);
    const detail = fakeZones.views[1];
    detail.zones.push({ id: "fake-stage", label: "Fake stage", boundaryType: "system", status: "shared", memberRefs: ["processing-service"], x: 40, y: 120, width: 260, height: 400 });
    expectFail("stage as zone", (await generate(tempRoot, "fake-stage-zone", fakeZones)).result, "stage-columns must use stageGuides");
    passed.push("stage guides cannot masquerade as boundaries");

    const missingLegend = clone(base); missingLegend.views[0].statusLegend = null;
    expectFail("missing status legend", (await generate(tempRoot, "missing-legend", missingLegend)).result, "without a visible statusLegend");
    passed.push("current and planned legend");

    const statusDrift = clone(base); statusDrift.views[0].connectors.find(item => item.id === "ov-service-controlled").status = "current";
    expectFail("connector status drift", (await generate(tempRoot, "status-drift", statusDrift)).result, "status differs from rel-service-controlled");
    passed.push("fact and connector status parity");

    const emptyContainer = clone(base);
    const targetZone = emptyContainer.views[0].zones.find(item => item.id === "target-environment");
    targetZone.width = 300; targetZone.height = 320;
    const emptyFiles = await generate(tempRoot, "empty-container", emptyContainer);
    expectPass("empty container generation", emptyFiles.result);
    expectFail("empty container geometry", check(geometryChecker, emptyFiles), "padding around its only child");
    passed.push("single-child container padding");

    const overflowingZoneText = clone(base);
    overflowingZoneText.views[0].zones.find(item => item.id === "exchange-boundary").subtitle = "This deliberately overlong boundary subtitle must not escape the structural container";
    const zoneTextFiles = await generate(tempRoot, "overflowing-zone-text", overflowingZoneText);
    expectPass("overflowing zone text generation", zoneTextFiles.result);
    expectFail("overflowing zone text geometry", check(geometryChecker, zoneTextFiles), "subtitle overflows its boundary");
    passed.push("structural boundary text overflow");

    const overflowingStageText = clone(base);
    overflowingStageText.views[1].stageGuides.find(item => item.id === "detail-exchange").subtitle = "This deliberately overlong stage subtitle must remain inside its stage guide";
    const stageTextFiles = await generate(tempRoot, "overflowing-stage-text", overflowingStageText);
    expectPass("overflowing stage text generation", stageTextFiles.result);
    expectFail("overflowing stage text geometry", check(geometryChecker, stageTextFiles), "subtitle overflows its stage guide");
    passed.push("stage guide text overflow");

    const lowUtilization = clone(base); lowUtilization.views[0].canvas.height = 1500; lowUtilization.views[0].reviewViewport.height = 1500;
    const lowFiles = await generate(tempRoot, "low-utilization", lowUtilization);
    expectPass("low utilization generation", lowFiles.result);
    expectFail("low utilization readability", check(readabilityChecker, lowFiles), "content utilization");
    passed.push("55 percent overview utilization");

    const emptyBand = clone(base);
    emptyBand.views[0].canvas.width = 2200;
    emptyBand.views[0].reviewViewport.width = 2200;
    emptyBand.views[0].placements.find(item => item.ref === "target-execution").x = 1900;
    const targetBoundary = emptyBand.views[0].zones.find(item => item.id === "target-environment");
    targetBoundary.x = 1870;
    const bandFiles = await generate(tempRoot, "empty-band", emptyBand);
    expectPass("empty band generation", bandFiles.result);
    expectFail("empty band readability", check(readabilityChecker, bandFiles), "empty band on the primary axis");
    passed.push("primary-axis empty-band check");

    const dense = clone(base);
    for (let index = 1; index <= 10; index += 1) addOverviewSupportingNode(dense, index);
    const denseFiles = await generate(tempRoot, "dense-overview", dense);
    expectPass("dense generation", denseFiles.result);
    expectFail("dense overview", check(readabilityChecker, denseFiles), "visible elements; limit is 18");
    passed.push("overview density gate");

    const detailSupportingDetour = clone(base);
    detailSupportingDetour.views[1].connectors.find(item => item.id === "detail-result-store").route.points = [
      { x: 1280, y: 330 }, { x: 1300, y: 330 }, { x: 1300, y: 20 }, { x: 1330, y: 20 }, { x: 1330, y: 235 }, { x: 1350, y: 235 },
    ];
    const warningFiles = await generate(tempRoot, "support-warning", detailSupportingDetour);
    expectPass("support warning generation", warningFiles.result);
    expectWarning("support warning", check(readabilityChecker, warningFiles, ["--view", "implementation-detail"]), "detail warning(s)");
    passed.push("supporting-detail warning");

    const illegalColor = await generate(tempRoot, "illegal-color", clone(base));
    expectPass("illegal color generation", illegalColor.result);
    const svgPath = join(illegalColor.outDir, "illegal-color-overview.svg");
    await writeFile(svgPath, (await readFile(svgPath, "utf8")).replace("#222222", "#ff0000"), "utf8");
    expectFail("illegal color", check(artifactChecker, illegalColor), "undeclared non-neutral color #ff0000");
    passed.push("grayscale enforcement");

    console.log(`Topology V2 skill tests passed (${passed.length}): ${passed.join(", ")}`);
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
}

main().catch(error => { console.error(error.message || error); process.exit(1); });
