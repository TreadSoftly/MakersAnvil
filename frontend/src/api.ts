/**
 * Purpose: Adapt the portable Makers Anvil API to the promoted previous-app React experience.
 * Used by: App.tsx for state refresh, authorized intake, contained STL preflight, and visible blockers.
 * Inputs: Same-origin current API records plus browser File objects selected by the user.
 * Outputs: The previous workbench's stable view model without exposing private filesystem paths.
 * Side effects: GET requests are read-only; upload and STL preflight use the current guarded POST contracts.
 * Safety: Tool launch, output opening, arbitrary routes, folders, archives, and machine-specific paths remain blocked.
 * Failure behavior: Invalid responses and blocked operations throw concise user-visible errors.
 * Related proof: React tests, current API tests, authorized-intake tests, and contained-execution tests.
 */

import type {
  AppState,
  CapabilityLane,
  ContainedArtifact,
  ExecutionHistoryEntry,
  IntakeFile,
  RecentEventsResponse,
  RouteCard,
  RouteInfo,
  RouteTarget,
  ToolHandoff,
  ToolHealth,
} from "./types";

type JsonRecord = Record<string, any>;

export type AppWindowAction = "minimize" | "compact" | "exit";

/** Read one JSON response and preserve the current backend's path-free error message. */
async function jsonFetch<T>(url: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store", credentials: "omit", ...options });
  } catch {
    throw new Error("Local backend is not answering. Restart the Makers Anvil application and try again.");
  }
  let payload: T & { error?: string; message?: string };
  try {
    payload = (await response.json()) as T & { error?: string; message?: string };
  } catch {
    throw new Error("The local Makers Anvil service returned an unreadable response.");
  }
  if (!response.ok) {
    throw new Error(payload.message || payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

/** Convert exact bytes into the compact size language used by the previous workbench. */
function sizeLabel(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "not proven";
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${bytes} B`;
}

/** Map current route identities to the previous workbench's retained navigation vocabulary. */
function routeTarget(routeId: string): RouteTarget {
  if (routeId === "image-reference-review") return "blender-reference";
  if (routeId === "mesh-to-toolpath") return "mesh-review";
  if (routeId === "cad-to-mesh") return "cad-review";
  return "auto";
}

/** Build one old-view route record from current path-redacted planning evidence. */
function routeInfo(preview?: JsonRecord): RouteInfo {
  const route = preview?.route || {};
  const readiness = preview?.readiness || {};
  const target = routeTarget(String(route.id || ""));
  return {
    routeId: String(route.id || "none"),
    target,
    label: String(route.label || "No work plan selected"),
    status: readiness.executionReady ? "enabled" : "preview_only",
    blockedClaims: Array.isArray(readiness.blockers) ? readiness.blockers.join("; ") : "Execution is not proven.",
  };
}

/** Normalize current intake kinds to the previous UI's broader presentation categories. */
function classification(kind: string): IntakeFile["classification"] {
  if (["image", "mesh", "cad", "document"].includes(kind)) return kind as IntakeFile["classification"];
  if (kind === "toolpath") return "slicer";
  return "unsupported";
}

/** Translate current authorized intake and route previews into selectable previous-app file cards. */
function adaptFiles(current: JsonRecord): IntakeFile[] {
  const previews = Array.isArray(current.routePreview?.previews) ? current.routePreview.previews : [];
  const records = Array.isArray(current.intakeCatalog?.records) ? current.intakeCatalog.records : [];
  return records.map((record: JsonRecord) => {
    const preview = previews.find((item: JsonRecord) => item.source?.intakeId === record.id);
    return {
      name: String(record.source?.displayName || "Unnamed source"),
      extension: String(record.source?.extension || ""),
      sizeLabel: sizeLabel(Number(record.source?.sizeBytes || 0)),
      sha256: String(record.storage?.sha256 || "not-proven"),
      classification: classification(String(record.source?.kind || "unsupported")),
      route: routeInfo(preview),
      pathDisplay: String(record.storage?.logicalReference || "makers-anvil-data://user/intake"),
      previewUrl: record.source?.kind === "image" && record.storage?.integrityVerified === true
        ? `/api/intake/previews/${encodeURIComponent(String(record.id || ""))}`
        : undefined,
      isCandidate: Boolean(preview),
      sourceKind: "authorized-app-copy",
      relativePathStatus: "private-source-path-not-stored",
    };
  });
}

/** Produce exact legacy route cards while preserving current execution blockers. */
function adaptRoutes(current: JsonRecord, selected: RouteInfo, files: IntakeFile[]): RouteCard[] {
  const isStl = files.some((file) => file.isCandidate && file.extension.toLowerCase() === ".stl");
  const definitions: Array<[RouteTarget, string]> = [
    ["auto", "Automatic plan selection"],
    ["blender-reference", "Image reference work"],
    ["mesh-review", "Contained STL preflight"],
    ["cad-review", "CAD review"],
    ["cad-derivative", "CAD derivative review"],
  ];
  return definitions.map(([target, label]) => {
    const selectedHere = selected.target === target;
    const enabled = target === "mesh-review" && selectedHere && isStl;
    return {
      target,
      label,
      status: enabled ? "enabled" : "blocked",
      routeId: selectedHere ? selected.routeId : target,
      outputStatus: enabled ? "structural proof only" : "not created",
      missingGate: enabled ? "explicit confirmation required" : selectedHere ? selected.blockedClaims : "No matching selected input",
    };
  });
}

const TOOL_ICON: Record<string, string> = {
  blender: "/tool-icons/blender.png",
  freecad: "/tool-icons/freecad.png",
  "ultimaker-cura": "/tool-icons/cura.png",
  prusaslicer: "/tool-icons/prusaslicer.png",
  orcaslicer: "/tool-icons/orcaslicer.png",
};

/** Reuse the prior tool carousel while sourcing only current path-redacted presence evidence. */
function adaptTools(current: JsonRecord): ToolHealth[] {
  const tools = Array.isArray(current.toolDetection?.tools) ? current.toolDetection.tools : [];
  return tools.map((tool: JsonRecord) => ({
    tool: String(tool.label || tool.id || "Unknown tool"),
    role: Array.isArray(tool.families) ? tool.families.join(", ") : "maker tool",
    health: tool.detection?.installed ? "detected" : "missing",
    iconUrl: TOOL_ICON[String(tool.id || "")] || "",
    launchable: false,
    launchKind: "blocked",
    launchPathDisplay: "private path not exposed",
    launchReason: "Detection is read-only. Tool launch requires a separately proven adapter.",
    automationStatus: "not proven",
    probeStatus: String(tool.claimState || "not proven"),
    sourceReference: "current portable tool catalog",
    blockedClaims: "No executable path, version command, selected-file handoff, or process launch is enabled.",
  }));
}

/** Join current capability lanes to prior tool-handoff cards without inventing launch readiness. */
function adaptHandoffs(current: JsonRecord, tools: ToolHealth[]): ToolHandoff[] {
  const lanes = Array.isArray(current.capabilityMatrix?.lanes) ? current.capabilityMatrix.lanes : [];
  return lanes.flatMap((lane: JsonRecord) => (lane.tools || []).map((candidate: JsonRecord) => {
    const tool = tools.find((item) => item.tool === candidate.label);
    return {
      classification: classification(String(lane.id || "unsupported")),
      currentCount: Number(lane.currentCount || 0),
      routeTarget: routeTarget(String(lane.route?.id || "")),
      routeId: String(lane.route?.id || "none"),
      tool: String(candidate.label || candidate.id || "Unknown tool"),
      toolDisplay: String(candidate.label || candidate.id || "Unknown tool"),
      toolLaunchable: false,
      toolOpenStatus: "blocked",
      directFileLaunchStatus: "not_proven_file_argument",
      presetName: `${lane.label || "Maker"} plan preview`,
      inputFormats: Array.isArray(lane.inputExamples) ? lane.inputExamples : [],
      previewContract: String(lane.whatWorks || "Metadata-only planning is available."),
      outputContract: "Outputs require contained execution and proof before opening.",
      latestOutputKey: "",
      latestOutputAvailable: false,
      nativeOutputKey: "",
      nativeOutputOpenKind: "",
      nativeOutputLabel: "No proven native output",
      nativeOutputAvailable: false,
      nativeOutputLaunchStatus: "blocked",
      proof: String(candidate.claimState || tool?.probeStatus || "not proven"),
      blockedClaims: String(lane.nextStep || "Tool handoff is not proven."),
      status: "preview_only",
      statusLabel: "Preview only",
    };
  }));
}

/** Translate current capability lanes into the prior app's comparison matrix. */
function adaptCapability(current: JsonRecord): AppState["capabilityMatrix"] {
  const matrix = current.capabilityMatrix || {};
  const lanes: CapabilityLane[] = (matrix.lanes || []).map((lane: JsonRecord) => ({
    id: String(lane.id || "unknown"),
    label: String(lane.label || "Unknown"),
    status: String(lane.status || "blocked"),
    statusLabel: String(lane.claimState || "not proven"),
    currentCount: Number(lane.currentCount || 0),
    inputExamples: Array.isArray(lane.inputExamples) ? lane.inputExamples : [],
    primaryPlan: String(lane.route?.label || "No plan"),
    proof: String(lane.whatWorks || "No proof"),
    whatWorks: String(lane.whatWorks || "Metadata inspection only."),
    nextStep: String(lane.nextStep || "Additional proof is required."),
    blocked: lane.executionReady ? "" : "Execution remains blocked.",
    tools: (lane.tools || []).map((tool: JsonRecord) => ({
      name: String(tool.label || tool.id || "Unknown tool"),
      status: String(tool.claimState || "not proven"),
      launch: "blocked",
    })),
  }));
  const records = current.intakeCatalog?.records || [];
  const tools = current.toolDetection?.tools || [];
  return {
    summary: {
      totalFiles: Number(records.length || 0),
      supportedFiles: Number(records.filter((record: JsonRecord) => record.source?.kind !== "unsupported").length),
      selectedPlan: String(current.routePreview?.previews?.[0]?.route?.label || "No plan selected"),
      selectedStatus: String(current.routePreview?.previews?.[0]?.claimState || "not proven"),
      canPreview: Number(current.routePreview?.summary?.previewCount || 0) > 0,
      latestOutputCount: Number(current.containedExecutions?.summary?.proofCount || 0),
      detectedToolCount: Number(tools.filter((tool: JsonRecord) => tool.detection?.installed).length),
      launchableToolCount: 0,
    },
    ingressMethods: (matrix.ingressMethods || []).map((method: JsonRecord) => ({
      id: String(method.id), label: String(method.label), status: String(method.claimState),
      statusLabel: method.enabled ? "available" : "blocked", detail: method.enabled ? "Available through guarded intake." : "Not enabled.",
    })),
    lanes,
    honesty: Array.isArray(matrix.honesty) ? matrix.honesty : [],
  };
}

/** Map the newest proof-bearing contained execution into bounded in-app artifacts. */
function adaptLatestJob(current: JsonRecord): AppState["latestJob"] {
  const executions = Array.isArray(current.containedExecutions?.executions) ? current.containedExecutions.executions : [];
  const latest = executions.find((item: JsonRecord) => {
    const lifecycle = item.record?.lifecycle?.state;
    return ["completed", "failed"].includes(lifecycle) && item.record?.proof;
  });
  if (!latest) return { exists: false, selectedRoute: "none", outputs: [], availableOutputs: [], missingOutputs: [] };
  const record = latest.record;
  const logicalRoot = String(record.workspace?.logicalRoot || `makers-anvil-data://user/executions/${record.id}`);
  const outputs = [
    { key: "report", label: "STL preflight report", openKind: "Report", exists: true, pathDisplay: String(record.proof.report?.logicalPath || `${logicalRoot}/outputs/stl-preflight-report.json`) },
    { key: "proof", label: "Execution proof", openKind: "Proof", exists: true, pathDisplay: `${logicalRoot}/outputs/execution-proof.json` },
  ];
  return { exists: true, selectedRoute: routeTarget(String(record.route?.id || "")), outputs, availableOutputs: outputs, missingOutputs: [] };
}

/**
 * Purpose: Convert strict path-redacted execution catalog items into compact workbench history rows.
 * Inputs: Current composed API state containing validated execution, cancellation, audit, and action records.
 * Outputs: Ordered presentation records with closed lifecycle values and no physical paths.
 * How it works: Rejects malformed ids/states, normalizes bounded fields, and derives cancellation/proof availability.
 * Side effects: None; this function transforms an in-memory response only.
 * Failure behavior: Invalid catalog items are omitted instead of becoming actionable UI rows.
 * Safety: Cancel is offered only for authorized/running work with no existing request and an enabled backend action.
 * Example: A completed proof record becomes one non-cancellable row with report/proof actions.
 * Related proof: api.test.ts history mapping and App.test.tsx cancellation interaction.
 */
function adaptExecutionHistory(current: JsonRecord): ExecutionHistoryEntry[] {
  const executions = Array.isArray(current.containedExecutions?.executions) ? current.containedExecutions.executions : [];
  const cancelEnabled = current.containedExecutions?.actions?.cancel?.enabledInApi === true;
  const allowedStates = new Set(["authorized", "running", "completed", "cancelled", "failed"]);
  return executions.flatMap((item: JsonRecord) => {
    const record = item.record || {};
    const lifecycleState = String(record.lifecycle?.state || "");
    if (!allowedStates.has(lifecycleState) || !/^execution-[a-f0-9]{32}$/.test(String(record.id || ""))) return [];
    const cancellationState = ["not-requested", "requested", "observed"].includes(String(item.cancellation?.state))
      ? String(item.cancellation.state) as ExecutionHistoryEntry["cancellationState"]
      : "not-requested";
    const proofOutcome = ["passed", "failed"].includes(String(record.proof?.outcome))
      ? String(record.proof.outcome) as ExecutionHistoryEntry["proofOutcome"]
      : "not-available";
    return [{
      id: String(record.id), sourceName: String(record.source?.displayName || "Authorized STL"),
      operationLabel: String(record.operation?.label || "Built-in STL preflight"),
      lifecycleState: lifecycleState as ExecutionHistoryEntry["lifecycleState"], claimState: String(record.claimState || "not proven"),
      createdUtc: String(record.createdUtc || ""), updatedUtc: String(record.updatedUtc || ""),
      completedUtc: typeof record.lifecycle?.completedUtc === "string" ? record.lifecycle.completedUtc : null,
      cancellationState, canCancel: cancelEnabled && ["authorized", "running"].includes(lifecycleState) && cancellationState === "not-requested",
      hasProof: Boolean(record.proof), proofOutcome,
      auditEventCount: Number(item.audit?.summary?.eventCount || 0),
      logicalRoot: String(record.workspace?.logicalRoot || `makers-anvil-data://user/executions/${record.id}`),
    }];
  });
}

/** Compose the complete previous-app view model from current portable backend truth. */
function adaptState(current: JsonRecord): AppState {
  const files = adaptFiles(current);
  const previews = Array.isArray(current.routePreview?.previews) ? current.routePreview.previews : [];
  const selected = routeInfo(previews[0]);
  const tools = adaptTools(current);
  const byKind = current.intakeCatalog?.summary?.byKind || {};
  const supported = files.filter((file) => file.classification !== "unsupported").length;
  return {
    appName: "Makers Anvil",
    workspaceName: "Makers Anvil",
    workspacePath: "makers-anvil-data://user",
    dropPathDisplay: "Portable app-owned intake",
    intake: {
      state: files.length ? (previews.length ? "preview_ready" : "needs_plan") : "waiting",
      message: files.length ? `${files.length} authorized app-owned source file(s).` : "Add one source file to begin.",
      nextAction: previews.length ? "Review the selected work plan and its blockers." : "Choose one supported file.",
      selectedRoute: selected,
      counts: {
        total: files.length,
        images: Number(byKind.image || 0), meshes: Number(byKind.mesh || 0), cad: Number(byKind.cad || 0),
        electronics: Number(byKind.electronics || 0), slicer: Number(byKind.toolpath || 0),
        simulation: Number(byKind.simulation || 0), documents: Number(byKind.document || 0),
        archives: 0, unsupported: files.length - supported, supported,
      },
      files,
    },
    ingress: {
      stageId: "authorized-portable-intake", status: String(current.intakeCatalog?.claimState || "not proven"),
      sourceKind: "browser-explicit-authorization", generatedAtUtc: new Date().toISOString(),
      manifestJsonPathDisplay: String(current.intakeCatalog?.recordsPath || "makers-anvil-data://user/intake/records"),
      manifestCsvPathDisplay: "not generated", manifestMarkdownPathDisplay: "not generated",
      fileCount: files.length, candidateCount: previews.length,
      routePlan: {
        batchKind: files.length === 1 ? "one-authorized-file" : "empty",
        selectedRouteTarget: selected.target, selectedRouteId: selected.routeId, selectedRouteStatus: selected.status,
        selectedRouteLabel: selected.label, autoRunAllowed: false,
        reason: "Current portable backend planning evidence.", blockedClaims: selected.blockedClaims,
      },
      safety: {
        originalsPreserved: true, routeNeutral: true, folderImportEnabled: false, archiveExtractionEnabled: false,
        clipboardPasteEnabled: true, downloadWatchingEnabled: false, multiRouteAutoRunEnabled: false,
        blockedClaims: ["folder import", "archive extraction", "automatic multi-route execution"],
      },
    },
    routes: adaptRoutes(current, selected, files),
    tools,
    toolHandoffs: adaptHandoffs(current, tools),
    latestJob: adaptLatestJob(current),
    executionHistory: adaptExecutionHistory(current),
    capabilityMatrix: adaptCapability(current),
    claims: {
      allowed: ["authorized app-owned intake", "read-only work plans", "contained STL structural preflight"],
      blocked: Array.isArray(current.blockedActions) ? current.blockedActions : [],
    },
    launcher: { oldPanelUntouched: true, switchAllowed: false, rule: "The promoted React UI uses only current portable services." },
  };
}

/** Fetch and adapt the current app snapshot into the promoted workbench contract. */
export async function getState(): Promise<AppState> {
  const payload = await jsonFetch<JsonRecord>("/api/state");
  // The promoted workbench owns this presentation contract. Accepting an already
  // adapted payload keeps component tests and future desktop bridges independent
  // from the lower-level portable API without weakening any mutation boundary.
  if (payload.intake?.files && Array.isArray(payload.routes) && Array.isArray(payload.tools)) {
    return payload as AppState;
  }
  return adaptState(payload);
}

/** Translate fixed server-authored activity into the prior Dev journal. */
export async function getRecentEvents(_limit = 30): Promise<RecentEventsResponse> {
  const activity = await jsonFetch<JsonRecord>("/api/activity/recent");
  return {
    events: (activity.events || []).map((event: JsonRecord) => ({
      timestampUtc: String(event.timestampUtc || ""), action: String(event.eventType || "activity"),
      surface: String(event.surface || "workbench"), status: String(event.outcome || "info"),
      detail: { summary: String(event.summary || ""), subjectId: String(event.subjectId || "") },
    })),
    pathDisplay: String(activity.logicalRoot || "makers-anvil-data://user/logs/activity"),
    exists: Number(activity.summary?.eventCount || 0) > 0,
  };
}

/** Keep UI-only interaction journaling local until a fixed event is server-authorized. */
export async function logUserAction(_event: { action: string; surface: string; status?: string; detail?: Record<string, unknown> }): Promise<{ ok: boolean }> {
  return { ok: false };
}

/**
 * Purpose: Authorize and run only the current built-in STL structural preflight.
 * Inputs: Mesh-review target plus an optional callback receiving generated execution identity.
 * Outputs: Terminal lifecycle, exit semantics, path-redacted message, and execution id.
 * How it works: Reads current source/session/policy, posts exact consent, emits identity, then posts Run.
 * Side effects: Creates and runs one app-owned contained preflight through guarded same-origin APIs.
 * Failure behavior: Missing STL, token, identity, policy, or API success throws a visible bounded error.
 * Safety: The callback exposes no physical path and the operation starts no external process or tool.
 * Example: Cancellation returns lifecycle ``cancelled`` with exit code two rather than fake failure proof.
 * Related proof: api.test.ts early-identity test and contained execution backend tests.
 */
export async function runRoute(
  target: RouteTarget,
  onAuthorized?: (execution: { id: string; sourceName: string }) => void,
): Promise<{ ok: boolean; exitCode: number; output: string; executionId: string; lifecycleState: string }> {
  if (target !== "mesh-review") throw new Error("This work plan is preview-only. Its contained execution adapter is not proven yet.");
  const [state, session, policy] = await Promise.all([
    jsonFetch<JsonRecord>("/api/state"), jsonFetch<JsonRecord>("/api/intake/session"), jsonFetch<JsonRecord>("/api/executions/policy"),
  ]);
  const source = (state.intakeCatalog?.records || []).find((record: JsonRecord) => record.source?.kind === "mesh" && record.source?.extension === ".stl");
  if (!source) throw new Error("Add one authorized STL before running the structural preflight.");
  const headers = { "Content-Type": "application/json", "X-Makers-Anvil-Request-Token": String(session.requestToken || "") };
  const authorization = await jsonFetch<JsonRecord>(String(policy.endpoints?.authorize || "/api/executions/authorizations"), {
    method: "POST", headers,
    body: JSON.stringify({ intakeId: source.id, routeId: policy.scope.routeId, operationId: policy.scope.operationId, accepted: true }),
  });
  const executionId = String(authorization.record?.id || "");
  if (!executionId) throw new Error("The STL preflight authorization did not create an execution record.");
  onAuthorized?.({ id: executionId, sourceName: String(authorization.record?.source?.displayName || "Authorized STL") });
  const result = await jsonFetch<JsonRecord>(String(policy.endpoints.runTemplate).replace("{executionId}", encodeURIComponent(executionId)), {
    method: "POST", headers: { "X-Makers-Anvil-Request-Token": String(session.requestToken || "") },
  });
  const lifecycleState = String(result.record?.lifecycle?.state || "failed");
  return {
    ok: lifecycleState === "completed", exitCode: lifecycleState === "completed" ? 0 : lifecycleState === "cancelled" ? 2 : 1,
    output: lifecycleState === "cancelled" ? "Contained STL structural preflight cancelled cooperatively." : "Contained STL structural preflight completed with path-redacted proof.",
    executionId, lifecycleState,
  };
}

/**
 * Purpose: Request cooperative cancellation for one generated nonterminal execution id.
 * Inputs: Anchored generated execution id selected from current path-redacted history.
 * Outputs: Current lifecycle, cancellation state, and explicit process-signal truth.
 * How it works: Rechecks the live catalog/action, obtains the process token, then posts a bodyless request.
 * Side effects: Replaces app-owned cancellation state; authorized work may finalize immediately as cancelled.
 * Failure behavior: Invalid, missing, terminal, or disabled candidates throw before a mutation request.
 * Safety: No signal, process handle, command, path, or external tool data is accepted or constructed.
 * Example: A running record returns ``requested`` while its read loop observes the request cooperatively.
 * Related proof: api.test.ts guarded POST test and test_contained_execution.py cancellation cases.
 */
export async function cancelExecution(executionId: string): Promise<{ lifecycleState: string; cancellationState: string; processSignalSent: boolean }> {
  if (!/^execution-[a-f0-9]{32}$/.test(executionId)) throw new Error("The contained execution id is invalid.");
  const [session, catalog] = await Promise.all([jsonFetch<JsonRecord>("/api/intake/session"), jsonFetch<JsonRecord>("/api/executions/catalog")]);
  const candidate = (catalog.executions || []).find((item: JsonRecord) => item.record?.id === executionId);
  if (catalog.actions?.cancel?.enabledInApi !== true || !candidate || !["authorized", "running"].includes(candidate.record?.lifecycle?.state)) {
    throw new Error("This contained execution is no longer cancellable.");
  }
  const result = await jsonFetch<JsonRecord>(`/api/executions/${encodeURIComponent(executionId)}/cancel`, {
    method: "POST", headers: { "X-Makers-Anvil-Request-Token": String(session.requestToken || "") },
  });
  return {
    lifecycleState: String(result.record?.lifecycle?.state || "unknown"),
    cancellationState: String(result.cancellation?.state || "unknown"),
    processSignalSent: result.cancellation?.processSignalSent === true,
  };
}

/** Fetch one closed, verified JSON artifact for display inside the workbench. */
export async function openOutput(kind: string, requestedExecutionId = ""): Promise<ContainedArtifact> {
  const artifactKind = kind.toLowerCase();
  if (!(["report", "proof"] as string[]).includes(artifactKind)) {
    throw new Error("Output opening is blocked; only the contained execution report and proof can be viewed in the app.");
  }
  const catalog = await jsonFetch<JsonRecord>("/api/executions/catalog");
  const viewer = catalog.actions?.viewArtifact;
  if (viewer?.enabledInApi !== true || !Array.isArray(viewer.allowedKinds) || !viewer.allowedKinds.includes(artifactKind)) {
    throw new Error("Verified in-app artifact viewing is not enabled by the current backend.");
  }
  const latest = (catalog.executions || []).find((item: JsonRecord) => {
    const lifecycle = item.record?.lifecycle?.state;
    const requested = requestedExecutionId ? item.record?.id === requestedExecutionId : true;
    return requested && ["completed", "failed"].includes(lifecycle) && item.record?.proof;
  });
  const executionId = String(latest?.record?.id || "");
  if (!executionId) throw new Error("No verified execution artifact is available yet.");
  const endpoint = `/api/executions/${encodeURIComponent(executionId)}/artifacts/${encodeURIComponent(artifactKind)}`;
  return jsonFetch<ContainedArtifact>(endpoint);
}

/** Explain the app-owned intake boundary without exposing or opening a private path. */
export async function openIntakeFolder(): Promise<{ ok: boolean; opened: string; openMode: string; message: string; pathDisplay: string }> {
  throw new Error("Intake storage is private app-owned data. Folder opening is not enabled yet.");
}

/** Keep old app-window commands absent from the portable pywebview shell. */
export async function controlAppWindow(_action: AppWindowAction): Promise<{ ok: boolean; action: AppWindowAction; message: string }> {
  throw new Error("Window commands are managed by the native application shell.");
}

/** Keep tool launch visibly blocked while retaining the prior tool carousel. */
export async function openTool(_tool: string): Promise<{ ok: boolean; tool: string; openMode: string; message: string; pathDisplay: string }> {
  throw new Error("Tool launch is blocked until an allowlisted portable launch adapter is proven.");
}

/** Keep direct output-to-tool handoff blocked. */
export async function openToolOutput(_tool: string, _outputKey: string): Promise<{ ok: boolean; tool: string; opened: string; openMode: string; message: string; pathDisplay: string; outputPathDisplay: string; absoluteOutputPathDisplay: string }> {
  throw new Error("Native output handoff is blocked until both the output and tool adapter are proven.");
}

/** Authorize and copy one exact browser File into current portable quarantine storage. */
export async function uploadFiles(files: FileList | File[]): Promise<unknown> {
  const selected = Array.from(files);
  if (selected.length !== 1) throw new Error("Makers Anvil currently accepts exactly one file at a time.");
  const file = selected[0];
  const session = await jsonFetch<JsonRecord>("/api/intake/session");
  const extension = file.name.toLowerCase().match(/(\.[a-z0-9]+)$/)?.[1] || "";
  if (!(session.constraints?.allowedExtensions || []).includes(extension)) throw new Error("That file extension is not enabled for intake.");
  if (file.size <= 0 || file.size > Number(session.constraints?.maxFileBytes || 0)) throw new Error("The selected file is empty or exceeds the intake limit.");
  const headers = { "Content-Type": "application/json", "X-Makers-Anvil-Request-Token": String(session.requestToken || "") };
  const authorized = await jsonFetch<JsonRecord>(String(session.authorizeEndpoint), {
    method: "POST", headers,
    body: JSON.stringify({ displayName: file.name, sizeBytes: file.size, modifiedUtc: new Date(file.lastModified).toISOString() }),
  });
  const authorizationId = String(authorized.authorization?.id || "");
  if (!authorizationId) throw new Error("The file authorization response was incomplete.");
  return jsonFetch(String(session.contentEndpointTemplate).replace("{authorizationId}", encodeURIComponent(authorizationId)), {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream", "X-Makers-Anvil-Request-Token": String(session.requestToken || "") },
    body: file,
  });
}
