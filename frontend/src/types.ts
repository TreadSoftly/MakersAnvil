/**
 * Purpose: Declare the presentation contracts consumed by the promoted Makers Anvil React workbench.
 * Used by: App.tsx, api.ts, and component tests for compile-time agreement on visible state.
 * Inputs: No runtime input; TypeScript checks values supplied by adapters and test fixtures.
 * Outputs: Interfaces and unions for intake, routes, tools, proof, activity, capabilities, and app state.
 * Side effects: None because type declarations are erased from the production JavaScript bundle.
 * Safety: Explicit fields make missing blockers and proof status visible during development.
 * Failure behavior: Contract drift fails TypeScript compilation before a package can be produced.
 * Related proof: npm build, App.test.tsx, and the backend-to-view adapter in api.ts.
 */

export type RouteTarget = "auto" | "blender-reference" | "mesh-review" | "cad-review" | "cad-derivative";

export interface RouteInfo {
  routeId: string;
  target: string;
  label: string;
  status: string;
  blockedClaims: string;
}

export interface IntakeFile {
  name: string;
  extension: string;
  sizeLabel: string;
  sha256: string;
  classification: "image" | "mesh" | "cad" | "electronics" | "slicer" | "simulation" | "document" | "archive" | "unsupported";
  route: RouteInfo;
  pathDisplay: string;
  previewUrl?: string;
  isCandidate: boolean;
  sourceKind?: string;
  originalRelativePath?: string;
  topFolder?: string;
  relativePathStatus?: string;
  archiveInventory?: {
    archiveInventoryStatus: string;
    archiveFormat: string;
    archiveEntryCount: number;
    archiveUnsafeEntryCount: number;
    archiveTotalUncompressedBytes: number;
    archiveTotalUncompressedSizeLabel: string;
    archiveLargestEntryBytes: number;
    archiveLargestEntrySizeLabel: string;
    archiveNestedArchiveCount: number;
    archiveHasEncryptedEntries: boolean;
    archiveInventoryNote: string;
    archiveEntriesPreview: Array<Record<string, unknown>>;
  };
}

export interface IntakeState {
  state: string;
  message: string;
  nextAction: string;
  selectedRoute: RouteInfo;
  counts: {
    total: number;
    images: number;
    meshes: number;
    cad?: number;
    electronics?: number;
    slicer?: number;
    simulation?: number;
    documents?: number;
    archives?: number;
    unsupported: number;
    supported: number;
  };
  files: IntakeFile[];
}

export interface IngressSummary {
  stageId: string;
  status: string;
  sourceKind: string;
  generatedAtUtc: string;
  manifestJsonPathDisplay: string;
  manifestCsvPathDisplay: string;
  manifestMarkdownPathDisplay: string;
  fileCount: number;
  candidateCount: number;
  routePlan: {
    batchKind: string;
    selectedRouteTarget: string;
    selectedRouteId: string;
    selectedRouteStatus: string;
    selectedRouteLabel: string;
    autoRunAllowed: boolean;
    reason: string;
    blockedClaims: string;
  };
  safety: {
    originalsPreserved: boolean;
    routeNeutral: boolean;
    folderImportEnabled: boolean;
    archiveExtractionEnabled: boolean;
    clipboardPasteEnabled: boolean;
    downloadWatchingEnabled: boolean;
    multiRouteAutoRunEnabled: boolean;
    blockedClaims: string[];
  };
  archiveInventory?: {
    archiveCount: number;
    inventoriedArchiveCount: number;
    unsafeArchiveCount: number;
    unsafeEntryCount: number;
    nestedArchiveCount: number;
    encryptedArchiveCount: number;
    totalEntries: number;
    totalUncompressedBytes: number;
    totalUncompressedSizeLabel: string;
    extractionEnabled: boolean;
    note: string;
  };
}

export interface RouteCard {
  target: string;
  label: string;
  status: "enabled" | "blocked";
  routeId?: string;
  outputStatus?: string;
  missingGate?: string;
}

export interface ToolHealth {
  tool: string;
  role: string;
  health: "detected" | "manual" | "candidate" | "blocked" | "missing";
  iconUrl?: string;
  launchable: boolean;
  launchKind: string;
  launchPathDisplay: string;
  launchReason: string;
  automationStatus: string;
  probeStatus: string;
  sourceReference: string;
  blockedClaims: string;
}

export interface ToolHandoff {
  classification: IntakeFile["classification"];
  currentCount: number;
  routeTarget: string;
  routeId: string;
  tool: string;
  toolDisplay: string;
  toolLaunchable: boolean;
  toolOpenStatus: string;
  directFileLaunchStatus: string;
  presetName: string;
  inputFormats: string[];
  previewContract: string;
  outputContract: string;
  latestOutputKey: string;
  latestOutputAvailable: boolean;
  nativeOutputKey: string;
  nativeOutputOpenKind: string;
  nativeOutputLabel: string;
  nativeOutputAvailable: boolean;
  nativeOutputLaunchStatus: string;
  proof: string;
  blockedClaims: string;
  status: string;
  statusLabel: string;
}

export interface LatestOutput {
  key: string;
  label: string;
  openKind: string;
  exists: boolean;
  pathDisplay: string;
}

export interface LatestJob {
  exists: boolean;
  selectedRoute: string;
  outputs: LatestOutput[];
  availableOutputs: LatestOutput[];
  missingOutputs: LatestOutput[];
}

export interface ContainedArtifact {
  schemaVersion: string;
  claimState: string;
  mode: "verified-in-app-json";
  executionId: string;
  artifactKind: "report" | "proof";
  title: string;
  logicalPath: string;
  content: Record<string, unknown>;
  integrity: { recordMatched: boolean; sha256: string; digestMatched: boolean; sizeBytes: number };
  safety: { readOnly: boolean; physicalPathExposed: boolean; outputOpened: boolean; externalProcessStarted: boolean; externalToolLaunched: boolean };
}

export type ExecutionLifecycleState = "authorized" | "running" | "completed" | "cancelled" | "failed";

export interface ExecutionHistoryEntry {
  id: string;
  sourceName: string;
  operationLabel: string;
  lifecycleState: ExecutionLifecycleState;
  claimState: string;
  createdUtc: string;
  updatedUtc: string;
  completedUtc: string | null;
  cancellationState: "not-requested" | "requested" | "observed";
  canCancel: boolean;
  hasProof: boolean;
  proofOutcome: "passed" | "failed" | "not-available";
  auditEventCount: number;
  logicalRoot: string;
}

export interface CapabilityToolRef {
  name: string;
  status: string;
  launch: string;
}

export interface CapabilityLane {
  id: string;
  label: string;
  status: string;
  statusLabel: string;
  currentCount: number;
  inputExamples: string[];
  primaryPlan: string;
  proof: string;
  whatWorks: string;
  nextStep: string;
  blocked: string;
  tools: CapabilityToolRef[];
}

export interface CapabilityIngressMethod {
  id: string;
  label: string;
  status: string;
  statusLabel: string;
  detail: string;
}

export interface CapabilityMatrix {
  summary: {
    totalFiles: number;
    supportedFiles: number;
    selectedPlan: string;
    selectedStatus: string;
    canPreview: boolean;
    latestOutputCount: number;
    detectedToolCount: number;
    launchableToolCount: number;
  };
  ingressMethods: CapabilityIngressMethod[];
  lanes: CapabilityLane[];
  honesty: string[];
}

export interface UserActionEvent {
  timestampUtc: string;
  action: string;
  surface: string;
  status: string;
  detail: Record<string, unknown>;
}

export interface RecentEventsResponse {
  events: UserActionEvent[];
  pathDisplay: string;
  exists: boolean;
}

export interface AppState {
  appName: string;
  workspaceName: string;
  workspacePath: string;
  dropPathDisplay: string;
  intake: IntakeState;
  ingress: IngressSummary;
  routes: RouteCard[];
  tools: ToolHealth[];
  toolHandoffs: ToolHandoff[];
  latestJob: LatestJob;
  executionHistory: ExecutionHistoryEntry[];
  capabilityMatrix: CapabilityMatrix;
  claims: {
    allowed: string[];
    blocked: string[];
  };
  launcher: {
    oldPanelUntouched: boolean;
    switchAllowed: boolean;
    rule: string;
  };
}
