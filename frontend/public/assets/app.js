/**
 * Purpose: Fetch and render the current Makers Anvil workbench truth.
 * Used by: index.html after the static dashboard structure has loaded.
 * Inputs: JSON from the loopback API's GET endpoints and trusted DOM regions.
 * Outputs: Workbench truth plus one choose-review-authorize intake interaction.
 * Side effects: Renders DOM, performs GETs, and may POST one explicitly authorized file.
 * Safety: Intake is same-origin/one-file; route, tool, output, and install stay blocked.
 * Failure behavior: Missing data falls back to conservative unknown/blocked truth.
 * Related proof: tests/test_api.py and browser smoke assertions.
 */

import { renderCapabilityMatrix } from "./capability-lanes.js";
import { renderContainedExecutions } from "./contained-execution.js";
import { renderActivityHistory, renderWorkbenchExperience, showWorkbenchNotice } from "./workbench-experience.js";

// Endpoint constants keep read routes and the bounded intake boundary visible in one place.
// Adding a URL here authorizes nothing: refresh uses GET; intake/settings name their guarded POST routes separately.
const stateUrl = "/api/state";
const healthUrl = "/api/health";
const workspaceUrl = "/api/workspace/status";
const layoutUrl = "/api/workspace/layout";
const intakeUrl = "/api/intake/catalog";
const intakeSessionUrl = "/api/intake/session";
const routePreviewUrl = "/api/routes/preview";
const outputProofUrl = "/api/outputs/preview";
const toolDetectionUrl = "/api/tools/detection";
const toolDryRunUrl = "/api/tools/dry-run";
const executionGatesUrl = "/api/execution/gates";
const executionRequestUrl = "/api/execution/requests/preview";
const jobWorkspaceUrl = "/api/jobs/catalog";
const workbenchExperienceUrl = "/api/workbench/experience";
const activityHistoryUrl = "/api/activity/recent";
const capabilityMatrixUrl = "/api/capabilities/matrix";
const containedExecutionPolicyUrl = "/api/executions/policy";
const containedExecutionCatalogUrl = "/api/executions/catalog";

// Intake session/token and File objects remain in process/browser memory only.
// Neither value enters durable app state, URLs, logs, or rendered HTML.
let activeIntakeSession = null;
let pendingIntakeFile = null;
let intakeBusy = false;

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
    records: [],
    safety: { sourcePathStored: false, routeExecutionEnabled: false },
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
  executionGates: {
    claimState: "unknown",
    mode: "not proven",
    scope: { routeId: "not proven", maxConcurrentExecutions: 0, executionEnabled: false },
    summary: { evaluatedPlanCount: 0, outOfScopePlanCount: 0, requiredGateCount: 0, satisfiedGateCount: 0, blockedPlanCount: 0 },
    evaluations: [],
    safety: {},
    executionAction: { claimState: "blocked", enabledInApi: false },
  },
  executionRequestPreview: {
    claimState: "unknown",
    mode: "not proven",
    scope: { routeId: "not proven", requestPersistenceEnabled: false, authorizationEnabled: false, auditWriteEnabled: false },
    summary: { previewCount: 0, persistedRequestCount: 0, acceptedAuthorizationCount: 0, writtenAuditEventCount: 0, executionReadyCount: 0 },
    previews: [],
    safety: {},
    actions: {
      createRequest: { claimState: "blocked", enabledInApi: false },
      recordAuthorization: { claimState: "blocked", enabledInApi: false },
      execute: { claimState: "blocked", enabledInApi: false },
    },
  },
  jobWorkspaceCatalog: {
    claimState: "unknown",
    mode: "not proven",
    jobsPath: "not proven",
    recordsRootExists: false,
    summary: { preparedJobCount: 0, cancellationRequestedCount: 0, invalidJobCount: 0, executionReadyCount: 0 },
    jobs: [],
    safety: {},
    actions: {
      prepare: { claimState: "staged", enabledInApi: false },
      cancel: { claimState: "staged", enabledInApi: false },
      execute: { claimState: "blocked", enabledInApi: false },
    },
  },
  capabilityMatrix: {
    claimState: "unknown",
    summary: { laneCount: 0, previewReadyLaneCount: 0 },
    ingressMethods: [],
    lanes: [],
    honesty: ["Execution remains blocked."],
  },
};

/**
 * Purpose: Convert one closed claim-state label into its CSS class token.
 * Inputs: ``state`` is an internal claim-state string such as ``preview-only``.
 * Outputs: Returns a lowercase-compatible token with whitespace replaced by dashes.
 * How it works: Coerces absent values to ``unknown`` and normalizes only whitespace.
 * Side effects: None; the arrow function returns a string without touching the DOM.
 * Failure behavior: Non-string values become strings rather than causing a hidden crash.
 * Safety: Callers use the result only as a CSS class, never as executable markup.
 * Example: ``claimClass("not proven")`` returns ``not-proven``.
 * Related proof: tests/test_frontend_workbench.py and claim-state schema checks.
 */
const claimClass = (state) => String(state || "unknown").replace(/\s+/g, "-");

/**
 * Purpose: Return trusted badge markup for internal capability and track records.
 * Inputs: Caller supplies ``state``.
 * Outputs: Returns trusted badge markup for a closed internal claim-state label.
 * How it works: Normalizes the label into a CSS class and returns the corresponding span markup.
 * Side effects: None; it returns a string and does not touch the DOM by itself.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Call only with closed claim-state data, never arbitrary user-controlled HTML.
 * Example: ``badge("blocked")`` returns markup styled as a blocked state.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function badge(state) {
  return `<span class="badge ${claimClass(state)}">${state}</span>`;
}

/**
 * Purpose: Render platform delivery truth; no track card contains an actionable control.
 * Inputs: Caller supplies ``tracks``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderTracks(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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

/**
 * Purpose: Render capability summaries and permanently disabled placeholder buttons.
 * Inputs: Caller supplies ``capabilities``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderCapabilities(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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

/**
 * Purpose: Render the durable blocked-action list supplied by committed status truth.
 * Inputs: Caller supplies ``actions``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderBlocked(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderBlocked(actions) {
  const target = document.querySelector("#blocked-actions");
  target.innerHTML = actions.map((action) => `<li><span>■</span>${action}</li>`).join("");
}

/**
 * Purpose: Merge workspace status with app state and display current durable pass pointers.
 * Inputs: Caller supplies ``state``, ``workspace``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderWorkspace(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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

/**
 * Purpose: Display logical runtime layout without exposing a resolved personal directory.
 * Inputs: Caller supplies ``state``, ``layout``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderLayout(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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

/**
 * Purpose: Display authorized intake counts, privacy boundaries, and picker readiness.
 * Inputs: Caller supplies ``state``, ``catalog``, and process-local ``session``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderIntake(fallbackState, {}, {})`` keeps Add file disabled offline.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderIntake(state, catalog = {}, session = {}) {
  const intake = catalog.schemaVersion ? catalog : state.intakeCatalog || fallbackState.intakeCatalog;
  activeIntakeSession = session.schemaVersion === "makers-anvil.api.intake-session.v1" ? session : null;
  const intakeState = document.querySelector("#intake-state");
  intakeState.textContent = intake.claimState || "unknown";
  intakeState.className = `badge ${claimClass(intakeState.textContent)}`;
  document.querySelector("#intake-mode").textContent = intake.mode || "not proven";
  const summary = intake.summary || {};
  document.querySelector("#intake-records").textContent = `${summary.recordCount || 0} staged · ${summary.invalidRecordCount || 0} invalid`;
  const safety = intake.safety || {};
  document.querySelector("#intake-source-data").textContent = safety.sourcePathStored === false
    ? "source path private · authorized copy app-owned"
    : "not proven";
  document.querySelector("#intake-api-action").textContent = intake.creationAction?.enabledInApi === true
    && intake.creationAction?.requiresExplicitAuthorization === true
    ? "explicit authorization"
    : "blocked";
  const addButton = document.querySelector("#intake-add-button");
  const fileInput = document.querySelector("#intake-file-input");
  const allowedExtensions = activeIntakeSession?.constraints?.allowedExtensions || [];
  fileInput.accept = allowedExtensions.join(",");
  addButton.disabled = intakeBusy || allowedExtensions.length === 0;
  addButton.title = allowedExtensions.length ? "Choose one source file" : "Authorized intake is unavailable";
}

/**
 * Purpose: Render one path-free intake guidance, progress, success, or error message.
 * Inputs: Caller supplies visible ``message`` and optional ``stateName``.
 * Outputs: Returns ``undefined`` after updating the ARIA live status line.
 * How it works: Writes textContent and maps only success/error to known color classes.
 * Side effects: Updates one existing DOM status element.
 * Failure behavior: Unknown state names render neutral text rather than invented success.
 * Safety: Message text is never interpreted as HTML and must not include paths/tokens.
 * Example: ``setIntakeFeedback("File rejected.", "error")`` shows a red status.
 * Related proof: Frontend structural tests and browser intake smoke.
 */
function setIntakeFeedback(message, stateName = "") {
  const feedback = document.querySelector("#intake-feedback");
  feedback.textContent = message;
  feedback.className = "intake-feedback";
  if (stateName === "success" || stateName === "error") {
    feedback.classList.add(`is-${stateName}`);
  }
}

/**
 * Purpose: Format a nonnegative file byte count for compact review text.
 * Inputs: Caller supplies browser ``File.size`` bytes.
 * Outputs: Human-readable bytes, KiB, or MiB string.
 * How it works: Chooses one fixed unit threshold and one decimal place where useful.
 * Side effects: None.
 * Failure behavior: Invalid/negative values return ``size not proven``.
 * Safety: Formatting does not replace the server's exact integer size validation.
 * Example: ``formatIntakeBytes(2048)`` returns ``2.0 KiB``.
 * Related proof: Frontend controller tests and visible review screenshots.
 */
function formatIntakeBytes(bytes) {
  if (!Number.isInteger(bytes) || bytes < 0) {
    return "size not proven";
  }
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KiB`;
  }
  return `${bytes} bytes`;
}

/**
 * Purpose: Clear only the browser's pending file review state.
 * Inputs: Optional ``preserveFeedback`` flag for completed/error messages.
 * Outputs: Returns ``undefined`` after restoring the hidden review row.
 * How it works: Drops the in-memory File reference, clears input value, and disables consent.
 * Side effects: Updates DOM and releases the browser-selected File reference.
 * Failure behavior: Missing optional elements surface as implementation errors in tests.
 * Safety: Does not delete the user's source file or any completed app-owned intake.
 * Example: Cancel calls ``resetPendingIntake()`` before another selection.
 * Related proof: Frontend cancel and browser interaction tests.
 */
function resetPendingIntake(preserveFeedback = false) {
  pendingIntakeFile = null;
  document.querySelector("#intake-file-input").value = "";
  document.querySelector("#intake-review").hidden = true;
  document.querySelector("#intake-authorize-button").disabled = true;
  if (!preserveFeedback) {
    setIntakeFeedback("Choose one supported file to review.");
  }
}

/**
 * Purpose: Review one browser-selected file without transmitting bytes or a path.
 * Inputs: Native file-input change event.
 * Outputs: Returns ``undefined`` after displaying name, extension, and size.
 * How it works: Applies session extension/size hints, then retains one File in memory.
 * Side effects: Updates review DOM and in-memory pending selection only.
 * Failure behavior: Missing, empty, oversize, archive, or unsupported files show an error.
 * Safety: Client checks improve UX; server policy remains authoritative at authorization.
 * Example: Choosing ``part.stl`` reveals Authorize copy but sends no request.
 * Related proof: Frontend tests and server-side negative intake tests.
 */
function reviewSelectedIntakeFile(event) {
  const file = event.target.files?.[0] || null;
  if (!file || !activeIntakeSession) {
    resetPendingIntake();
    return;
  }
  const extensionMatch = file.name.toLowerCase().match(/(\.[a-z0-9]+)$/);
  const extension = extensionMatch ? extensionMatch[1] : "";
  const constraints = activeIntakeSession.constraints || {};
  if (!(constraints.allowedExtensions || []).includes(extension)) {
    resetPendingIntake(true);
    setIntakeFeedback("That file extension is not enabled for authorized intake.", "error");
    return;
  }
  if (!Number.isInteger(file.size) || file.size <= 0 || file.size > constraints.maxFileBytes) {
    resetPendingIntake(true);
    setIntakeFeedback("The selected file is empty or exceeds the intake size limit.", "error");
    return;
  }
  pendingIntakeFile = file;
  document.querySelector("#intake-review-name").textContent = file.name;
  document.querySelector("#intake-review-meta").textContent = `${extension.toUpperCase()} · ${formatIntakeBytes(file.size)}`;
  document.querySelector("#intake-review").hidden = false;
  document.querySelector("#intake-authorize-button").disabled = false;
  setIntakeFeedback("Review this file, then authorize one app-owned copy.");
}

/**
 * Purpose: Authorize and transfer the exact reviewed file through two guarded POSTs.
 * Inputs: In-memory File plus process-local session token/endpoints.
 * Outputs: Promise resolving after contained copy and full state refresh.
 * How it works: Posts path-free metadata, then sends File bytes as octet-stream once.
 * Side effects: May create one app-owned authorization, content file, and catalog record.
 * Failure behavior: Server/client rejection remains visible and selection can be retried.
 * Safety: Uses same-origin mode, omits credentials, sends no source path, and runs nothing.
 * Example: Selecting Authorize copy for ``part.stl`` creates quarantined intake only.
 * Related proof: API/server tests and live desktop/browser intake smoke.
 */
async function authorizePendingIntake() {
  if (!pendingIntakeFile || !activeIntakeSession || intakeBusy) {
    return;
  }
  intakeBusy = true;
  const file = pendingIntakeFile;
  const addButton = document.querySelector("#intake-add-button");
  const authorizeButton = document.querySelector("#intake-authorize-button");
  addButton.disabled = true;
  authorizeButton.disabled = true;
  setIntakeFeedback("Authorizing this file...");
  const commonOptions = {
    mode: "same-origin",
    credentials: "omit",
    cache: "no-store",
    redirect: "error",
  };
  try {
    const authorizationResponse = await fetch(activeIntakeSession.authorizeEndpoint, {
      ...commonOptions,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Makers-Anvil-Request-Token": activeIntakeSession.requestToken,
      },
      body: JSON.stringify({
        displayName: file.name,
        sizeBytes: file.size,
        modifiedUtc: new Date(file.lastModified).toISOString(),
      }),
    });
    const authorizationPayload = await authorizationResponse.json();
    if (!authorizationResponse.ok) {
      throw new Error(authorizationPayload.message || "File authorization was rejected.");
    }
    const authorizationId = authorizationPayload.authorization?.id;
    if (typeof authorizationId !== "string" || !authorizationId.startsWith("intake-auth-")) {
      throw new Error("The intake authorization response was invalid.");
    }
    const contentUrl = activeIntakeSession.contentEndpointTemplate.replace(
      "{authorizationId}",
      encodeURIComponent(authorizationId),
    );
    setIntakeFeedback("Copying into app-owned quarantine storage...");
    const contentResponse = await fetch(contentUrl, {
      ...commonOptions,
      method: "POST",
      headers: {
        "Content-Type": "application/octet-stream",
        "X-Makers-Anvil-Request-Token": activeIntakeSession.requestToken,
      },
      body: file,
    });
    const contentPayload = await contentResponse.json();
    if (!contentResponse.ok) {
      throw new Error(contentPayload.message || "File copy did not complete.");
    }
    resetPendingIntake(true);
    setIntakeFeedback("Copy complete. Content remains quarantined until later proof gates pass.", "success");
    showWorkbenchNotice("Authorized file copied into app-owned storage.");
    await loadState();
  } catch (error) {
    setIntakeFeedback(error instanceof Error ? error.message : "File intake failed.", "error");
  } finally {
    intakeBusy = false;
    addButton.disabled = !activeIntakeSession;
    authorizeButton.disabled = !pendingIntakeFile;
  }
}

/**
 * Purpose: Wire picker, review authorization, and cancel controls once.
 * Inputs: Existing intake controls from the semantic HTML shell.
 * Outputs: Returns ``undefined`` after registering event listeners.
 * How it works: Picker click selects locally; separate listeners review, authorize, or clear.
 * Side effects: Registers browser handlers and may open the native file chooser on click.
 * Failure behavior: Session/render logic keeps Add file disabled when the API is unavailable.
 * Safety: No drag/drop/paste/global listener exists and selection alone sends no request.
 * Example: Called once with other workbench controls before initial state load.
 * Related proof: Frontend control tests and live interaction smoke.
 */
function initializeIntakeControls() {
  const addButton = document.querySelector("#intake-add-button");
  const fileInput = document.querySelector("#intake-file-input");
  addButton.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", reviewSelectedIntakeFile);
  document.querySelector("#intake-authorize-button").addEventListener("click", authorizePendingIntake);
  document.querySelector("#intake-cancel-button").addEventListener("click", () => resetPendingIntake());
}

/**
 * Purpose: Render untrusted route metadata through DOM text nodes without executing steps.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderRoutePreview(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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
    empty.textContent = "No work plans available.";
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

/**
 * Purpose: Render logical output and proof plans while creation/open controls remain absent.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderOutputProof(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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
    empty.textContent = "No output proof available.";
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

/**
 * Purpose: Render path-redacted tool evidence and blocked software actions.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderToolDetection(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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

/**
 * Purpose: Render semantic invocation plans that contain no runnable command or handoff.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderToolDryRun(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
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
    empty.textContent = "No tool setup previews available.";
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

/**
 * Purpose: Render one-route gate evidence while authorization and execution stay disabled.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderExecutionGates(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderExecutionGates(state, response = {}) {
  const gates = response.schemaVersion ? response : state.executionGates || fallbackState.executionGates;
  const gateState = document.querySelector("#execution-gate-state");
  gateState.textContent = gates.claimState || "unknown";
  gateState.className = `badge ${claimClass(gateState.textContent)}`;
  const scope = gates.scope || {};
  const summary = gates.summary || {};
  document.querySelector("#execution-gate-scope").textContent = scope.routeId
    ? `${scope.routeId} · ${scope.maxConcurrentExecutions || 0} future slot`
    : "not proven";
  document.querySelector("#execution-gate-count").textContent = `${summary.evaluatedPlanCount || 0} evaluated · ${summary.outOfScopePlanCount || 0} out of scope`;
  document.querySelector("#execution-gate-progress").textContent = `${summary.satisfiedGateCount || 0}/${summary.requiredGateCount || 0} satisfied`;
  const safety = gates.safety || {};
  document.querySelector("#execution-gate-safety").textContent = safety.executionRequestCreated === false
    && safety.processStarted === false
    && safety.filesystemWritten === false
    ? "no request, process, or write"
    : "not proven";
  document.querySelector("#execution-gate-action").textContent = gates.executionAction?.enabledInApi === false
    && scope.executionEnabled === false
    ? "blocked"
    : "not proven";

  const target = document.querySelector("#execution-gate-list");
  target.replaceChildren();
  if (!gates.evaluations?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No in-scope execution gate evaluations available.";
    target.append(empty);
    return;
  }

  gates.evaluations.forEach((evaluation) => {
    const item = document.createElement("article");
    item.className = "execution-gate-item";
    const heading = document.createElement("div");
    heading.className = "execution-gate-head";
    const title = document.createElement("h3");
    title.textContent = evaluation.route.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(evaluation.claimState)}`;
    stateBadge.textContent = evaluation.claimState;
    heading.append(title, stateBadge);
    const tool = document.createElement("p");
    tool.className = "execution-gate-tool";
    tool.textContent = evaluation.tool ? `${evaluation.tool.label} · detected` : "Tool candidate · not proven";
    const gateList = document.createElement("ul");
    gateList.className = "execution-gate-matrix";
    evaluation.gates.forEach((gate) => {
      const gateItem = document.createElement("li");
      gateItem.className = gate.satisfied ? "satisfied" : "unsatisfied";
      gateItem.textContent = `${gate.label} · ${gate.claimState}`;
      gateList.append(gateItem);
    });
    const blockers = document.createElement("p");
    blockers.className = "execution-gate-blockers";
    blockers.textContent = `Blocked by: ${evaluation.readiness.blockers.join(", ")}`;
    item.append(heading, tool, gateList, blockers);
    target.append(item);
  });
}

/**
 * Purpose: Render logical request intent and empty audit plans without enabling controls.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderExecutionRequest(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderExecutionRequest(state, response = {}) {
  const request = response.schemaVersion ? response : state.executionRequestPreview || fallbackState.executionRequestPreview;
  const requestState = document.querySelector("#execution-request-state");
  requestState.textContent = request.claimState || "unknown";
  requestState.className = `badge ${claimClass(requestState.textContent)}`;
  document.querySelector("#execution-request-mode").textContent = request.mode || "not proven";
  const summary = request.summary || {};
  document.querySelector("#execution-request-count").textContent = `${summary.previewCount || 0} available · ${summary.persistedRequestCount || 0} saved`;
  document.querySelector("#execution-request-authorization").textContent = `${summary.acceptedAuthorizationCount || 0} accepted`;
  document.querySelector("#execution-request-audit").textContent = `${summary.writtenAuditEventCount || 0} written`;
  document.querySelector("#execution-request-action").textContent = summary.executionReadyCount === 0
    && request.actions?.execute?.enabledInApi === false
    ? "blocked"
    : "not proven";

  const target = document.querySelector("#execution-request-list");
  target.replaceChildren();
  if (!request.previews?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No execution request previews available.";
    target.append(empty);
    return;
  }

  // Intent contains logical references only. Text nodes preserve that boundary
  // and prevent intake display data from being interpreted as HTML.
  request.previews.forEach((preview) => {
    const item = document.createElement("article");
    item.className = "execution-request-item";
    const heading = document.createElement("div");
    heading.className = "execution-request-head";
    const title = document.createElement("h3");
    title.textContent = preview.operation.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(preview.claimState)}`;
    stateBadge.textContent = preview.claimState;
    heading.append(title, stateBadge);
    const intent = document.createElement("p");
    intent.className = "execution-request-intent";
    intent.textContent = `${preview.intent.source.logicalReference} → ${preview.intent.output.logicalDirectory}`;
    const authorization = document.createElement("p");
    authorization.textContent = preview.authorization.accepted ? "Authorization accepted" : "Authorization not accepted";
    const audit = document.createElement("p");
    audit.textContent = `${preview.audit.requiredEventTypes.length} required audit events · ${preview.audit.events.length} written`;
    const blockers = document.createElement("p");
    blockers.className = "execution-request-blockers";
    blockers.textContent = `Blocked by: ${preview.readiness.blockers.join(", ")}`;
    item.append(heading, intent, authorization, audit, blockers);
    target.append(item);
  });
}

/**
 * Purpose: Render path-redacted prepared jobs and unsignaled cancellation requests.
 * Inputs: Caller supplies ``state``, ``response``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderJobWorkspaces(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderJobWorkspaces(state, response = {}) {
  const catalog = response.schemaVersion ? response : state.jobWorkspaceCatalog || fallbackState.jobWorkspaceCatalog;
  const catalogState = document.querySelector("#job-workspace-state");
  catalogState.textContent = catalog.claimState || "unknown";
  catalogState.className = `badge ${claimClass(catalogState.textContent)}`;
  document.querySelector("#job-workspace-mode").textContent = catalog.mode || "not proven";
  const summary = catalog.summary || {};
  document.querySelector("#job-workspace-count").textContent = `${summary.preparedJobCount || 0} prepared · ${summary.invalidJobCount || 0} invalid`;
  document.querySelector("#job-cancellation-count").textContent = `${summary.cancellationRequestedCount || 0} requested`;
  document.querySelector("#job-workspace-location").textContent = catalog.jobsPath || "not proven";
  document.querySelector("#job-workspace-execution").textContent = summary.executionReadyCount === 0
    && catalog.actions?.execute?.enabledInApi === false
    ? "blocked"
    : "not proven";

  const target = document.querySelector("#job-workspace-list");
  target.replaceChildren();
  if (!catalog.jobs?.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No prepared job workspaces available.";
    target.append(empty);
    return;
  }

  // Runtime records are untrusted local data. Render logical identifiers as
  // text and never expose or reconstruct the private workspace path.
  catalog.jobs.forEach((item) => {
    const record = item.record;
    const cancellation = item.cancellation;
    const row = document.createElement("article");
    row.className = "job-workspace-item";
    const heading = document.createElement("div");
    heading.className = "job-workspace-head";
    const title = document.createElement("h3");
    title.textContent = record.operation.label;
    const stateBadge = document.createElement("span");
    stateBadge.className = `badge ${claimClass(record.claimState)}`;
    stateBadge.textContent = record.claimState;
    heading.append(title, stateBadge);
    const identity = document.createElement("p");
    identity.className = "job-workspace-identity";
    identity.textContent = `${record.id} · ${record.route.label}`;
    const location = document.createElement("p");
    location.className = "job-workspace-location";
    location.textContent = record.workspace.logicalRoot;
    const cancellationState = document.createElement("p");
    cancellationState.textContent = cancellation.state === "requested"
      ? "Cancellation requested · no process signal sent"
      : "Cancellation not requested · no process signal sent";
    const readiness = document.createElement("p");
    readiness.className = "job-workspace-blocked";
    readiness.textContent = "Prepared only · authorization, command, process, output, audit, and proof remain blocked";
    row.append(heading, identity, location, cancellationState, readiness);
    target.append(row);
  });
}

/**
 * Purpose: Summarize the selected input and expected output for the primary workbench. Untrusted file names remain text nodes, and missing evidence stays explicit.
 * Inputs: Caller supplies ``state``, ``health``, ``intake``, ``routePreview``, ``outputProof``.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderWorkbenchSummary(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderWorkbenchSummary(state, health, intake, routePreview, outputProof) {
  const catalog = intake.schemaVersion ? intake : state.intakeCatalog || fallbackState.intakeCatalog;
  const routes = routePreview.schemaVersion ? routePreview : state.routePreview || fallbackState.routePreview;
  const outputs = outputProof.schemaVersion ? outputProof : state.outputProof || fallbackState.outputProof;
  const record = catalog.records?.[0];
  const source = record?.source;
  const selectedState = document.querySelector("#selected-input-state");

  selectedState.textContent = record?.claimState || (source ? "staged" : "not proven");
  selectedState.className = `badge ${claimClass(selectedState.textContent)}`;
  document.querySelector("#selected-input-title").textContent = source?.displayName || "No source selected";
  document.querySelector("#selected-input-meta").textContent = source
    ? `${source.kind} · ${source.extension} · ${record?.privacy?.sourceContentStored === true ? "authorized app copy" : "metadata only"}`
    : "Choose and authorize one file";
  document.querySelector("#selected-input-visual").textContent = source?.extension
    ? source.extension.replace(".", "").slice(0, 6)
    : "--";

  const bundle = outputs.bundles?.[0];
  const route = routes.previews?.[0];
  document.querySelector("#expected-output-title").textContent = bundle?.output?.label
    || route?.route?.label
    || "No work plan selected";
  document.querySelector("#expected-output-meta").textContent = bundle
    ? `${bundle.artifacts?.length || 0} expected artifacts · proof incomplete`
    : route
      ? "Work plan selected · output bundle not available"
      : "Output remains preview-only";

  const liveState = health.claimState || state.claimState || "unknown";
  document.querySelector("#rail-health-label").textContent = liveState === "proven" ? "Local ready" : liveState;
}

/**
 * Purpose: Switch the stable command deck without changing application or server state.
 * Inputs: Caller supplies ``viewName``.
 * Outputs: Returns ``undefined`` after selecting one local command-deck view.
 * How it works: Hides nonmatching panels and synchronizes tab/rail accessibility state.
 * Side effects: Changes DOM visibility and ARIA attributes only.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Does not call an API or change application/runtime records.
 * Example: ``selectWorkbenchView("plans")`` shows the Plans panel.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function selectWorkbenchView(viewName) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.viewPanel !== viewName;
  });
  document.querySelectorAll("[data-workbench-view]").forEach((button) => {
    const active = button.dataset.workbenchView === viewName;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".rail-link").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === viewName && button.dataset.focus === "workbench");
  });
}

/**
 * Purpose: Focus one visible work zone and briefly expose the navigation destination.
 * Inputs: Caller supplies ``regionId``.
 * Outputs: Returns ``undefined`` after moving browser focus to one known region.
 * How it works: Finds the region, focuses/scrolls it, and briefly applies a visible focus class.
 * Side effects: Changes browser focus, scroll position, and a temporary CSS class.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: The region id comes from committed navigation mappings, not executable content.
 * Example: ``focusWorkbenchRegion("tools-zone")`` reveals the Tools area.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function focusWorkbenchRegion(regionId) {
  const target = document.querySelector(`#${regionId}`);
  if (!target) {
    return;
  }
  target.setAttribute("tabindex", "-1");
  target.focus({ preventScroll: true });
  target.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
  target.classList.add("is-focused");
  window.setTimeout(() => target.classList.remove("is-focused"), 900);
}

/**
 * Purpose: Wire read-only tabs, rail destinations, and quick-jump search once.
 * Inputs: No caller-supplied values; the function reads documented local DOM/API state.
 * Outputs: Returns ``undefined`` after registering local navigation listeners.
 * How it works: Connects tabs, rail buttons, and exact quick-jump terms to known workbench regions.
 * Side effects: Registers browser event listeners; it performs no request immediately.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Handlers only switch/focus views; operational maker actions remain disabled.
 * Example: Called once during module startup before the first ``loadState()``.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function initializeWorkbenchControls() {
  document.querySelectorAll("[data-workbench-view]").forEach((button) => {
    button.addEventListener("click", () => selectWorkbenchView(button.dataset.workbenchView));
  });

  document.querySelectorAll(".rail-link").forEach((button) => {
    button.addEventListener("click", () => {
      selectWorkbenchView(button.dataset.view || "workflow");
      document.querySelectorAll(".rail-link").forEach((item) => item.classList.toggle("is-active", item === button));
      window.requestAnimationFrame(() => focusWorkbenchRegion(button.dataset.focus));
    });
  });

  const destinations = {
    "workbench": ["workflow", "workbench"],
    "intake": ["workflow", "intake-zone"],
    "selected input": ["workflow", "selected-input-zone"],
    "tools": ["workflow", "tools-zone"],
    "plans": ["plans", "plan-surface"],
    "output proof": ["workflow", "proof-inspector"],
    "developer evidence": ["dev", "dev-surface"],
  };
  const search = document.querySelector("#command-search");
  const navigate = () => {
    const destination = destinations[search.value.trim().toLowerCase()];
    if (!destination) {
      return;
    }
    selectWorkbenchView(destination[0]);
    window.requestAnimationFrame(() => focusWorkbenchRegion(destination[1]));
    search.value = "";
  };
  search.addEventListener("change", navigate);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      navigate();
    }
  });
  initializeIntakeControls();
}

/**
 * Purpose: Compose one coherent dashboard frame from all read-only API snapshots.
 * Inputs: Caller supplies state/health/workspace, intake session/catalog, and all preview snapshots.
 * Outputs: Returns ``undefined`` after updating the owned workbench DOM region.
 * How it works: Reads the supplied schema-shaped snapshot, applies conservative fallbacks, and renders the matching view.
 * Side effects: Replaces or updates text and child nodes inside existing frontend regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: Untrusted metadata uses text nodes/textContent; this renderer never authorizes an action.
 * Example: ``renderState(fallbackState, {})`` renders a conservative empty/blocked example.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
function renderState(state, health, workspace = {}, layout = {}, intake = {}, intakeSession = {}, routePreview = {}, outputProof = {}, toolDetection = {}, toolDryRun = {}, executionGates = {}, executionRequest = {}, jobWorkspace = {}, experience = {}, activity = {}, capabilityMatrix = {}, containedPolicy = {}, containedCatalog = {}) {
  const completion = Number(state.completion?.realApp || 0);
  document.querySelector("#completion").textContent = `${completion.toFixed(4)}%`;
  document.querySelector("#completion-bar").style.width = `${Math.min(completion, 100)}%`;
  document.querySelector("#build-label").textContent = `${state.apiBuild || health.apiBuild || "unknown build"} · ${state.claimState}`;
  renderWorkspace(state, workspace);
  renderLayout(state, layout);
  renderIntake(state, intake, intakeSession);
  renderRoutePreview(state, routePreview);
  renderOutputProof(state, outputProof);
  renderToolDetection(state, toolDetection);
  renderToolDryRun(state, toolDryRun);
  renderExecutionGates(state, executionGates);
  renderExecutionRequest(state, executionRequest);
  renderJobWorkspaces(state, jobWorkspace);
  renderCapabilityMatrix(capabilityMatrix.schemaVersion ? capabilityMatrix : state.capabilityMatrix || fallbackState.capabilityMatrix);
  renderContainedExecutions(containedPolicy, containedCatalog.schemaVersion ? containedCatalog : state.containedExecutions || {}, intake, intakeSession.requestToken || "", loadState);
  renderWorkbenchExperience(experience, intakeSession.requestToken || "", loadState);
  renderActivityHistory(activity);
  renderWorkbenchSummary(state, health, intake, routePreview, outputProof);
  renderTracks(state.tracks || []);
  renderCapabilities(state.capabilities || []);
  renderBlocked(state.blockedActions || []);
}

/**
 * Purpose: Fetch every read snapshot/session together and fall back to conservative truth.
 * Inputs: No caller-supplied values; the function reads documented local DOM/API state.
 * Outputs: Returns a Promise that resolves after one complete dashboard render attempt.
 * How it works: Fetches all related GET endpoints together, validates responses, then renders one coherent frame.
 * Side effects: Performs loopback GET requests and updates existing DOM regions.
 * Failure behavior: Missing/invalid evidence is rendered as unknown, blocked, or empty; unexpected errors remain visible to the caller/fallback path.
 * Safety: This refresh sends GET only; intake POSTs require a separate user action.
 * Example: ``await loadState()`` refreshes the workbench from current loopback truth.
 * Related proof: tests/test_frontend_workbench.py and browser viewport checks.
 */
async function loadState() {
  // Fetch related records together so one refresh renders a coherent snapshot.
  try {
    const [stateResponse, healthResponse, workspaceResponse, layoutResponse, intakeResponse, intakeSessionResponse, routePreviewResponse, outputProofResponse, toolDetectionResponse, toolDryRunResponse, executionGatesResponse, executionRequestResponse, jobWorkspaceResponse, experienceResponse, activityResponse, capabilityMatrixResponse, containedPolicyResponse, containedCatalogResponse] = await Promise.all([
      fetch(stateUrl, { method: "GET", cache: "no-store" }),
      fetch(healthUrl, { method: "GET", cache: "no-store" }),
      fetch(workspaceUrl, { method: "GET", cache: "no-store" }),
      fetch(layoutUrl, { method: "GET", cache: "no-store" }),
      fetch(intakeUrl, { method: "GET", cache: "no-store" }),
      fetch(intakeSessionUrl, { method: "GET", cache: "no-store" }),
      fetch(routePreviewUrl, { method: "GET", cache: "no-store" }),
      fetch(outputProofUrl, { method: "GET", cache: "no-store" }),
      fetch(toolDetectionUrl, { method: "GET", cache: "no-store" }),
      fetch(toolDryRunUrl, { method: "GET", cache: "no-store" }),
      fetch(executionGatesUrl, { method: "GET", cache: "no-store" }),
      fetch(executionRequestUrl, { method: "GET", cache: "no-store" }),
      fetch(jobWorkspaceUrl, { method: "GET", cache: "no-store" }),
      fetch(workbenchExperienceUrl, { method: "GET", cache: "no-store" }),
      fetch(activityHistoryUrl, { method: "GET", cache: "no-store" }),
      fetch(capabilityMatrixUrl, { method: "GET", cache: "no-store" }),
      fetch(containedExecutionPolicyUrl, { method: "GET", cache: "no-store" }),
      fetch(containedExecutionCatalogUrl, { method: "GET", cache: "no-store" }),
    ]);
    if (!stateResponse.ok || !healthResponse.ok || !workspaceResponse.ok || !layoutResponse.ok || !intakeResponse.ok || !intakeSessionResponse.ok || !routePreviewResponse.ok || !outputProofResponse.ok || !toolDetectionResponse.ok || !toolDryRunResponse.ok || !executionGatesResponse.ok || !executionRequestResponse.ok || !jobWorkspaceResponse.ok || !experienceResponse.ok || !activityResponse.ok || !capabilityMatrixResponse.ok || !containedPolicyResponse.ok || !containedCatalogResponse.ok) {
      throw new Error("state request failed");
    }
    renderState(
      await stateResponse.json(),
      await healthResponse.json(),
      await workspaceResponse.json(),
      await layoutResponse.json(),
      await intakeResponse.json(),
      await intakeSessionResponse.json(),
      await routePreviewResponse.json(),
      await outputProofResponse.json(),
      await toolDetectionResponse.json(),
      await toolDryRunResponse.json(),
      await executionGatesResponse.json(),
      await executionRequestResponse.json(),
      await jobWorkspaceResponse.json(),
      await experienceResponse.json(),
      await activityResponse.json(),
      await capabilityMatrixResponse.json(),
      await containedPolicyResponse.json(),
      await containedCatalogResponse.json(),
    );
  } catch (error) {
    renderState(fallbackState, { apiBuild: "offline" });
  }
}

initializeWorkbenchControls();
document.querySelector("#refresh").addEventListener("click", loadState);
loadState();
