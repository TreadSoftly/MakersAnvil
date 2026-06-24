/**
 * Read-only dashboard controller.
 *
 * Inputs: JSON from the loopback API's GET endpoints.
 * Outputs: text, badges, meters, capability cards, and blocked-action rows.
 * Safety: this file performs no POST, PUT, DELETE, file, route, or tool action.
 */

const stateUrl = "/api/state";
const healthUrl = "/api/health";
const workspaceUrl = "/api/workspace/status";
const layoutUrl = "/api/workspace/layout";
const intakeUrl = "/api/intake/catalog";
const routePreviewUrl = "/api/routes/preview";
const outputProofUrl = "/api/outputs/preview";
const toolDetectionUrl = "/api/tools/detection";
const toolDryRunUrl = "/api/tools/dry-run";

// The fallback preserves the page structure when the server is unavailable;
// it never converts missing evidence into a successful or enabled state.
const fallbackState = {
  appName: "Makers Anvil",
  apiBuild: "offline",
  claimState: "unknown",
  completion: { realApp: 0 },
  tracks: [],
  capabilities: [],
  blockedActions: ["state unavailable"],
  currentPass: { id: "unknown", title: "state unavailable", claimState: "unknown" },
  nextPass: { id: "unknown", title: "state unavailable", claimState: "unknown" },
  sourceTruth: {},
  workspaceConfig: {
    runtimeLocation: {
      mode: "unknown",
      label: "not proven",
      logicalRoot: "not proven",
      sourceRootDependency: false,
      absolutePathExposed: false,
    },
    directories: [],
    creationAction: { enabledInApi: false },
  },
  intakeCatalog: {
    claimState: "unknown",
    mode: "not proven",
    summary: { recordCount: 0, invalidRecordCount: 0 },
    safety: { sourcePathStored: false, sourceContentStored: false },
    creationAction: { enabledInApi: false },
  },
  routePreview: {
    claimState: "unknown",
    mode: "not proven",
    summary: { previewCount: 0, unmatchedCount: 0 },
    previews: [],
    safety: { sourcePathUsed: false, sourceContentRead: false },
    executionAction: { enabledInApi: false },
  },
  outputProof: {
    claimState: "unknown",
    mode: "not proven",
    logicalRoot: "not proven",
    summary: { bundleCount: 0, artifactCount: 0, requiredProofCount: 0, completedProofCount: 0 },
    bundles: [],
    actions: { create: { enabledInApi: false }, open: { enabledInApi: false } },
  },
  toolDetection: {
    claimState: "unknown",
    mode: "not proven",
    platform: { id: "unknown", claimState: "not proven" },
    summary: { toolCount: 0, detectedCount: 0, notDetectedCount: 0 },
    familyCoverage: [],
    tools: [],
    safety: { processExecuted: false, versionCommandExecuted: false, filesystemWritten: false },
    actions: { launch: { enabledInApi: false }, install: { enabledInApi: false } },
  },
  toolDryRun: {
    claimState: "unknown",
    mode: "not proven",
    summary: { routePreviewCount: 0, planCount: 0, selectedToolCount: 0, blockedPlanCount: 0, unmatchedPlanCount: 0 },
    plans: [],
    safety: {},
    executionAction: { claimState: "blocked", enabledInApi: false },
  },
};

const claimClass = (state) => String(state || "unknown").replace(/\s+/g, "-");

function badge(state) {
  return `<span class="badge ${claimClass(state)}">${state}</span>`;
}

function renderTracks(tracks) {
  // Tracks are high-level platform targets, not executable workflow actions.
  const target = document.querySelector("#tracks");
  target.innerHTML = tracks.map((track) => `
    <article class="panel">
      <div class="panel-head">
        <h2>${track.label}</h2>
        ${badge(track.claimState)}
      </div>
      <p>${track.summary}</p>
    </article>
  `).join("");
}

function renderCapabilities(capabilities) {
  // Capability buttons remain disabled until a later pass proves an action gate.
  const target = document.querySelector("#capabilities");
  target.innerHTML = capabilities.map((capability) => `
    <article class="panel capability">
      <div class="panel-head">
        <h2>${capability.label}</h2>
        ${badge(capability.claimState)}
      </div>
      <p>${capability.summary}</p>
      <button class="ghost-button" type="button" disabled title="Action disabled until a proof gate exists">⊘</button>
    </article>
  `).join("");
}

function renderBlocked(actions) {
  const target = document.querySelector("#blocked-actions");
  target.innerHTML = actions.map((action) => `<li><span>■</span>${action}</li>`).join("");
}

function renderWorkspace(state, workspace) {
  const current = workspace.currentPass || state.currentPass || fallbackState.currentPass;
  const next = workspace.nextPass || state.nextPass || fallbackState.nextPass;
  const sourceTruth = workspace.sourceTruth || state.sourceTruth || {};
  const workspaceState = document.querySelector("#workspace-state");
  workspaceState.textContent = workspace.claimState || state.claimState || "unknown";
  workspaceState.className = `badge ${claimClass(workspaceState.textContent)}`;
  document.querySelector("#current-pass").textContent = `${current.id} · ${current.title}`;
  document.querySelector("#next-pass").textContent = `${next.id} · ${next.title}`;
  document.querySelector("#status-source").textContent = sourceTruth.statusPath || "not proven";
}

function renderLayout(state, layout = {}) {
  const workspaceConfig = layout.runtimeLocation ? layout : state.workspaceConfig || fallbackState.workspaceConfig;
  const layoutState = document.querySelector("#layout-state");
  layoutState.textContent = workspaceConfig.claimState || "unknown";
  layoutState.className = `badge ${claimClass(layoutState.textContent)}`;
  const runtimeLocation = workspaceConfig.runtimeLocation || fallbackState.workspaceConfig.runtimeLocation;
  document.querySelector("#runtime-mode").textContent = runtimeLocation.mode || "not proven";
  document.querySelector("#runtime-location").textContent = runtimeLocation.label && runtimeLocation.logicalRoot
    ? `${runtimeLocation.label} · ${runtimeLocation.logicalRoot}`
    : "not proven";
  const directories = workspaceConfig.directories || [];
  const existingCount = directories.filter((directory) => directory.exists).length;
  document.querySelector("#runtime-directories").textContent = `${existingCount}/${directories.length} detected`;
  document.querySelector("#runtime-source-dependency").textContent = runtimeLocation.sourceRootDependency === false
    ? "none"
    : "not proven";
  const creation = workspaceConfig.creationAction || {};
  document.querySelector("#runtime-init").textContent = creation.enabledInApi === false ? `${creation.script} · API disabled` : "not proven";
}

function renderIntake(state, catalog = {}) {
  const intake = catalog.schemaVersion ? catalog : state.intakeCatalog || fallbackState.intakeCatalog;
  const intakeState = document.querySelector("#intake-state");
  intakeState.textContent = intake.claimState || "unknown";
  intakeState.className = `badge ${claimClass(intakeState.textContent)}`;
  document.querySelector("#intake-mode").textContent = intake.mode || "not proven";
  const summary = intake.summary || {};
  document.querySelector("#intake-records").textContent = `${summary.recordCount || 0} staged · ${summary.invalidRecordCount || 0} invalid`;
  const safety = intake.safety || {};
  document.querySelector("#intake-source-data").textContent = safety.sourcePathStored === false && safety.sourceContentStored === false
    ? "paths and contents not stored"
    : "not proven";
  document.querySelector("#intake-api-action").textContent = intake.creationAction?.enabledInApi === false ? "blocked" : "not proven";
}

function renderRoutePreview(state, response = {}) {
  const routePreview = response.schemaVersion ? response : state.routePreview || fallbackState.routePreview;
  const previewState = document.querySelector("#route-preview-state");
  previewState.textContent = routePreview.claimState || "unknown";
  previewState.className = `badge ${claimClass(previewState.textContent)}`;
  document.querySelector("#route-preview-mode").textContent = routePreview.mode || "not proven";
  const summary = routePreview.summary || {};
  const previewCount = summary.previewCount || 0;
  const candidateLabel = previewCount === 1 ? "candidate" : "candidates";
  document.querySelector("#route-preview-count").textContent = `${previewCount} ${candidateLabel} · ${summary.unmatchedCount || 0} unmatched`;
  const safety = routePreview.safety || {};
  document.querySelector("#route-preview-source").textContent = safety.sourcePathUsed === false && safety.sourceContentRead === false
    ? "metadata records only"
    : "not proven";
  document.querySelector("#route-preview-execution").textContent = routePreview.executionAction?.enabledInApi === false
    ? "blocked"
    : "not proven";

  const target = document.querySelector("#route-preview-list");
  target.replaceChildren();
  if (!routePreview.previews?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No route previews available.";
    target.append(empty);
    return;
  }

  // Source display names originate in untrusted local metadata. DOM text nodes
  // preserve the filename literally and prevent it from becoming executable HTML.
  routePreview.previews.forEach((preview) => {
    const item = document.createElement("article");
    item.className = "route-preview-item";
    const heading = document.createElement("div");
    heading.className = "route-preview-head";
    const title = document.createElement("h3");
    title.textContent = preview.route.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(preview.claimState)}`;
    stateBadge.textContent = preview.claimState;
    heading.append(title, stateBadge);

    const source = document.createElement("p");
    source.className = "route-preview-source";
    source.textContent = `${preview.source.displayName} · ${preview.source.kind} · ${preview.source.extension}`;
    const routeSummary = document.createElement("p");
    routeSummary.textContent = preview.route.summary;
    const tool = document.createElement("p");
    tool.className = "route-preview-tool";
    tool.textContent = `Tool family: ${preview.route.toolFamily}`;
    const steps = document.createElement("ol");
    steps.className = "route-step-list";
    preview.steps.forEach((step) => {
      const itemStep = document.createElement("li");
      itemStep.textContent = `${step.label} · ${step.phase} · ${step.claimState}`;
      steps.append(itemStep);
    });
    const blockers = document.createElement("p");
    blockers.className = "route-preview-blockers";
    blockers.textContent = `Blocked by: ${preview.readiness.blockers.join(", ")}`;
    item.append(heading, source, routeSummary, tool, steps, blockers);
    target.append(item);
  });
}

function renderOutputProof(state, response = {}) {
  const outputProof = response.schemaVersion ? response : state.outputProof || fallbackState.outputProof;
  const outputState = document.querySelector("#output-proof-state");
  outputState.textContent = outputProof.claimState || "unknown";
  outputState.className = `badge ${claimClass(outputState.textContent)}`;
  document.querySelector("#output-proof-mode").textContent = outputProof.mode || "not proven";
  const summary = outputProof.summary || {};
  const bundleCount = summary.bundleCount || 0;
  const bundleLabel = bundleCount === 1 ? "bundle" : "bundles";
  document.querySelector("#output-bundle-count").textContent = `${bundleCount} ${bundleLabel} · ${summary.artifactCount || 0} artifacts`;
  document.querySelector("#output-proof-count").textContent = `${summary.completedProofCount || 0}/${summary.requiredProofCount || 0} complete`;
  document.querySelector("#output-logical-root").textContent = outputProof.logicalRoot || "not proven";
  const actions = outputProof.actions || {};
  document.querySelector("#output-actions").textContent = actions.create?.enabledInApi === false && actions.open?.enabledInApi === false
    ? "create and open blocked"
    : "not proven";

  const target = document.querySelector("#output-bundle-list");
  target.replaceChildren();
  if (!outputProof.bundles?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No output bundle previews available.";
    target.append(empty);
    return;
  }

  // Bundle labels and source names remain text nodes because they can include
  // untrusted local metadata and must never become markup or executable UI.
  outputProof.bundles.forEach((bundle) => {
    const item = document.createElement("article");
    item.className = "output-bundle-item";
    const heading = document.createElement("div");
    heading.className = "output-bundle-head";
    const title = document.createElement("h3");
    title.textContent = bundle.output.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(bundle.claimState)}`;
    stateBadge.textContent = bundle.claimState;
    heading.append(title, stateBadge);

    const source = document.createElement("p");
    source.className = "output-bundle-source";
    source.textContent = `${bundle.source.displayName} · ${bundle.source.kind}`;
    const destination = document.createElement("p");
    destination.className = "output-bundle-destination";
    destination.textContent = bundle.output.logicalDirectory;

    const columns = document.createElement("div");
    columns.className = "output-proof-columns";
    const artifactColumn = document.createElement("div");
    const artifactTitle = document.createElement("h4");
    artifactTitle.textContent = "Expected artifacts";
    const artifacts = document.createElement("ul");
    artifacts.className = "output-proof-list";
    bundle.artifacts.forEach((artifact) => {
      const listItem = document.createElement("li");
      listItem.textContent = `${artifact.label} · ${artifact.suggestedExtension} · ${artifact.claimState}`;
      artifacts.append(listItem);
    });
    artifactColumn.append(artifactTitle, artifacts);

    const proofColumn = document.createElement("div");
    const proofTitle = document.createElement("h4");
    proofTitle.textContent = "Required proof";
    const proof = document.createElement("ul");
    proof.className = "output-proof-list";
    bundle.proof.forEach((proofItem) => {
      const listItem = document.createElement("li");
      listItem.textContent = `${proofItem.label} · ${proofItem.claimState}`;
      proof.append(listItem);
    });
    proofColumn.append(proofTitle, proof);
    columns.append(artifactColumn, proofColumn);

    const blockers = document.createElement("p");
    blockers.className = "output-proof-blockers";
    blockers.textContent = `Blocked by: ${bundle.readiness.blockers.join(", ")}`;
    item.append(heading, source, destination, columns, blockers);
    target.append(item);
  });
}

function renderToolDetection(state, response = {}) {
  const toolDetection = response.schemaVersion ? response : state.toolDetection || fallbackState.toolDetection;
  const toolState = document.querySelector("#tool-detection-state");
  toolState.textContent = toolDetection.claimState || "unknown";
  toolState.className = `badge ${claimClass(toolState.textContent)}`;
  document.querySelector("#tool-platform").textContent = toolDetection.platform?.id || "unknown";
  const summary = toolDetection.summary || {};
  document.querySelector("#tool-detection-count").textContent = `${summary.detectedCount || 0}/${summary.toolCount || 0} detected`;
  const coverage = toolDetection.familyCoverage || [];
  const coveredFamilies = coverage.filter((family) => family.detectedToolCount > 0).length;
  document.querySelector("#tool-family-coverage").textContent = `${coveredFamilies}/${coverage.length} families covered`;
  const safety = toolDetection.safety || {};
  document.querySelector("#tool-detection-safety").textContent = safety.processExecuted === false
    && safety.versionCommandExecuted === false
    && safety.filesystemWritten === false
    ? "paths redacted · nothing executed or written"
    : "not proven";
  const actions = toolDetection.actions || {};
  document.querySelector("#tool-detection-actions").textContent = actions.launch?.enabledInApi === false
    && actions.install?.enabledInApi === false
    ? "launch and software changes blocked"
    : "not proven";

  const familyTarget = document.querySelector("#tool-family-list");
  familyTarget.replaceChildren();
  coverage.forEach((family) => {
    const item = document.createElement("li");
    item.textContent = `${family.id} · ${family.detectedToolCount} detected · ${family.claimState}`;
    familyTarget.append(item);
  });

  const toolTarget = document.querySelector("#tool-detection-list");
  toolTarget.replaceChildren();
  toolDetection.tools?.forEach((tool) => {
    const item = document.createElement("article");
    item.className = "tool-detection-item";
    const heading = document.createElement("div");
    heading.className = "tool-detection-head";
    const title = document.createElement("h3");
    title.textContent = tool.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(tool.claimState)}`;
    stateBadge.textContent = tool.claimState;
    heading.append(title, stateBadge);

    const identity = document.createElement("p");
    identity.className = "tool-identity";
    identity.textContent = `${tool.publisher} · ${tool.families.join(", ")}`;
    const evidence = document.createElement("p");
    evidence.textContent = tool.detection.installed
      ? `${tool.detection.method} · ${tool.detection.executableName}`
      : "No match in checked PATH or standard locations";
    const version = document.createElement("p");
    version.className = "tool-version";
    version.textContent = `Version: ${tool.version.claimState}`;
    item.append(heading, identity, evidence, version);
    toolTarget.append(item);
  });
}

function renderToolDryRun(state, response = {}) {
  const dryRun = response.schemaVersion ? response : state.toolDryRun || fallbackState.toolDryRun;
  const dryRunState = document.querySelector("#tool-dry-run-state");
  dryRunState.textContent = dryRun.claimState || "unknown";
  dryRunState.className = `badge ${claimClass(dryRunState.textContent)}`;
  document.querySelector("#tool-dry-run-mode").textContent = dryRun.mode || "not proven";
  const summary = dryRun.summary || {};
  document.querySelector("#tool-dry-run-count").textContent = `${summary.planCount || 0} planned · ${summary.blockedPlanCount || 0} blocked`;
  document.querySelector("#tool-dry-run-selection").textContent = `${summary.selectedToolCount || 0}/${summary.planCount || 0} plans matched`;
  const safety = dryRun.safety || {};
  document.querySelector("#tool-dry-run-command").textContent = safety.commandConstructed === false
    ? "not constructed"
    : "not proven";
  document.querySelector("#tool-dry-run-execution").textContent = dryRun.executionAction?.enabledInApi === false
    && safety.processExecuted === false
    && safety.selectedFileHandedOff === false
    ? "handoff and execution blocked"
    : "not proven";

  const target = document.querySelector("#tool-dry-run-list");
  target.replaceChildren();
  if (!dryRun.plans?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No tool dry-run plans available.";
    target.append(empty);
    return;
  }

  // Display names are untrusted metadata and logical references deliberately
  // replace private source/output paths, so every plan is rendered as text.
  dryRun.plans.forEach((plan) => {
    const item = document.createElement("article");
    item.className = "tool-dry-run-item";
    const heading = document.createElement("div");
    heading.className = "tool-dry-run-head";
    const title = document.createElement("h3");
    title.textContent = plan.invocation.operation.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(plan.claimState)}`;
    stateBadge.textContent = plan.claimState;
    heading.append(title, stateBadge);

    const source = document.createElement("p");
    source.className = "tool-dry-run-source";
    source.textContent = `${plan.source.displayName} · ${plan.route.label}`;
    const selection = document.createElement("p");
    selection.className = "tool-dry-run-selection";
    selection.textContent = plan.toolSelection.selectedTool
      ? `${plan.toolSelection.selectedTool.label} · ${plan.toolSelection.selectedTool.executableName}`
      : `No detected candidate · ${plan.toolSelection.requiredFamily}`;
    const references = document.createElement("p");
    references.className = "tool-dry-run-references";
    references.textContent = `${plan.source.logicalReference} → ${plan.output.logicalDirectory}`;
    const blockers = document.createElement("p");
    blockers.className = "tool-dry-run-blockers";
    blockers.textContent = `Blocked by: ${plan.readiness.blockers.join(", ")}`;
    item.append(heading, source, selection, references, blockers);
    target.append(item);
  });
}

function renderState(state, health, workspace = {}, layout = {}, intake = {}, routePreview = {}, outputProof = {}, toolDetection = {}, toolDryRun = {}) {
  const completion = Number(state.completion?.realApp || 0);
  document.querySelector("#completion").textContent = `${completion.toFixed(4)}%`;
  document.querySelector("#completion-bar").style.width = `${Math.min(completion, 100)}%`;
  document.querySelector("#build-label").textContent = `${state.apiBuild || health.apiBuild || "unknown build"} · ${state.claimState}`;
  renderWorkspace(state, workspace);
  renderLayout(state, layout);
  renderIntake(state, intake);
  renderRoutePreview(state, routePreview);
  renderOutputProof(state, outputProof);
  renderToolDetection(state, toolDetection);
  renderToolDryRun(state, toolDryRun);
  renderTracks(state.tracks || []);
  renderCapabilities(state.capabilities || []);
  renderBlocked(state.blockedActions || []);
}

async function loadState() {
  // Fetch related records together so one refresh renders a coherent snapshot.
  try {
    const [stateResponse, healthResponse, workspaceResponse, layoutResponse, intakeResponse, routePreviewResponse, outputProofResponse, toolDetectionResponse, toolDryRunResponse] = await Promise.all([
      fetch(stateUrl, { method: "GET", cache: "no-store" }),
      fetch(healthUrl, { method: "GET", cache: "no-store" }),
      fetch(workspaceUrl, { method: "GET", cache: "no-store" }),
      fetch(layoutUrl, { method: "GET", cache: "no-store" }),
      fetch(intakeUrl, { method: "GET", cache: "no-store" }),
      fetch(routePreviewUrl, { method: "GET", cache: "no-store" }),
      fetch(outputProofUrl, { method: "GET", cache: "no-store" }),
      fetch(toolDetectionUrl, { method: "GET", cache: "no-store" }),
      fetch(toolDryRunUrl, { method: "GET", cache: "no-store" }),
    ]);
    if (!stateResponse.ok || !healthResponse.ok || !workspaceResponse.ok || !layoutResponse.ok || !intakeResponse.ok || !routePreviewResponse.ok || !outputProofResponse.ok || !toolDetectionResponse.ok || !toolDryRunResponse.ok) {
      throw new Error("state request failed");
    }
    renderState(
      await stateResponse.json(),
      await healthResponse.json(),
      await workspaceResponse.json(),
      await layoutResponse.json(),
      await intakeResponse.json(),
      await routePreviewResponse.json(),
      await outputProofResponse.json(),
      await toolDetectionResponse.json(),
      await toolDryRunResponse.json(),
    );
  } catch (error) {
    renderState(fallbackState, { apiBuild: "offline" });
  }
}

document.querySelector("#refresh").addEventListener("click", loadState);
loadState();
