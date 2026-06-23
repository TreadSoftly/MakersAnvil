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

function renderState(state, health, workspace = {}, layout = {}, intake = {}, routePreview = {}) {
  const completion = Number(state.completion?.realApp || 0);
  document.querySelector("#completion").textContent = `${completion.toFixed(4)}%`;
  document.querySelector("#completion-bar").style.width = `${Math.min(completion, 100)}%`;
  document.querySelector("#build-label").textContent = `${state.apiBuild || health.apiBuild || "unknown build"} · ${state.claimState}`;
  renderWorkspace(state, workspace);
  renderLayout(state, layout);
  renderIntake(state, intake);
  renderRoutePreview(state, routePreview);
  renderTracks(state.tracks || []);
  renderCapabilities(state.capabilities || []);
  renderBlocked(state.blockedActions || []);
}

async function loadState() {
  // Fetch related records together so one refresh renders a coherent snapshot.
  try {
    const [stateResponse, healthResponse, workspaceResponse, layoutResponse, intakeResponse, routePreviewResponse] = await Promise.all([
      fetch(stateUrl, { method: "GET", cache: "no-store" }),
      fetch(healthUrl, { method: "GET", cache: "no-store" }),
      fetch(workspaceUrl, { method: "GET", cache: "no-store" }),
      fetch(layoutUrl, { method: "GET", cache: "no-store" }),
      fetch(intakeUrl, { method: "GET", cache: "no-store" }),
      fetch(routePreviewUrl, { method: "GET", cache: "no-store" }),
    ]);
    if (!stateResponse.ok || !healthResponse.ok || !workspaceResponse.ok || !layoutResponse.ok || !intakeResponse.ok || !routePreviewResponse.ok) {
      throw new Error("state request failed");
    }
    renderState(
      await stateResponse.json(),
      await healthResponse.json(),
      await workspaceResponse.json(),
      await layoutResponse.json(),
      await intakeResponse.json(),
      await routePreviewResponse.json(),
    );
  } catch (error) {
    renderState(fallbackState, { apiBuild: "offline" });
  }
}

document.querySelector("#refresh").addEventListener("click", loadState);
loadState();
