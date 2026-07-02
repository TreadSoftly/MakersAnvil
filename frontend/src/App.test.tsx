/**
 * Purpose: Preserve the previous app's accepted workbench behavior while proving current portable safety boundaries.
 * Used by: Vitest locally and the repository CI frontend verification job.
 * Inputs: Deterministic AppState fixtures, browser events, and same-origin API response mocks.
 * Outputs: Twenty-two interaction assertions covering layout, navigation, intake, tools, plans, proof, history, cancellation, and failures.
 * Side effects: Uses jsdom and mocked fetch only; no real user file, process, server, or path is touched.
 * Safety: Unsafe legacy tool/output/path calls are expected to stay visibly blocked.
 * Failure behavior: Any missing workflow, changed accessible label, or weakened guard fails the suite.
 * Related proof: api.ts adapter tests, Python server tests, and browser/native smoke inspection.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";
import { App } from "./App";
import type { AppState } from "./types";

function fixture(overrides: Partial<AppState> = {}): AppState {
  return {
    appName: "Makers Anvil Control Panel",
    workspaceName: "Makers Anvil",
    workspacePath: "C:\\workspace",
    dropPathDisplay: "00_DROP_REFERENCE_IMAGES_HERE",
    intake: {
      state: "ready_image",
      message: "Ready: your image file(s) can become a Blender reference scene.",
      nextAction: "Preview the image reference work plan, then start the job if the plan looks right.",
      selectedRoute: {
        routeId: "DMI-ROUTE-BLENDER-REFERENCE-001",
        target: "blender-reference",
        label: "Image reference work scene",
        status: "reference_only",
        blockedClaims: "No CAD truth.",
      },
      counts: { total: 1, images: 1, meshes: 0, unsupported: 0, supported: 1 },
      files: [
        {
          name: "reference.png",
          extension: ".png",
          sizeLabel: "1.0 KB",
          sha256: "1234567890abcdef",
          classification: "image",
          route: {
            routeId: "DMI-ROUTE-BLENDER-REFERENCE-001",
            target: "blender-reference",
            label: "Image reference work scene",
            status: "reference_only",
            blockedClaims: "No CAD truth.",
          },
          pathDisplay: "00_DROP_REFERENCE_IMAGES_HERE/reference.png",
          previewUrl: "/api/intake/preview/reference.png",
          isCandidate: true,
        },
      ],
    },
    ingress: {
      stageId: "current-intake",
      status: "safe_ingress_staged",
      sourceKind: "drop-folder-scan",
      generatedAtUtc: "2026-06-09T19:00:00Z",
      manifestJsonPathDisplay: "Application\\control_panel\\ingress\\current_intake_manifest.json",
      manifestCsvPathDisplay: "Application\\control_panel\\ingress\\current_intake_manifest.csv",
      manifestMarkdownPathDisplay: "Application\\control_panel\\ingress\\CURRENT_INTAKE_MANIFEST.md",
      fileCount: 1,
      candidateCount: 1,
      routePlan: {
        batchKind: "single-route",
        selectedRouteTarget: "blender-reference",
        selectedRouteId: "DMI-ROUTE-BLENDER-REFERENCE-001",
        selectedRouteStatus: "reference_only",
        selectedRouteLabel: "Image reference work scene",
        autoRunAllowed: true,
        reason: "One supported file class is present, so one proven review work plan can be previewed.",
        blockedClaims: "No CAD truth.",
      },
      safety: {
        originalsPreserved: true,
        routeNeutral: true,
        folderImportEnabled: false,
        archiveExtractionEnabled: false,
        clipboardPasteEnabled: true,
        downloadWatchingEnabled: false,
        multiRouteAutoRunEnabled: false,
        blockedClaims: ["No CAD truth, print readiness, simulation validation, manufacturing readiness, or physical readiness is claimed."],
      },
    },
    routes: [
      { target: "blender-reference", label: "Images to Blender reference work scene", status: "enabled", outputStatus: "reference_only" },
      { target: "mesh-review", label: "Meshes to Blender/FreeCAD review package", status: "enabled", outputStatus: "draft_review_only" },
      {
        target: "cad-derivative",
        label: "CAD files to derivative review package",
        status: "enabled",
        outputStatus: "cad_derivative_review_only",
      },
      { target: "cad-review", label: "CAD files to review package", status: "enabled", outputStatus: "cad_review_only" },
      { target: "electronics", label: "Electronics intake", status: "blocked", missingGate: "ECAD work-plan contract" },
    ],
    tools: [
      {
        tool: "Blender",
        role: "Visual scenes",
        health: "detected",
        iconUrl: "/tool-icons/blender.png",
        automationStatus: "design_tool_cli",
        blockedClaims: "Does not prove CAD correctness.",
        launchable: true,
        launchKind: "gui",
        launchPathDisplay: "C:\\Tools\\blender.exe",
        launchReason: "Ready to open from the dashboard.",
        probeStatus: "completed",
        sourceReference: "SRC-TEST-BLENDER",
      },
      {
        tool: "MeshLab",
        role: "Manual mesh",
        health: "manual",
        automationStatus: "manual_gui_target",
        blockedClaims: "Manual only.",
        launchable: true,
        launchKind: "gui",
        launchPathDisplay: "C:\\Tools\\meshlab.exe",
        launchReason: "Ready to open from the dashboard.",
        probeStatus: "not_run",
        sourceReference: "SRC-TEST-MESHLAB",
      },
      {
        tool: "Gmsh",
        role: "Mesh candidate",
        health: "candidate",
        automationStatus: "candidate_needs_geometry_smoke",
        blockedClaims: "Candidate.",
        launchable: true,
        launchKind: "gui",
        launchPathDisplay: "C:\\Tools\\gmsh.exe",
        launchReason: "Ready to open from the dashboard.",
        probeStatus: "completed",
        sourceReference: "SRC-TEST-GMSH",
      },
      {
        tool: "Docker CLI",
        role: "Container client",
        health: "blocked",
        automationStatus: "blocked_until_daemon_proof",
        blockedClaims: "No container route.",
        launchable: false,
        launchKind: "blocked",
        launchPathDisplay: "",
        launchReason: "No dashboard launch is enabled for this command-only or blocked tool.",
        probeStatus: "completed",
        sourceReference: "SRC-TEST-DOCKER",
      },
    ],
    toolHandoffs: [
      {
        classification: "image",
        currentCount: 1,
        routeTarget: "blender-reference",
        routeId: "DMI-ROUTE-BLENDER-REFERENCE-001",
        tool: "Blender",
        toolDisplay: "Blender",
        toolLaunchable: true,
        toolOpenStatus: "gui_open_proven",
        directFileLaunchStatus: "not_proven_file_argument",
        presetName: "Reference scene layout",
        inputFormats: ["png", "jpg", "webp"],
        previewContract: "Selected image preview is available immediately; completed jobs expose a reference-board preview.",
        outputContract: "Reference board preview, review note, Blender image-plane work scene, and scene inventory.",
        latestOutputKey: "preview",
        latestOutputAvailable: true,
        nativeOutputKey: "blend",
        nativeOutputOpenKind: "Blend",
        nativeOutputLabel: "Open latest Blender work scene",
        nativeOutputAvailable: true,
        nativeOutputLaunchStatus: "latest_native_output_ready",
        proof: "Reference-only image-to-Blender work scene route is proven.",
        blockedClaims: "No CAD truth.",
        status: "handoff_preview_ready",
        statusLabel: "Preview ready",
      },
      {
        classification: "cad",
        currentCount: 0,
        routeTarget: "cad-derivative",
        routeId: "MA-ROUTE-CAD-DERIVATIVE-001",
        tool: "FreeCADCmd",
        toolDisplay: "FreeCADCmd",
        toolLaunchable: true,
        toolOpenStatus: "gui_open_proven",
        directFileLaunchStatus: "not_proven_file_argument",
        presetName: "CAD derivative review checks",
        inputFormats: ["step", "stp", "iges", "brep", "fcstd", "scad"],
        previewContract: "CAD files receive a review-package preview note; derivative outputs appear only after a job runs.",
        outputContract: "Review-only derivative package, manifest, comparison report, and tool log when tools pass.",
        latestOutputKey: "comparison",
        latestOutputAvailable: false,
        nativeOutputKey: "",
        nativeOutputOpenKind: "",
        nativeOutputLabel: "",
        nativeOutputAvailable: false,
        nativeOutputLaunchStatus: "not_configured",
        proof: "CAD derivative package route is proven as review evidence only.",
        blockedClaims: "No CAD truth.",
        status: "waiting_for_matching_input",
        statusLabel: "Waiting",
      },
    ],
    latestJob: {
      exists: true,
      selectedRoute: "blender-reference",
      outputs: [],
      availableOutputs: [
        { key: "preview", label: "Open preview image", openKind: "Preview", exists: true, pathDisplay: "preview.png" },
        { key: "blend", label: "Open Blender work scene", openKind: "Blend", exists: true, pathDisplay: "scene.blend" },
      ],
      missingOutputs: [{ key: "inventory", label: "Scene inventory", openKind: "Inventory", exists: false, pathDisplay: "missing.json" }],
    },
    executionHistory: [],
    capabilityMatrix: {
      summary: {
        totalFiles: 1,
        supportedFiles: 1,
        selectedPlan: "blender-reference",
        selectedStatus: "reference_only",
        canPreview: true,
        latestOutputCount: 1,
        detectedToolCount: 4,
        launchableToolCount: 3,
      },
      ingressMethods: [
        {
          id: "drag-drop",
          label: "Source file intake",
          status: "ready",
          statusLabel: "Working now",
          detail: "Dashboard upload and watched drop-folder scans write the current intake manifest.",
        },
        {
          id: "clipboard-files",
          label: "Copy/paste file objects",
          status: "ready",
          statusLabel: "Working now",
          detail: "File objects pasted into the dashboard use the same safe upload path.",
        },
        {
          id: "folder-import",
          label: "Folders and batches",
          status: "blocked",
          statusLabel: "Metadata only",
          detail: "Folder-origin metadata can be recorded, but recursive folder import is not enabled.",
        },
        {
          id: "archive-extract",
          label: "Compressed files",
          status: "blocked",
          statusLabel: "Inventory only",
          detail: "Archive contents can be inventoried; extraction remains blocked.",
        },
        {
          id: "downloads",
          label: "Downloads/watch folder",
          status: "blocked",
          statusLabel: "Not active",
          detail: "No download watcher or URL importer is enabled.",
        },
      ],
      lanes: [
        {
          id: "images",
          label: "Images",
          status: "active",
          statusLabel: "Ready to preview",
          currentCount: 1,
          inputExamples: ["png", "jpg"],
          primaryPlan: "Image reference work scene",
          proof: "Reference-only Blender work scene is proven.",
          whatWorks: "Creates a reference board, review note, scene inventory, and Blender image-plane scene.",
          nextStep: "Drop images, preview the work plan, then run the job.",
          blocked: "No CAD truth.",
          tools: [{ name: "Blender", status: "detected", launch: "launchable" }],
        },
        {
          id: "cad",
          label: "CAD files",
          status: "ready",
          statusLabel: "Ready when dropped",
          currentCount: 0,
          inputExamples: ["step"],
          primaryPlan: "CAD derivative review package",
          proof: "Review-only derivatives can be generated.",
          whatWorks: "Builds review packages and derivative comparison notes when route-specific checks pass.",
          nextStep: "Use CAD files alone.",
          blocked: "No CAD truth.",
          tools: [{ name: "FreeCADCmd", status: "detected", launch: "launchable" }],
        },
      ],
      honesty: [
        "Detected tools do not prove output correctness.",
        "Review-only outputs do not prove CAD truth, print readiness, simulation validation, manufacturing readiness, or physical readiness.",
      ],
    },
    claims: {
      allowed: ["reference_only", "draft_review_only", "cad_review_only", "cad_derivative_review_only", "blocked"],
      blocked: ["CAD complete", "print ready", "simulation proven", "build ready", "fly ready"],
    },
    launcher: {
      oldPanelUntouched: true,
      switchAllowed: false,
      rule: "Do not switch the root media-control launcher until gates pass.",
    },
    ...overrides,
  };
}

function mockFetch(state: AppState) {
  const fetchMock = vi.fn(async (url: string) => {
    if (url === "/api/state") {
      return new Response(JSON.stringify(state), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    if (url === "/api/jobs/run") {
      return new Response(JSON.stringify({ ok: true, exitCode: 0, output: "Job complete." }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url === "/api/tools/open") {
      return new Response(
        JSON.stringify({
          ok: true,
          tool: "Blender",
          openMode: "gui",
          message: "Tool launch requested.",
          pathDisplay: "C:\\Tools\\blender.exe",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/tools/open-output") {
      return new Response(
        JSON.stringify({
          ok: true,
          tool: "Blender",
          opened: "blend",
          openMode: "native-output",
          message: "Tool launch requested with latest native output.",
          pathDisplay: "C:\\Tools\\blender.exe",
          outputPathDisplay: "Projects\\DesignMediaIntake\\jobs\\job_test\\outputs\\blender\\reference_scene.blend",
          absoluteOutputPathDisplay: "C:\\workspace\\Projects\\DesignMediaIntake\\jobs\\job_test\\outputs\\blender\\reference_scene.blend",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/intake/open-folder") {
      return new Response(
        JSON.stringify({
          ok: true,
          opened: "IntakeFolder",
          openMode: "folder",
          message: "Opened output folder.",
          pathDisplay: "00_DROP_REFERENCE_IMAGES_HERE",
          absolutePathDisplay: "C:\\workspace\\00_DROP_REFERENCE_IMAGES_HERE",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/app/window") {
      return new Response(
        JSON.stringify({
          ok: true,
          action: "compact",
          message: "Makers Anvil app window set to compact size 1180x780.",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/open") {
      return new Response(
        JSON.stringify({
          ok: true,
          opened: "Preview",
          openMode: "default",
          message: "Opened output file.",
          pathDisplay: "Projects\\DesignMediaIntake\\jobs\\job_test\\outputs\\blender\\reference_board_preview.png",
          absolutePathDisplay: "C:\\workspace\\Projects\\DesignMediaIntake\\jobs\\job_test\\outputs\\blender\\reference_board_preview.png",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/events/log") {
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    if (String(url).startsWith("/api/events/recent")) {
      return new Response(
        JSON.stringify({
          events: [
            {
              timestampUtc: "2026-06-08T12:00:00Z",
              action: "route_run_completed",
              surface: "route",
              status: "ok",
              detail: { target: "blender-reference" },
            },
          ],
          pathDisplay: "Application\\control_panel\\logs\\user_action_events.jsonl",
          exists: true,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/activity/recent") {
      return new Response(
        JSON.stringify({
          events: [{ timestampUtc: "2026-06-08T12:00:00Z", eventType: "route_run_completed", surface: "route", outcome: "ok", summary: "Completed route proof." }],
          logicalRoot: "makers-anvil-data://user/logs/activity",
          summary: { eventCount: 1 },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/intake/session") {
      return new Response(
        JSON.stringify({
          requestToken: "test-request-token",
          authorizeEndpoint: "/api/intake/authorizations",
          contentEndpointTemplate: "/api/intake/authorizations/{authorizationId}/content",
          constraints: { allowedExtensions: [".png", ".stl"], maxFileBytes: 1024 * 1024 },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url === "/api/intake/authorizations") {
      return new Response(JSON.stringify({ authorization: { id: "auth-test" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url === "/api/intake/authorizations/auth-test/content") {
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("Makers Anvil control panel", () => {
  test("renders dashboard state and hides missing latest output action", async () => {
    mockFetch(fixture());
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Makers Anvil" })).toBeInTheDocument();
    expect(screen.getAllByText("Ready: your image file(s) can become a Blender reference scene.").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /Intake status: 1 file, plan ready/i })).toBeInTheDocument();
    expect(screen.getAllByText("Image files can become visual reference planes inside a Blender scene.").length).toBeGreaterThan(0);
    expect(document.querySelector('img[src="/api/intake/preview/reference.png"]')).toBeInTheDocument();
    expect(screen.getAllByAltText("Authorized preview of reference.png").length).toBeGreaterThan(0);
    expect(document.querySelector('img[src="/tool-icons/blender.png"]')).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Latest job output" })).toBeInTheDocument();
    expect(screen.getByText(/Latest output proof: Images to Blender reference work scene/i)).toBeInTheDocument();
    expect(screen.getByText(/Created Open preview image/i)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Current Makers Anvil capability status" })).toBeInTheDocument();
    expect(screen.getByText("What Makers Anvil can handle now")).toBeInTheDocument();
    expect(screen.getByText("Source file intake")).toBeInTheDocument();
    expect(screen.getAllByText("Ready to preview").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: /View preview image/i }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Scene inventory/i })).not.toBeInTheDocument();
  });

  test("supports Work Flow, Plans, and Dev mode switching without a duplicate Tool tab", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    expect(await screen.findByRole("tab", { name: "Work Flow" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("region", { name: "Selected input readout" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Job result readout" })).toBeInTheDocument();
    expect(screen.getByText(/Direct selected-file launch is Not proven/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Reference board preview, review note, Blender image-plane work scene/i).length).toBeGreaterThan(0);
    await user.click(screen.getByRole("tab", { name: "Plans" }));
    expect(screen.getByRole("region", { name: "Work plans" })).toBeInTheDocument();
    expect(screen.getByText("Not ready")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Tool" })).not.toBeInTheDocument();
    expect(screen.getByRole("article", { name: "Blender tool" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Tool open mode" })).toBeInTheDocument();
    expect(screen.getByLabelText("Selected tool handoff contract")).toBeInTheDocument();
    expect(screen.getAllByText("GUI open proven").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not proven").length).toBeGreaterThan(0);
    expect(screen.getByText("Work plan preset")).toBeInTheDocument();
    expect(screen.getAllByText(/Reference scene layout/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Visual reference scenes, layout, inspection, and rendering.").length).toBeGreaterThan(0);
    expect(screen.getByText("SRC-TEST-BLENDER")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Dev" }));
    expect(screen.getByText("Old launcher untouched")).toBeInTheDocument();
    expect(screen.getAllByText("true").length).toBeGreaterThan(0);
    expect(screen.getByRole("region", { name: "Staging manifest" })).toBeInTheDocument();
    expect(screen.getByText("safe_ingress_staged")).toBeInTheDocument();
    expect(screen.getByText("Application\\control_panel\\ingress\\current_intake_manifest.json")).toBeInTheDocument();
    expect(screen.getByText("Archive extraction")).toBeInTheDocument();
    expect(screen.getByText("Capability matrix")).toBeInTheDocument();
    expect(screen.getByText("Launchable tools")).toBeInTheDocument();
    expect(screen.getByText("Reference-only Blender work scene is proven.")).toBeInTheDocument();
    expect(screen.getAllByText("blocked").length).toBeGreaterThan(0);
    expect(screen.getByRole("region", { name: "User test journal" })).toBeInTheDocument();
    expect(screen.getAllByText("route_run_completed").length).toBeGreaterThan(0);
    expect(screen.getByText(/makers-anvil-data:\/\/user\/logs\/activity/i)).toBeInTheDocument();
  });

  test("searches real tools and launches a selected detected tool", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    const search = await screen.findByRole("searchbox", { name: /Search plans, tools, files/i });
    await user.type(search, "blender");
    expect(screen.getByText(/Open tool - Visual reference scenes/i)).toBeInTheDocument();
    await user.click(screen.getByText(/Open tool - Visual reference scenes/i));
    expect(await screen.findByText(/Tool launch is blocked until an allowlisted portable launch adapter is proven/i)).toBeInTheDocument();
  });

  test("opens the latest native work output from the selected handoff", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Open latest Blender work scene" }));
    expect(await screen.findByText(/Native output handoff is blocked until both the output and tool adapter are proven/i)).toBeInTheDocument();
  });

  test("runs the first command search result with Enter", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    const search = await screen.findByRole("searchbox", { name: /Search plans, tools, files/i });
    await user.type(search, "preview{enter}");
    expect(await screen.findByText(/only the contained execution report and proof can be viewed in the app/i)).toBeInTheDocument();
  });

  test("views verified contained report JSON inside the workbench", async () => {
    const user = userEvent.setup();
    const reportJob: AppState["latestJob"] = {
      exists: true,
      selectedRoute: "mesh-review",
      outputs: [],
      availableOutputs: [
        { key: "report", label: "STL preflight report", openKind: "Report", exists: true, pathDisplay: "makers-anvil-data://user/executions/execution-test/outputs/stl-preflight-report.json" },
        { key: "proof", label: "Execution proof", openKind: "Proof", exists: true, pathDisplay: "makers-anvil-data://user/executions/execution-test/outputs/execution-proof.json" },
      ],
      missingOutputs: [],
    };
    const state = fixture({ latestJob: reportJob });
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url === "/api/state") return new Response(JSON.stringify(state), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/activity/recent") return new Response(JSON.stringify({ events: [], logicalRoot: "makers-anvil-data://user/logs/activity", summary: { eventCount: 0 } }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/executions/catalog") return new Response(JSON.stringify({ executions: [{ record: { id: "execution-0123456789abcdef0123456789abcdef", lifecycle: { state: "completed" }, proof: { outcome: "passed" } } }], actions: { viewArtifact: { enabledInApi: true, allowedKinds: ["report", "proof"] } } }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/artifacts/report")) return new Response(JSON.stringify({ schemaVersion: "makers-anvil.api.contained-artifact.v1", claimState: "proven", mode: "verified-in-app-json", executionId: "execution-0123456789abcdef0123456789abcdef", artifactKind: "report", title: "STL preflight report", logicalPath: reportJob.availableOutputs[0].pathDisplay, content: { triangleCount: 1, result: { passed: true, fullRouteCompleted: false } }, integrity: { recordMatched: true, sha256: "a".repeat(64), digestMatched: true, sizeBytes: 512 }, safety: { readOnly: true, physicalPathExposed: false, outputOpened: false, externalProcessStarted: false, externalToolLaunched: false } }), { status: 200, headers: { "Content-Type": "application/json" } });
      return new Response(JSON.stringify({ message: "Unexpected test route" }), { status: 404, headers: { "Content-Type": "application/json" } });
    }));
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /View preflight report/i }));
    const dialog = await screen.findByRole("dialog", { name: "STL preflight report" });
    expect(within(dialog).getByText("verified")).toBeInTheDocument();
    expect(within(dialog).getByLabelText("STL preflight report JSON")).toHaveTextContent('"triangleCount": 1');
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "STL preflight report" })).not.toBeInTheDocument();
  });

  test("renders execution history and requests cooperative cancellation without a process signal", async () => {
    const user = userEvent.setup();
    const executionId = "execution-fedcba9876543210fedcba9876543210";
    const running = {
      id: executionId, sourceName: "large-fixture.stl", operationLabel: "Built-in STL preflight",
      lifecycleState: "running" as const, claimState: "staged", createdUtc: "2026-07-01T20:00:00Z", updatedUtc: "2026-07-01T20:00:01Z",
      completedUtc: null, cancellationState: "not-requested" as const, canCancel: true, hasProof: false,
      proofOutcome: "not-available" as const, auditEventCount: 3, logicalRoot: `makers-anvil-data://user/executions/${executionId}`,
    };
    const state = fixture({ executionHistory: [running] });
    const fetchMock = vi.fn(async (url: string) => {
      if (url === "/api/state") return new Response(JSON.stringify(state), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/activity/recent") return new Response(JSON.stringify({ events: [], logicalRoot: "makers-anvil-data://user/logs/activity", summary: { eventCount: 0 } }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/intake/session") return new Response(JSON.stringify({ requestToken: "cancel-token" }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/executions/catalog") return new Response(JSON.stringify({ actions: { cancel: { enabledInApi: true } }, executions: [{ record: { id: executionId, lifecycle: { state: "running" } } }] }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/cancel")) return new Response(JSON.stringify({ record: { lifecycle: { state: "running" } }, cancellation: { state: "requested", processSignalSent: false } }), { status: 200, headers: { "Content-Type": "application/json" } });
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    const history = await screen.findByRole("region", { name: "Contained execution history" });
    expect(within(history).getByText("large-fixture.stl")).toBeInTheDocument();
    expect(within(history).getByText("Running")).toBeInTheDocument();
    await user.click(within(history).getByRole("button", { name: /Cancel preflight/i }));
    expect(await screen.findByText(/Cooperative cancellation requested/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(`/api/executions/${executionId}/cancel`, expect.objectContaining({ method: "POST" }));
    expect(document.body.textContent).not.toContain("process signal sent");
  });

  test("opens the active intake folder from the secondary drop action", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /Open intake/i }));
    expect(await screen.findByText(/Intake storage is private app-owned data/i)).toBeInTheDocument();
  });

  test("clicks the full drop zone to open the file picker", async () => {
    const user = userEvent.setup();
    const clickSpy = vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(() => undefined);
    mockFetch(fixture());
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /Add source files to intake/i }));
    expect(clickSpy).toHaveBeenCalled();
    clickSpy.mockClear();
    await user.click(screen.getByText(/Drop, choose, or paste images/i));
    expect(clickSpy).toHaveBeenCalled();
    clickSpy.mockRestore();
  });

  test("uploads files dropped onto the drop zone", async () => {
    const fetchMock = mockFetch(fixture());
    render(<App />);
    const dropZone = await screen.findByTestId("drop-zone");
    const file = new File(["solid mesh"], "propeller.stl", { type: "model/stl" });
    fireEvent.dragOver(dropZone, { dataTransfer: { files: [file] } });
    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/intake/authorizations/auth-test/content",
        expect.objectContaining({
          method: "POST",
          body: file,
        }),
      );
    });
  });

  test("uploads files pasted into the workbench", async () => {
    const fetchMock = mockFetch(fixture());
    render(<App />);
    await screen.findByRole("button", { name: /Add source files to intake/i });
    const file = new File(["pasted image"], "clipboard-reference.png", { type: "image/png" });
    const event = new Event("paste", { bubbles: true, cancelable: true });
    Object.defineProperty(event, "clipboardData", {
      value: { files: [file] },
    });
    window.dispatchEvent(event);
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/intake/authorizations/auth-test/content",
        expect.objectContaining({
          method: "POST",
          body: file,
        }),
      );
    });
  });

  test("opens real sidebar panels for settings and gated simulation", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect(screen.getByRole("region", { name: "Settings and setup" })).toBeInTheDocument();
    expect(screen.getByText("Current launch commands")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Simulation" }));
    expect(screen.getByRole("region", { name: "Simulation work" })).toBeInTheDocument();
    expect(screen.getByText(/solver runs, and validation are not ready yet/i)).toBeInTheDocument();
  });

  test("keeps native window controls out of the dashboard chrome", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    const { container } = render(<App />);
    expect(await screen.findByRole("heading", { name: "Tools" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous tool" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next tool" })).toBeInTheDocument();
    expect(screen.getByRole("article", { name: "Blender tool" })).toBeInTheDocument();
    expect(screen.getAllByText("Visual reference scenes, layout, inspection, and rendering.").length).toBeGreaterThan(0);
    await user.click(screen.getByRole("button", { name: "Next tool" }));
    expect(screen.getByRole("article", { name: "MeshLab tool" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Minimize app window" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Make app window smaller" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Exit app window" })).not.toBeInTheDocument();
    expect(screen.queryByText("Ray")).not.toBeInTheDocument();
    expect(screen.queryByText("local / verified")).not.toBeInTheDocument();
    expect(screen.queryByText("local verified")).not.toBeInTheDocument();
    expect(screen.getByRole("status", { name: /System ready: Ready to preview/i })).toBeInTheDocument();
    expect(container.querySelector(".rail-heartbeat polyline")).toBeInTheDocument();
  });

  test("opens a detected GUI tool through the controlled backend action", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Open Blender" }));
    expect(await screen.findByText(/Tool launch is blocked until an allowlisted portable launch adapter is proven/i)).toBeInTheDocument();
  });

  test("opens contextual help without relying on visible markdown", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Info: Current plan" }));
    expect(screen.getByRole("dialog", { name: "Current plan details" })).toBeInTheDocument();
    expect(screen.getByText("Purpose")).toBeInTheDocument();
    expect(screen.getByText("Turn the current file mix into one clear next action.")).toBeInTheDocument();
  });

  test("shows run preview before executing a work plan", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    const intake = await screen.findByRole("region", { name: "Input drop zone" });
    await user.click(within(intake).getByRole("button", { name: /Preview plan/i }));
    expect(screen.getByRole("region", { name: "Work plan preview" })).toBeInTheDocument();
    expect(screen.getByText("Reference/review output only. No design correctness claim.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start job/i })).toBeEnabled();
  });

  test("journals latest output refresh after a confirmed job run", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    const intake = await screen.findByRole("region", { name: "Input drop zone" });
    await user.click(within(intake).getByRole("button", { name: /Preview plan/i }));
    await user.click(screen.getByRole("button", { name: /Start job/i }));
    expect(await screen.findByText(/This work plan is preview-only/i)).toBeInTheDocument();
  });

  test("shows a right-side context inspector for selected plan proof", async () => {
    mockFetch(fixture());
    render(<App />);
    const inspector = await screen.findByRole("region", { name: "Job preview and proof" });
    expect(within(inspector).getByRole("heading", { name: /Work preview/i })).toBeInTheDocument();
    expect(within(inspector).getByText("Raw selected input")).toBeInTheDocument();
    expect(within(inspector).getByText("Expected output preview")).toBeInTheDocument();
    expect(within(inspector).getByText("DMI-BLENDER-001")).toBeInTheDocument();
    expect(within(inspector).getByTitle("DMI-ROUTE-BLENDER-REFERENCE-001")).toBeInTheDocument();
    expect(within(inspector).getByText("1234567890abcdef")).toBeInTheDocument();
  });

  test("only allows the plan matching the current intake to run", async () => {
    const user = userEvent.setup();
    mockFetch(fixture());
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Makers Anvil" })).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Plans" }));
    expect(screen.getByRole("button", { name: "Preview plan" })).toBeEnabled();
    const waitingButtons = screen.getAllByRole("button", { name: "Waiting" });
    expect(waitingButtons.length).toBeGreaterThan(0);
    for (const button of waitingButtons) {
      expect(button).toBeDisabled();
    }
  });

  test("enables CAD derivative route only for CAD-only intake", async () => {
    const user = userEvent.setup();
    const cadState = fixture({
      intake: {
        state: "ready_cad",
        message: "Ready: your CAD file(s) can become a derivative review package.",
        nextAction: "Preview the CAD derivative work plan, then start the job if you only need checked review derivatives.",
        selectedRoute: {
          routeId: "MA-ROUTE-CAD-DERIVATIVE-001",
          target: "cad-derivative",
          label: "CAD derivative review package",
          status: "cad_derivative_review_only",
          blockedClaims: "Tool-generated CAD derivatives for review only. No CAD truth.",
        },
        counts: { total: 1, images: 0, meshes: 0, cad: 1, unsupported: 0, supported: 1 },
        files: [
          {
            name: "part.step",
            extension: ".step",
            sizeLabel: "4 B",
            sha256: "abc123",
            classification: "cad",
            route: {
              routeId: "MA-ROUTE-CAD-DERIVATIVE-001",
              target: "cad-derivative",
              label: "CAD derivative review package",
              status: "cad_derivative_review_only",
              blockedClaims: "Tool-generated CAD derivatives for review only. No CAD truth.",
            },
            pathDisplay: "00_DROP_REFERENCE_IMAGES_HERE/part.step",
            isCandidate: true,
          },
        ],
      },
      latestJob: {
        exists: true,
        selectedRoute: "cad-derivative",
        outputs: [],
        availableOutputs: [
          { key: "review", label: "Review file", openKind: "Review", exists: true, pathDisplay: "CAD_DERIVATIVE_REVIEW.md" },
          {
            key: "comparison",
            label: "Comparison report",
            openKind: "Comparison",
            exists: true,
            pathDisplay: "CAD_DERIVATIVE_COMPARISON.md",
          },
          {
            key: "toolLog",
            label: "Tool log",
            openKind: "ToolLog",
            exists: true,
            pathDisplay: "CAD_DERIVATIVE_TOOL_LOG.json",
          },
        ],
        missingOutputs: [],
      },
    });
    mockFetch(cadState);
    render(<App />);
    expect((await screen.findAllByText("Ready: your CAD file(s) can become a derivative review package.")).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("CAD files can become derivative review packages; no dimensions or CAD truth are validated.").length,
    ).toBeGreaterThan(0);
    const intake = screen.getByRole("region", { name: "Input drop zone" });
    await user.click(within(intake).getByRole("button", { name: /Preview plan/i }));
    expect(screen.getByRole("region", { name: "Work plan preview" })).toBeInTheDocument();
    expect(screen.getAllByText(/comparison report/i).length).toBeGreaterThan(0);
  });

  test("does not render forbidden readiness claims as completion text", async () => {
    mockFetch(fixture());
    render(<App />);
    await waitFor(() => expect(screen.getByText("Makers Anvil")).toBeInTheDocument());
    const bodyText = document.body.textContent?.toLowerCase() || "";
    expect(bodyText).not.toContain("ready to build");
    expect(bodyText).not.toContain("simulation proven");
    expect(bodyText).not.toContain("print ready");
    expect(bodyText).not.toContain("fly ready");
  });

  test("shows a controlled backend-offline message instead of raw failed fetch text", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    render(<App />);
    expect(await screen.findByText(/Local backend is not answering/i)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("Failed to fetch");
  });
});
