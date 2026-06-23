const stateUrl = "/api/state";
const healthUrl = "/api/health";
const workspaceUrl = "/api/workspace/status";
const layoutUrl = "/api/workspace/layout";
const intakeUrl = "/api/intake/catalog";

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
  workspaceConfig: { runtimeRoot: "unknown", directories: [], creationAction: { enabledInApi: false } },
  intakeCatalog: {
    claimState: "unknown",
    mode: "not proven",
    summary: { recordCount: 0, invalidRecordCount: 0 },
    safety: { sourcePathStored: false, sourceContentStored: false },
    creationAction: { enabledInApi: false },
  },
};

const claimClass = (state) => String(state || "unknown").replace(/\s+/g, "-");

function badge(state) {
  return `<span class="badge ${claimClass(state)}">${state}</span>`;
}

function renderTracks(tracks) {
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
  const workspaceConfig = layout.runtimeRoot ? layout : state.workspaceConfig || fallbackState.workspaceConfig;
  const layoutState = document.querySelector("#layout-state");
  layoutState.textContent = workspaceConfig.claimState || "unknown";
  layoutState.className = `badge ${claimClass(layoutState.textContent)}`;
  document.querySelector("#runtime-root").textContent = workspaceConfig.runtimeRoot || "not proven";
  const directories = workspaceConfig.directories || [];
  const existingCount = directories.filter((directory) => directory.exists).length;
  document.querySelector("#runtime-directories").textContent = `${existingCount}/${directories.length} detected`;
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

function renderState(state, health, workspace = {}, layout = {}, intake = {}) {
  const completion = Number(state.completion?.realApp || 0);
  document.querySelector("#completion").textContent = `${completion.toFixed(4)}%`;
  document.querySelector("#completion-bar").style.width = `${Math.min(completion, 100)}%`;
  document.querySelector("#build-label").textContent = `${state.apiBuild || health.apiBuild || "unknown build"} · ${state.claimState}`;
  renderWorkspace(state, workspace);
  renderLayout(state, layout);
  renderIntake(state, intake);
  renderTracks(state.tracks || []);
  renderCapabilities(state.capabilities || []);
  renderBlocked(state.blockedActions || []);
}

async function loadState() {
  try {
    const [stateResponse, healthResponse, workspaceResponse, layoutResponse, intakeResponse] = await Promise.all([
      fetch(stateUrl, { method: "GET", cache: "no-store" }),
      fetch(healthUrl, { method: "GET", cache: "no-store" }),
      fetch(workspaceUrl, { method: "GET", cache: "no-store" }),
      fetch(layoutUrl, { method: "GET", cache: "no-store" }),
      fetch(intakeUrl, { method: "GET", cache: "no-store" }),
    ]);
    if (!stateResponse.ok || !healthResponse.ok || !workspaceResponse.ok || !layoutResponse.ok || !intakeResponse.ok) {
      throw new Error("state request failed");
    }
    renderState(
      await stateResponse.json(),
      await healthResponse.json(),
      await workspaceResponse.json(),
      await layoutResponse.json(),
      await intakeResponse.json(),
    );
  } catch (error) {
    renderState(fallbackState, { apiBuild: "offline" });
  }
}

document.querySelector("#refresh").addEventListener("click", loadState);
loadState();
