/**
 * Purpose: Render the promoted Makers Anvil workbench, navigation, tools, plans, proof, and settings experience.
 * Used by: main.tsx as the single React application root in browser and native desktop modes.
 * Inputs: Portable API view-model records plus explicit keyboard, pointer, drop, paste, and file-picker actions.
 * Outputs: Accessible React regions, dialogs, notices, previews, and command controls matching the accepted prior app.
 * Side effects: Refreshes local state and delegates guarded intake or preflight requests through api.ts.
 * Safety: Private paths, arbitrary commands, external tool launch, output opening, folders, and archives stay blocked.
 * Failure behavior: Adapter failures become visible notices while the last coherent view remains inspectable.
 * Related proof: App.test.tsx, test_frontend_workbench.py, and browser/native smoke evidence.
 */

import {
  Activity,
  AlertTriangle,
  Bell,
  Box,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircuitBoard,
  ClipboardList,
  Cpu,
  Database,
  Download,
  Eye,
  ExternalLink,
  FileText,
  FolderOpen,
  Home,
  ImageIcon,
  Layers3,
  Loader2,
  Package,
  Play,
  Printer,
  RefreshCw,
  Route,
  Search,
  Settings,
  SlidersHorizontal,
  Upload,
  Wind,
  Wrench,
  X,
} from "lucide-react";
import { type ChangeEvent, type DragEvent, type ReactNode, type RefObject, useEffect, useMemo, useRef, useState } from "react";
import {
  getRecentEvents,
  getState,
  logUserAction,
  openIntakeFolder,
  openOutput,
  openTool,
  openToolOutput,
  runRoute,
  uploadFiles,
} from "./api";
import { ContextHelp, type HelpContent } from "./components/ContextHelp";
import { ModeTabs } from "./components/ModeTabs";
import { StatusPill } from "./components/StatusPill";
import type {
  AppState,
  CapabilityLane,
  IntakeFile,
  IntakeState,
  LatestJob,
  RouteCard,
  RouteTarget,
  ToolHandoff,
  ToolHealth,
  UserActionEvent,
} from "./types";

const routeTargets: RouteTarget[] = ["auto", "blender-reference", "mesh-review", "cad-review", "cad-derivative"];

type SearchTarget =
  | { type: "file"; name: string }
  | { type: "route"; target: string }
  | { type: "tool"; tool: string }
  | { type: "output"; openKind: string }
  | { type: "mode"; mode: "goal" | "plans" | "granular" };

type RailSection = "Workbench" | "Intake" | "Plans" | "Tools" | "Files" | "Components" | "Simulation" | "Outputs" | "Settings";
type ToolLaunchMode = "tool-only" | "selected-input" | "work-plan";

interface SearchResult {
  id: string;
  group: string;
  label: string;
  detail: string;
  target: SearchTarget;
}

/** Coordinate workbench state, explicit user actions, and all visible application regions. */
export function App() {
  const [state, setState] = useState<AppState | null>(null);
  const [activeMode, setActiveMode] = useState("goal");
  const [selectedFileName, setSelectedFileName] = useState("");
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [previewTarget, setPreviewTarget] = useState<RouteTarget | "">("");
  const [events, setEvents] = useState<UserActionEvent[]>([]);
  const [eventLogPath, setEventLogPath] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeRailSection, setActiveRailSection] = useState<RailSection>("Workbench");
  const [railPanelSection, setRailPanelSection] = useState<RailSection | "">("");
  const [railExpanded, setRailExpanded] = useState(false);
  const [selectedToolName, setSelectedToolName] = useState("");
  const filePickerRef = useRef<HTMLInputElement | null>(null);
  const appLoadedLoggedRef = useRef(false);

  async function refresh() {
    setError("");
    const nextState = await getState();
    setState(nextState);
    const firstCandidate = nextState.intake.files.find((file) => file.isCandidate);
    setSelectedFileName((current) => {
      if (current && nextState.intake.files.some((file) => file.name === current)) {
        return current;
      }
      return firstCandidate?.name || "";
    });
    return nextState;
  }

  useEffect(() => {
    refresh()
      .then(() => {
        if (!appLoadedLoggedRef.current) {
          appLoadedLoggedRef.current = true;
          recordAction("app_loaded", { app: "Makers Anvil" }, "ok", "workbench");
        }
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
    refreshEvents().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!notice) return undefined;
    const timeout = window.setTimeout(() => setNotice(""), 6500);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  async function refreshEvents() {
    const response = await getRecentEvents(25);
    setEvents(response.events);
    setEventLogPath(response.pathDisplay);
  }

  function recordAction(
    action: string,
    detail: Record<string, unknown> = {},
    status: "info" | "ok" | "fail" | "blocked" = "info",
    surface = "workbench",
  ) {
    logUserAction({ action, surface, status, detail })
      .then(refreshEvents)
      .catch(() => undefined);
  }

  async function handleRefreshClick() {
    recordAction("refresh_clicked", {}, "info", "topbar");
    await refresh();
    await refreshEvents().catch(() => undefined);
  }

  async function handleRun(target: RouteTarget) {
    setBusy(true);
    setError("");
    recordAction("route_run_started", { target }, "info", "route");
    try {
      const result = await runRoute(target);
      setLog((current) => [`${target}: exit ${result.exitCode}`, result.output, ...current].filter(Boolean));
      const refreshed = await refresh();
      if (!result.ok) {
        setError(`Job failed with exit code ${result.exitCode}. Open Dev for captured output.`);
        recordAction("route_run_completed", { target, exitCode: result.exitCode }, "fail", "route");
      } else {
        const jobLabel = latestJobPlanLabel(refreshed.latestJob, refreshed.routes, target);
        const outputCount = refreshed.latestJob.availableOutputs.length;
        const primaryOutput = primaryJobOutput(refreshed.latestJob);
        setNotice(
          `Job complete: ${jobLabel}. ${primaryOutput?.label || `${outputCount} output${outputCount === 1 ? "" : "s"}`} ready in Latest job output.`,
        );
        setActiveRailSection("Outputs");
        recordAction("route_run_completed", { target, exitCode: result.exitCode }, "ok", "route");
      }
      recordAction(
        "latest_output_refreshed",
        {
          target,
          selectedRoute: refreshed.latestJob.selectedRoute || "none",
          availableOutputs: refreshed.latestJob.availableOutputs.length,
          missingOutputs: refreshed.latestJob.missingOutputs.length,
        },
        result.ok ? "ok" : "fail",
        "output",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      recordAction("route_run_error", { target, error: err instanceof Error ? err.message : String(err) }, "fail", "route");
    } finally {
      setBusy(false);
    }
  }

  async function handleOpen(kind: string) {
    setBusy(true);
    setError("");
    recordAction("output_open_requested", { kind }, "info", "output");
    try {
      const result = await openOutput(kind);
      setNotice(outputOpenNotice(kind, result.pathDisplay));
      setLog((current) => [`opened ${kind}: ${result.openMode} ${result.pathDisplay}`, ...current]);
      recordAction(
        "output_open_completed",
        { kind, openMode: result.openMode, pathDisplay: result.pathDisplay },
        "ok",
        "output",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      recordAction("output_open_error", { kind, error: err instanceof Error ? err.message : String(err) }, "fail", "output");
    } finally {
      setBusy(false);
    }
  }

  async function handleOpenIntakeFolder() {
    setBusy(true);
    setError("");
    recordAction("intake_folder_open_requested", {}, "info", "intake");
    try {
      const result = await openIntakeFolder();
      setNotice(`${result.message} ${result.pathDisplay}`);
      setLog((current) => [`opened intake folder: ${result.openMode} ${result.pathDisplay}`, ...current]);
      recordAction(
        "intake_folder_open_completed",
        { openMode: result.openMode, pathDisplay: result.pathDisplay },
        "ok",
        "intake",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      recordAction("intake_folder_open_error", { error: err instanceof Error ? err.message : String(err) }, "fail", "intake");
    } finally {
      setBusy(false);
    }
  }

  async function handleToolOpen(tool: ToolHealth) {
    setBusy(true);
    setError("");
    recordAction("tool_open_requested", { tool: tool.tool }, "info", "tool");
    try {
      const result = await openTool(tool.tool);
      setNotice(`${displayToolName(tool.tool)} launch requested. Opening a tool does not prove job output correctness.`);
      setLog((current) => [`opened tool ${tool.tool}: ${result.openMode} ${result.pathDisplay}`, ...current]);
      recordAction(
        "tool_open_completed",
        { tool: tool.tool, openMode: result.openMode, pathDisplay: result.pathDisplay },
        "ok",
        "tool",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      recordAction("tool_open_error", { tool: tool.tool, error: err instanceof Error ? err.message : String(err) }, "fail", "tool");
    } finally {
      setBusy(false);
    }
  }

  async function handleToolOutputOpen(tool: string, outputKey: string) {
    setBusy(true);
    setError("");
    recordAction("tool_native_output_open_requested", { tool, outputKey }, "info", "tool");
    try {
      const result = await openToolOutput(tool, outputKey);
      setNotice(`${displayToolName(tool)} launch requested with latest native output. Direct arbitrary selected-file launch is still not proven.`);
      setLog((current) => [`opened native output ${outputKey} in ${tool}: ${result.outputPathDisplay}`, ...current]);
      recordAction(
        "tool_native_output_open_completed",
        { tool, outputKey, openMode: result.openMode, outputPathDisplay: result.outputPathDisplay },
        "ok",
        "tool",
      );
      await refreshEvents();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      recordAction(
        "tool_native_output_open_error",
        { tool, outputKey, error: err instanceof Error ? err.message : String(err) },
        "fail",
        "tool",
      );
    } finally {
      setBusy(false);
    }
  }

  function requestFilePicker(surface = "intake") {
    if (busy) return;
    recordAction("file_picker_requested", { surface }, "info", "intake");
    filePickerRef.current?.click();
  }

  async function handleFilesUpload(files: FileList | File[], source = "file-input-or-drop") {
    if (busy) return;
    const selectedFiles = Array.from(files);
    if (!selectedFiles.length) return;
    const count = selectedFiles.length;
    const names = selectedFiles.map((file) => file.name);
    setBusy(true);
    setError("");
    recordAction("files_upload_started", { count, names, source }, "info", "intake");
    try {
      await uploadFiles(selectedFiles);
      await refresh();
      setNotice(source === "clipboard-paste" ? `Pasted ${count} file(s) into the intake folder.` : `Uploaded ${count} file(s) to the intake folder.`);
      setLog((current) => [`uploaded ${count} file(s)`, ...current]);
      recordAction("files_uploaded", { count, names, source }, "ok", "intake");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      recordAction("files_upload_error", { count, names, source, error: err instanceof Error ? err.message : String(err) }, "fail", "intake");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    try {
      if (event.target.files?.length) {
        await handleFilesUpload(event.target.files);
      }
    } finally {
      event.target.value = "";
    }
  }

  useEffect(() => {
    function handleClipboardPaste(event: ClipboardEvent) {
      if (busy) return;
      const target = event.target instanceof Element ? event.target : null;
      if (target?.closest("input, textarea, [contenteditable='true'], [role='searchbox']")) {
        return;
      }
      const files = event.clipboardData?.files;
      if (!files?.length) return;
      event.preventDefault();
      void handleFilesUpload(files, "clipboard-paste");
    }

    window.addEventListener("paste", handleClipboardPaste);
    return () => window.removeEventListener("paste", handleClipboardPaste);
  }, [busy]);

  function requestRunPreview(target: RouteTarget) {
    setError("");
    setNotice("");
    setPreviewTarget(target);
    recordAction("route_preview_opened", { target }, "info", "route");
  }

  async function confirmPreviewRun() {
    if (!previewTarget) return;
    const target = previewTarget;
    setPreviewTarget("");
    recordAction("route_preview_confirmed", { target }, "ok", "route");
    await handleRun(target);
  }

  function focusToolsPane() {
    document.getElementById("tools")?.scrollIntoView({ behavior: "smooth", block: "center" });
    setRailPanelSection("");
    setActiveMode("goal");
    setNotice("Tools are in the main Tools area. Use arrows or dots there; Dev keeps the raw inventory.");
    recordAction("tools_pane_focused", {}, "info", "tool");
  }

  function handleModeChange(mode: string) {
    if (mode === "tool") {
      focusToolsPane();
      return;
    }
    setActiveMode(mode);
    recordAction("mode_changed", { mode }, "info", "navigation");
  }

  function handleRailNavigate(section: RailSection) {
    setActiveRailSection(section);
    recordAction("rail_navigation_clicked", { section }, "info", "navigation");
    if (section === "Workbench") {
      setRailPanelSection("");
      window.scrollTo({ top: 0, behavior: "smooth" });
      setActiveMode("goal");
      setNotice("Workbench is active.");
      return;
    }
    setRailPanelSection(section);
    if (section === "Intake") {
      document.getElementById("drop")?.scrollIntoView({ behavior: "smooth", block: "center" });
      setNotice("File intake is open. Click the full tile, drag files onto it, or paste file objects.");
      return;
    }
    if (section === "Plans") {
      setActiveMode("plans");
      setNotice("Work plans are open with current runnable and blocked job options.");
      return;
    }
    if (section === "Tools") {
      focusToolsPane();
      return;
    }
    if (section === "Settings") {
      setNotice("Settings and setup panel is open.");
      return;
    }
    if (section === "Files" || section === "Outputs") {
      setActiveMode("granular");
      setNotice(`${section} panel is open with current Dev proof and output actions.`);
      return;
    }
    setActiveMode("goal");
    setNotice(`${section} panel is open. Its executable work plan needs proof first.`);
  }

  function handleSelectFile(name: string) {
    setSelectedFileName(name);
    recordAction("file_selected", { name }, "info", "intake");
  }

  function handleSelectTool(name: string) {
    setSelectedToolName(name);
    recordAction("tool_selected", { tool: name }, "info", "tool");
  }

  const toolSummary = useMemo(() => summarizeTools(state), [state]);
  const searchResults = useMemo(() => buildSearchResults(state, searchQuery), [state, searchQuery]);

  async function handleSearchSelect(result: SearchResult) {
    if (!state) return;
    setSearchQuery("");
    setSearchOpen(false);
    setError("");
    recordAction("command_search_selected", { group: result.group, label: result.label, type: result.target.type }, "info", "search");
    const target = result.target;
    if (target.type === "file") {
      handleSelectFile(target.name);
      setNotice(`Selected ${target.name}.`);
      return;
    }
    if (target.type === "route") {
      const route = state.routes.find((item) => item.target === target.target);
      setActiveMode("plans");
      if (route?.status === "enabled" && route.target !== "auto" && routeTargets.includes(route.target as RouteTarget)) {
        requestRunPreview(route.target as RouteTarget);
      } else {
        setNotice(`${route?.label || result.label}: ${friendlyProofText(route?.missingGate || "plan selection only")}.`);
      }
      return;
    }
    if (target.type === "tool") {
      const tool = state.tools.find((item) => item.tool === target.tool);
      if (!tool) return;
      setSelectedToolName(tool.tool);
      if (tool.launchable) {
        await handleToolOpen(tool);
      } else {
        focusToolsPane();
        setNotice(`${displayToolName(tool.tool)} is shown in Tools. ${tool.launchReason}`);
      }
      return;
    }
    if (target.type === "output") {
      await handleOpen(target.openKind);
      return;
    }
    handleModeChange(target.mode);
    setNotice(`Showing ${result.label}.`);
  }

  if (!state) {
    return (
      <main className="loading-shell">
        <Loader2 className="spin" aria-hidden="true" />
        <p>{error || "Starting Makers Anvil"}</p>
      </main>
    );
  }

  const selectedFile =
    state.intake.files.find((file) => file.name === selectedFileName) ||
    state.intake.files.find((file) => file.isCandidate) ||
    null;
  const selectedRoute = state.intake.selectedRoute;
  const enabledRun = selectedRoute.target !== "auto"
    && routeTargets.includes(selectedRoute.target as RouteTarget)
    && state.routes.some((route) => route.target === selectedRoute.target && route.status === "enabled");
  const previewRoute = previewTarget ? state.routes.find((route) => route.target === previewTarget) : undefined;
  const workbenchTools = carouselToolsForRoute(state.tools, selectedRoute.target);
  const selectedTool = workbenchTools.find((tool) => tool.tool === selectedToolName) || workbenchTools[0] || orderTools(state.tools)[0] || null;

  const tabs = [
    {
      id: "goal",
      label: "Work Flow",
      content: (
        <WorkFlowPanel
          state={state}
          selectedFile={selectedFile}
          selectedTool={selectedTool}
          toolHandoffs={state.toolHandoffs}
        />
      ),
    },
    {
      id: "plans",
      label: "Plans",
      content: (
        <PlansPanel
          state={state}
          routes={state.routes}
          selectedRoute={selectedRoute.target}
          busy={busy}
          onPreview={requestRunPreview}
        />
      ),
    },
    {
      id: "granular",
      label: "Dev",
      content: (
        <GranularPanel
          state={state}
          log={log}
          events={events}
          eventLogPath={eventLogPath}
          onOpen={handleOpen}
          onRefreshEvents={refreshEvents}
        />
      ),
    },
  ];

  return (
    <main className={`desktop-shell ${railExpanded ? "rail-expanded" : ""}`}>
      <Rail
        hasIssue={Boolean(error)}
        busy={busy}
        intake={state.intake}
        capability={state.capabilityMatrix}
        canRun={enabledRun}
        latestOutputCount={state.latestJob.availableOutputs.length}
        expanded={railExpanded}
        activeSection={activeRailSection}
        onNavigate={handleRailNavigate}
        onToggleExpanded={() => setRailExpanded((current) => !current)}
      />
      <section className={`workbench-shell rail-focus-${activeRailSection.toLowerCase()}`}>
        <header className="topbar">
          <div className="title-row">
            <div className="title-lockup">
              <h1 aria-label={state.workspaceName}>
                <span className="sr-only">{state.workspaceName}</span>
                <span className="title-word">Makers</span>
                <BrandForge />
                <span className="title-word">Anvil</span>
              </h1>
            </div>
            <ContextHelp content={HELP.workspace} />
          </div>
          <CommandSearch
            query={searchQuery}
            results={searchResults}
            open={searchOpen}
            onQueryChange={setSearchQuery}
            onOpenChange={setSearchOpen}
            onSelect={handleSearchSelect}
          />
          <div className="top-actions">
            <button className="icon-button" type="button" onClick={handleRefreshClick} disabled={busy} aria-label="Refresh state">
              <RefreshCw size={18} aria-hidden="true" />
            </button>
            <button
              className="icon-button"
              type="button"
              aria-label="Show activity journal"
              onClick={() => {
                handleModeChange("granular");
                setNotice("Showing the user test journal and Dev proof drawer.");
              }}
            >
              <Bell size={18} aria-hidden="true" />
            </button>
            <button
              className="icon-button"
              type="button"
              aria-label="Show settings"
              onClick={() => handleRailNavigate("Settings")}
            >
              <Settings size={18} aria-hidden="true" />
            </button>
          </div>
        </header>

        {error && (
          <div className="error-strip" role="alert">
            <AlertTriangle size={18} aria-hidden="true" />
            {error}
          </div>
        )}
        {notice && !error && (
          <div className="notice-strip" role="status">
            <CheckCircle2 size={18} aria-hidden="true" />
            {notice}
          </div>
        )}
        {previewTarget && previewRoute && (
          <RunPreview
            route={previewRoute}
            intake={state.intake}
            onCancel={() => setPreviewTarget("")}
            onConfirm={confirmPreviewRun}
            busy={busy}
          />
        )}
        {railPanelSection && railPanelSection !== "Workbench" && (
          <RailActionPanel
            section={railPanelSection}
            state={state}
            busy={busy}
            canRun={enabledRun}
            onClose={() => setRailPanelSection("")}
            onAddFiles={() => requestFilePicker("rail-panel")}
            onOpenIntakeFolder={handleOpenIntakeFolder}
            onMode={handleModeChange}
            onOpenOutput={handleOpen}
            onPreview={() => enabledRun && requestRunPreview(selectedRoute.target as RouteTarget)}
            onRefresh={handleRefreshClick}
            onToolOpen={handleToolOpen}
          />
        )}

        <div className={`workbench-grid mode-${activeMode}`}>
          <section className="main-column">
            <section className="intake-command-grid" aria-label="Add files and current plan">
              <DropZone
                state={state}
                busy={busy}
                fileInputRef={filePickerRef}
                onAddFiles={() => requestFilePicker("drop-zone")}
                onUpload={handleUpload}
                onDropFiles={(files) => handleFilesUpload(files, "drag-drop")}
                onOpenDropFolder={handleOpenIntakeFolder}
                canRun={enabledRun}
                onPreviewWorkPlan={() => enabledRun && requestRunPreview(selectedRoute.target as RouteTarget)}
              />
            </section>
            <ToolDock
              tools={state.tools}
              summary={toolSummary}
              selectedRoute={selectedRoute.target}
              intake={state.intake}
              selectedFile={selectedFile}
              toolHandoffs={state.toolHandoffs}
              busy={busy}
              onToolOpen={handleToolOpen}
              onToolOutputOpen={handleToolOutputOpen}
              selectedToolName={selectedTool?.tool || ""}
              onSelectTool={handleSelectTool}
              onMode={handleModeChange}
            />
            <MediaBoard
              files={state.intake.files}
              selectedFileName={selectedFile?.name || ""}
              onSelect={handleSelectFile}
            />
            <LatestOutputSummary job={state.latestJob} routes={state.routes} intake={state.intake} busy={busy} onOpen={handleOpen} />
            <ModeTabs tabs={tabs} active={activeMode} onChange={handleModeChange} />
          </section>
          <ContextInspector
            file={selectedFile}
            state={state}
            selectedTool={selectedTool}
            canRun={enabledRun}
            busy={busy}
            onRun={() => enabledRun && requestRunPreview(selectedRoute.target as RouteTarget)}
          />
        </div>
      </section>
    </main>
  );
}

function Rail({
  hasIssue,
  busy,
  intake,
  capability,
  canRun,
  latestOutputCount,
  expanded,
  activeSection,
  onNavigate,
  onToggleExpanded,
}: {
  hasIssue: boolean;
  busy: boolean;
  intake: IntakeState;
  capability: AppState["capabilityMatrix"];
  canRun: boolean;
  latestOutputCount: number;
  expanded: boolean;
  activeSection: RailSection;
  onNavigate: (section: RailSection) => void;
  onToggleExpanded: () => void;
}) {
  const statusLabel = hasIssue ? "Check app" : busy ? "Working" : "System ready";
  const statusDetail = hasIssue ? "Needs attention" : busy ? "Job running" : canRun ? "Ready to preview" : "Watching intake";
  const intakeLabel = `${intake.counts.total} file${intake.counts.total === 1 ? "" : "s"}`;
  const intakeDetail = canRun ? "plan ready" : intake.counts.total > 0 ? "needs proof" : "waiting";
  const outputDetail = latestOutputCount > 0 ? `${latestOutputCount} output${latestOutputCount === 1 ? "" : "s"}` : "no output yet";
  const healthDetails = [
    { label: "Inputs", value: `${capability.summary.totalFiles}` },
    { label: "Plan", value: capability.summary.canPreview ? "preview ready" : "waiting" },
    { label: "Tools", value: `${capability.summary.launchableToolCount}/${capability.summary.detectedToolCount}` },
    { label: "Outputs", value: `${capability.summary.latestOutputCount}` },
  ];
  const items: { label: RailSection; icon: ReactNode }[] = [
    { label: "Workbench", icon: <Home size={22} aria-hidden="true" /> },
    { label: "Intake", icon: <Upload size={22} aria-hidden="true" /> },
    { label: "Plans", icon: <Route size={22} aria-hidden="true" /> },
    { label: "Tools", icon: <Wrench size={22} aria-hidden="true" /> },
    { label: "Files", icon: <FolderOpen size={22} aria-hidden="true" /> },
    { label: "Components", icon: <Box size={22} aria-hidden="true" /> },
    { label: "Simulation", icon: <Wind size={22} aria-hidden="true" /> },
    { label: "Outputs", icon: <Download size={22} aria-hidden="true" /> },
    { label: "Settings", icon: <Settings size={22} aria-hidden="true" /> },
  ];
  return (
    <aside className={`app-rail ${expanded ? "expanded" : ""}`} aria-label="Workspace navigation">
      <button
        className="rail-toggle"
        type="button"
        onClick={onToggleExpanded}
        aria-label={expanded ? "Collapse navigation" : "Expand navigation"}
        aria-expanded={expanded}
      >
        {expanded ? <ChevronLeft size={18} aria-hidden="true" /> : <ChevronRight size={18} aria-hidden="true" />}
        <span>Menu</span>
      </button>
      <nav className="rail-nav" aria-label="Workspace sections">
        {items.map((item) => (
          <button
            key={item.label}
            className={item.label === activeSection ? "active" : ""}
            type="button"
            onClick={() => onNavigate(item.label)}
            aria-label={item.label}
            aria-pressed={item.label === activeSection}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="rail-bottom">
        <button
          className={`rail-intake-status ${canRun ? "ready" : intake.counts.total ? "needs-proof" : ""}`}
          type="button"
          onClick={() => onNavigate("Intake")}
          aria-label={`Intake status: ${intakeLabel}, ${intakeDetail}, ${outputDetail}`}
        >
          <Upload size={18} aria-hidden="true" />
          <span>
            <strong>Intake</strong>
            <small>{intakeLabel}</small>
          </span>
          <small>{intakeDetail}</small>
        </button>
        <div
          className={`rail-status ${hasIssue ? "warn" : ""} ${busy ? "busy" : ""}`}
          role="status"
          aria-live="polite"
          aria-label={`${statusLabel}: ${statusDetail}`}
        >
          <svg className="rail-heartbeat" viewBox="0 0 132 28" focusable="false" aria-hidden="true">
            <polyline points="0,15 18,15 26,15 31,6 39,23 48,11 58,15 132,15" />
          </svg>
          <span>{statusLabel}</span>
          <small>{statusDetail}</small>
          {expanded && (
            <dl className="rail-health-details" aria-label="System health details">
              {healthDetails.map((item) => (
                <div key={item.label}>
                  <dt>{item.label}</dt>
                  <dd>{item.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </div>
    </aside>
  );
}

function BrandForge({ compact = false }: { compact?: boolean }) {
  return (
    <span className={`brand-forge ${compact ? "compact" : ""}`} aria-hidden="true">
      <span className="brand-orbit" />
      <span className="brand-forge-core">
        <svg className="brand-anvil-svg" viewBox="0 0 128 86" focusable="false" aria-hidden="true">
          <path className="brand-anvil-top" d="M17 31h49c12 0 20-9 35-11l11-2-8 10c-7 9-15 13-26 14l-9 1-5 9H40l-7-11H19c-6 0-10-3-10-8 0-1 4-2 8-2Z" />
          <path className="brand-anvil-waist" d="M43 51h24l8 14H35l8-14Z" />
          <path className="brand-anvil-base" d="M24 66h63c5 0 9 3 10 8H14c1-5 5-8 10-8Z" />
          <path className="brand-anvil-highlight" d="M23 32h42c11 0 18-6 29-9" />
        </svg>
        <span className="brand-hammer">
          <span className="brand-hammer-head" />
          <span className="brand-hammer-handle" />
        </span>
        <span className="brand-spark spark-a" />
        <span className="brand-spark spark-b" />
        <span className="brand-spark spark-c" />
        <span className="brand-spark spark-d" />
      </span>
    </span>
  );
}

function RailActionPanel({
  section,
  state,
  busy,
  canRun,
  onClose,
  onAddFiles,
  onOpenIntakeFolder,
  onMode,
  onOpenOutput,
  onPreview,
  onRefresh,
  onToolOpen,
}: {
  section: Exclude<RailSection, "Workbench">;
  state: AppState;
  busy: boolean;
  canRun: boolean;
  onClose: () => void;
  onAddFiles: () => void;
  onOpenIntakeFolder: () => void;
  onMode: (mode: string) => void;
  onOpenOutput: (kind: string) => void;
  onPreview: () => void;
  onRefresh: () => void;
  onToolOpen: (tool: ToolHealth) => void;
}) {
  const launchableTools = orderTools(state.tools).filter((tool) => tool.launchable);
  const quickOutputs = prioritizeOutputs(state.latestJob.availableOutputs).slice(0, 3);
  const gmshOrParaView = launchableTools.find((tool) => ["Gmsh", "ParaView pvpython"].includes(tool.tool));
  const firstTool = launchableTools[0];

  const content: Record<
    Exclude<RailSection, "Workbench">,
    {
      title: string;
      eyebrow: string;
      summary: string;
      status: "ready" | "blocked" | "neutral";
      icon: ReactNode;
      detail: ReactNode;
      actions: ReactNode;
    }
  > = {
    Intake: {
      title: "File intake",
      eyebrow: "Source files",
      summary: "Click the full tile, drag files onto it, choose files, or paste file objects. Originals stay in the intake folder.",
      status: "ready",
      icon: <Upload size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>{state.intake.counts.total} file(s) loaded</strong>
          <span>{state.dropPathDisplay}</span>
        </>
      ),
      actions: (
        <>
          <button className="primary-button compact" type="button" onClick={onAddFiles} disabled={busy}>
            <Upload size={16} aria-hidden="true" />
            Choose files
          </button>
          <button className="secondary-button compact" type="button" onClick={onOpenIntakeFolder} disabled={busy}>
            <FolderOpen size={16} aria-hidden="true" />
            Open intake folder
          </button>
        </>
      ),
    },
    Plans: {
      title: "Work plans",
      eyebrow: "What can run now",
      summary: state.intake.message,
      status: canRun ? "ready" : "blocked",
      icon: <Route size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>{state.intake.selectedRoute.label}</strong>
          <span>{state.intake.selectedRoute.blockedClaims}</span>
        </>
      ),
      actions: (
        <>
          <button className="primary-button compact" type="button" onClick={onPreview} disabled={busy || !canRun}>
            <Play size={16} aria-hidden="true" />
            Preview plan
          </button>
          <button className="secondary-button compact" type="button" onClick={() => onMode("goal")}>
            <Route size={16} aria-hidden="true" />
            Show plans
          </button>
        </>
      ),
    },
    Tools: {
      title: "Tools",
      eyebrow: "Launch and inspect",
      summary: `${launchableTools.length} local GUI tool(s) can be launched from the dashboard where the current work plan allows it.`,
      status: launchableTools.length ? "ready" : "blocked",
      icon: <Wrench size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>{firstTool ? `${displayToolName(firstTool.tool)} is ready to open` : "No launchable tool found"}</strong>
            <span>Opening a tool does not prove output correctness; proof rules still control conversions.</span>
        </>
      ),
      actions: (
        <>
          <button className="primary-button compact" type="button" onClick={() => firstTool && onToolOpen(firstTool)} disabled={busy || !firstTool}>
            <ExternalLink size={16} aria-hidden="true" />
            {firstTool ? `Open ${displayToolName(firstTool.tool)}` : "Open tool"}
          </button>
          <button className="secondary-button compact" type="button" onClick={() => onMode("goal")}>
            <Wrench size={16} aria-hidden="true" />
            Work tools
          </button>
        </>
      ),
    },
    Files: {
      title: "Files",
      eyebrow: "Current intake",
      summary: "See every file Makers Anvil has classified, with hash and work-plan boundaries in Dev mode.",
      status: state.intake.counts.total ? "ready" : "neutral",
      icon: <FolderOpen size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>{state.intake.counts.supported} supported / {state.intake.counts.unsupported} unsupported</strong>
          <span>
            Images: {state.intake.counts.images}; Meshes: {state.intake.counts.meshes}; CAD: {state.intake.counts.cad || 0};
            Archives: {state.intake.counts.archives || 0}
          </span>
        </>
      ),
      actions: (
        <>
          <button className="primary-button compact" type="button" onClick={() => onMode("granular")}>
            <FileText size={16} aria-hidden="true" />
            File details
          </button>
          <button className="secondary-button compact" type="button" onClick={onOpenIntakeFolder} disabled={busy}>
            <FolderOpen size={16} aria-hidden="true" />
            Open folder
          </button>
        </>
      ),
    },
    Components: {
      title: "Components",
      eyebrow: "Planned library",
      summary: "Component extraction and part-library management are not executable yet. This panel keeps that boundary visible.",
      status: "blocked",
      icon: <Box size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>Work-plan proof required</strong>
          <span>No automatic component extraction, naming, or BOM creation is claimed yet.</span>
        </>
      ),
      actions: (
        <>
          <button className="secondary-button compact" type="button" onClick={() => onMode("granular")}>
            <FileText size={16} aria-hidden="true" />
            Show files
          </button>
          <button className="secondary-button compact" type="button" onClick={() => onMode("granular")}>
            <Wrench size={16} aria-hidden="true" />
            Dev proof
          </button>
        </>
      ),
    },
    Simulation: {
      title: "Simulation work",
      eyebrow: "Needs proof first",
      summary: "Simulation files can be recognized, but CFD/FEA setup, meshing, solver runs, and validation are not ready yet.",
      status: "blocked",
      icon: <Wind size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>{state.intake.counts.simulation || 0} simulation/data file(s) detected</strong>
          <span>Boundary conditions, mesh quality, solver choice, and validation checks must be built before runs are allowed.</span>
        </>
      ),
      actions: (
        <>
          <button className="primary-button compact" type="button" onClick={() => gmshOrParaView && onToolOpen(gmshOrParaView)} disabled={busy || !gmshOrParaView}>
            <ExternalLink size={16} aria-hidden="true" />
            {gmshOrParaView ? `Open ${displayToolName(gmshOrParaView.tool)}` : "Open sim tool"}
          </button>
          <button className="secondary-button compact" type="button" onClick={() => onMode("granular")}>
            <Wrench size={16} aria-hidden="true" />
            Dev proof
          </button>
        </>
      ),
    },
    Outputs: {
      title: "Outputs",
      eyebrow: "Latest job",
      summary: state.latestJob.exists ? "Open the latest verified job outputs from the current local job bundle." : "No job bundle exists yet.",
      status: quickOutputs.length ? "ready" : "neutral",
      icon: <Download size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>{quickOutputs.length} openable output(s)</strong>
          <span>{state.latestJob.selectedRoute || "No job has completed in the current output pointer."}</span>
        </>
      ),
      actions: (
        <>
          <button
            className="primary-button compact"
            type="button"
            onClick={() => quickOutputs[0] && onOpenOutput(quickOutputs[0].openKind)}
            disabled={busy || !quickOutputs[0]}
          >
            <ExternalLink size={16} aria-hidden="true" />
            {quickOutputs[0] ? quickOutputs[0].label : "Open output"}
          </button>
          <button className="secondary-button compact" type="button" onClick={() => onMode("granular")}>
            <FileText size={16} aria-hidden="true" />
            Output details
          </button>
        </>
      ),
    },
    Settings: {
      title: "Settings and setup",
      eyebrow: "Local control",
      summary: "Current settings are safe local actions and setup visibility. Destructive or install actions stay behind verified proof.",
      status: "neutral",
      icon: <Settings size={24} aria-hidden="true" />,
      detail: (
        <>
          <strong>Current launch commands</strong>
          <span>ma, makers, makersanvil, makers-anvil, makeranvil, makersa, manvil, anvil</span>
        </>
      ),
      actions: (
        <>
          <button className="primary-button compact" type="button" onClick={onRefresh} disabled={busy}>
            <RefreshCw size={16} aria-hidden="true" />
            Refresh
          </button>
          <button className="secondary-button compact" type="button" onClick={() => onMode("granular")}>
            <ClipboardList size={16} aria-hidden="true" />
            Show journal
          </button>
          <button className="secondary-button compact" type="button" onClick={onOpenIntakeFolder} disabled={busy}>
            <FolderOpen size={16} aria-hidden="true" />
            Open intake folder
          </button>
        </>
      ),
    },
  };

  const panel = content[section];
  return (
    <section className={`rail-action-panel ${panel.status}`} aria-label={panel.title}>
      <div className="rail-panel-icon">{panel.icon}</div>
      <div className="rail-panel-copy">
        <span className="panel-eyebrow">{panel.eyebrow}</span>
        <h2>{panel.title}</h2>
        <p>{panel.summary}</p>
      </div>
      <div className="rail-panel-detail">{panel.detail}</div>
      <div className="rail-panel-actions">{panel.actions}</div>
      <button className="icon-button panel-close" type="button" onClick={onClose} aria-label={`Close ${panel.title} panel`}>
        <X size={17} aria-hidden="true" />
      </button>
    </section>
  );
}

function CommandSearch({
  query,
  results,
  open,
  onQueryChange,
  onOpenChange,
  onSelect,
}: {
  query: string;
  results: SearchResult[];
  open: boolean;
  onQueryChange: (value: string) => void;
  onOpenChange: (value: boolean) => void;
  onSelect: (result: SearchResult) => void | Promise<void>;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const hasQuery = query.trim().length > 0;

  useEffect(() => {
    function handleKeyDown(event: globalThis.KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        onOpenChange(true);
        inputRef.current?.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onOpenChange]);

  return (
    <div
      className={`command-search ${open ? "active" : ""}`}
      role="search"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          onOpenChange(false);
        }
      }}
    >
      <Search size={18} aria-hidden="true" />
      <input
        ref={inputRef}
        type="search"
        value={query}
        placeholder="Search plans, tools, files..."
        aria-label="Search plans, tools, files, outputs, and modes"
        onFocus={() => onOpenChange(true)}
        onChange={(event) => {
          onQueryChange(event.target.value);
          onOpenChange(true);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onOpenChange(false);
            event.currentTarget.blur();
            return;
          }
          if (event.key === "Enter" && results.length > 0) {
            event.preventDefault();
            void onSelect(results[0]);
          }
        }}
      />
      <kbd>{hasQuery && results.length > 0 ? "Enter" : "Ctrl K"}</kbd>
      {open && hasQuery && (
        <div className="command-results" aria-label="Search results">
          {results.length > 0 ? (
            results.map((result) => (
              <button className="command-result" key={result.id} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => onSelect(result)}>
                <span className="command-result-group">{result.group}</span>
                <span>
                  <strong>{result.label}</strong>
                  <small>{result.detail}</small>
                </span>
                <span className="command-result-action">{searchActionLabel(result)}</span>
              </button>
            ))
          ) : (
            <span className="command-empty">No matching files, tools, plans, or outputs.</span>
          )}
        </div>
      )}
    </div>
  );
}

function DropZone({
  state,
  busy,
  fileInputRef,
  onAddFiles,
  onUpload,
  onDropFiles,
  onOpenDropFolder,
  canRun,
  onPreviewWorkPlan,
}: {
  state: AppState;
  busy: boolean;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onAddFiles: () => void;
  onUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onDropFiles: (files: FileList) => void | Promise<void>;
  onOpenDropFolder: () => void;
  canRun: boolean;
  onPreviewWorkPlan: () => void;
}) {
  const inputId = "drop-zone-file-input";

  function handleDragOver(event: DragEvent<HTMLElement>) {
    if (busy) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    if (busy || !event.dataTransfer.files.length) return;
    void onDropFiles(event.dataTransfer.files);
  }

  return (
    <section
      className="drop-zone-shell"
      id="drop"
      aria-label="Input drop zone"
    >
      <button
        className="drop-zone"
        type="button"
        onClick={onAddFiles}
        disabled={busy}
        data-testid="drop-zone"
        aria-label="Add source files to intake"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <span className="drop-icon">
          <Upload size={32} aria-hidden="true" />
        </span>
        <span className="drop-copy">
          <strong>Add source files</strong>
          <span>Drop, choose, or paste images, meshes, CAD files, archives, documents, or tool files. Makers Anvil classifies them before any work plan runs.</span>
          <small>{state.dropPathDisplay}</small>
        </span>
      </button>
      <div className="drop-secondary-actions" aria-label="Drop folder actions">
        <button className="drop-action-card" type="button" onClick={onOpenDropFolder} disabled={busy}>
          <FolderOpen size={16} aria-hidden="true" />
          <span>
            <strong>Open intake</strong>
            <small>Open the watched source folder.</small>
          </span>
        </button>
        <button className="drop-action-card emphasized" type="button" onClick={onPreviewWorkPlan} disabled={busy || !canRun}>
          <Play size={16} aria-hidden="true" />
          <span>
            <strong>Preview plan</strong>
            <small>See expected output before running.</small>
          </span>
        </button>
      </div>
      <input
        id={inputId}
        ref={fileInputRef}
        type="file"
        aria-label="Choose files for intake"
        multiple
        disabled={busy}
        onChange={onUpload}
        accept=".png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff,.stl,.obj,.ply,.glb,.gltf,.3mf,.step,.stp,.iges,.igs,.brep,.fcstd,.scad,.kicad_pcb,.kicad_sch,.sch,.pcb,.net,.gcode,.bgcode,.vtk,.vtu,.foam,.csv,.tsv,.dat,.pdf,.md,.txt,.zip,.7z,.rar,.tar,.gz,.tgz"
      />
    </section>
  );
}

function BeginnerGuide({
  state,
  selectedFile,
  canRun,
}: {
  state: AppState;
  selectedFile: IntakeFile | null;
  canRun: boolean;
}) {
  const selectedKind = selectedFile ? formatClassification(selectedFile.classification) : "";
  const cards = [
    {
      label: "Files",
      status: state.intake.counts.total > 0 ? "Done" : "Waiting",
      text:
        state.intake.counts.total > 0
          ? `${state.intake.counts.total} item(s) in intake.`
          : "Drop files into intake.",
      icon: <Upload size={22} aria-hidden="true" />,
    },
    {
      label: "Type",
      status: selectedKind || "Waiting",
      text: selectedKind ? `${selectedKind} input detected.` : "Waiting for a file.",
      icon: <ClipboardList size={22} aria-hidden="true" />,
    },
    {
      label: "Next",
      status: canRun ? "Ready" : "Blocked",
      text: canRun ? "Preview plan, then start job." : "Needs a verified plan.",
      icon: <Route size={22} aria-hidden="true" />,
    },
  ];
  return (
    <section className="beginner-guide" aria-label="Intake status">
      <div className="beginner-guide-head">
        <span>
          <strong>Intake status</strong>
          <small>Live status for files in the intake folder.</small>
        </span>
        <span className={canRun ? "plan-state-pill ready" : "plan-state-pill blocked"}>{canRun ? "Plan ready" : "Needs proof"}</span>
        <ContextHelp content={HELP.startGuide} />
      </div>
      <div className="beginner-steps">
        {cards.map((card) => (
          <article className="beginner-step" key={card.label} aria-label={`${card.label}: ${card.status}. ${card.text}`} title={card.text}>
            <span className="beginner-step-icon">{card.icon}</span>
            <span className="beginner-step-copy">
              <strong>{card.label}</strong>
              <small>{card.text}</small>
            </span>
            <small className={card.status === "Done" || card.status === "Ready" ? "step-status ready" : "step-status"}>
              {card.status}
            </small>
          </article>
        ))}
      </div>
    </section>
  );
}

function MediaBoard({
  files,
  selectedFileName,
  onSelect,
}: {
  files: IntakeFile[];
  selectedFileName: string;
  onSelect: (name: string) => void;
}) {
  const candidates = files.filter((file) => file.isCandidate);
  const selectedIndex = Math.max(0, candidates.findIndex((file) => file.name === selectedFileName));
  const activeFile = candidates[selectedIndex] || candidates[0];

  function moveFile(delta: number) {
    if (!candidates.length) return;
    const nextIndex = (selectedIndex + delta + candidates.length) % candidates.length;
    onSelect(candidates[nextIndex].name);
  }

  return (
    <section className="media-section" aria-labelledby="media-heading">
      <div className="section-heading media-heading">
        <span className="section-title-copy">
          <h2 id="media-heading">
            Selected input
            <ContextHelp content={HELP.references} />
          </h2>
          <small>Raw source file from intake. This is not the generated output.</small>
        </span>
        <span className="chip">{candidates.length} items</span>
      </div>
      {activeFile ? (
        <>
          <div className="file-carousel-shell" aria-live="polite">
            <button className="file-cycle-button" type="button" onClick={() => moveFile(-1)} aria-label="Previous file" disabled={candidates.length <= 1}>
              <ChevronLeft size={22} aria-hidden="true" />
            </button>
            <article className="file-carousel-card" aria-label={`${activeFile.name} file preview`}>
              <FilePreview file={activeFile} />
              <span className="media-copy">
                <strong>{activeFile.name}</strong>
                <span>
                  {formatClassification(activeFile.classification)} - {activeFile.sizeLabel}
                </span>
                <small>{fileBeginnerInfo(activeFile.classification).plain}</small>
              </span>
              <div className="file-detail-grid" aria-label="Selected file details">
                <span>
                  <strong>Plan</strong>
                  <small>{activeFile.route?.target || "waiting"}</small>
                </span>
                <span>
                  <strong>Status</strong>
                  <small>{formatStatusLabel(activeFile.route?.status || "blocked")}</small>
                </span>
                <span>
                  <strong>Hash</strong>
                  <small>{shortHash(activeFile.sha256)}</small>
                </span>
              </div>
            </article>
            <button className="file-cycle-button" type="button" onClick={() => moveFile(1)} aria-label="Next file" disabled={candidates.length <= 1}>
              <ChevronRight size={22} aria-hidden="true" />
            </button>
          </div>
          <div className="file-carousel-footer">
            <span>Raw inputs cycle here; generated output proof is separate.</span>
            <div className="tool-dot-row" aria-label="File carousel position">
              {candidates.map((file, index) => (
                <button
                  key={file.pathDisplay}
                  className={index === selectedIndex ? "active" : ""}
                  type="button"
                  onClick={() => onSelect(file.name)}
                  aria-label={`Show ${file.name}`}
                >
                  <span />
                </button>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="empty-card">
          <Upload size={36} aria-hidden="true" />
          <strong>No files loaded</strong>
          <span>Add source files above to inspect inputs and preview a work plan.</span>
        </div>
      )}
    </section>
  );
}

function FilePreview({ file }: { file: IntakeFile }) {
  const [previewFailed, setPreviewFailed] = useState(false);
  if (file.classification === "image" && file.previewUrl && !previewFailed) {
    return (
      <span className="file-preview">
        <span className="file-badge">{file.extension.replace(".", "").toUpperCase()}</span>
        <img
          src={file.previewUrl}
          alt={`Authorized preview of ${file.name}`}
          decoding="async"
          onError={() => setPreviewFailed(true)}
        />
      </span>
    );
  }
  const icon = iconForClassification(file.classification, 72);
  return (
    <span className={`file-preview generated ${file.classification}`}>
      <span className="file-badge">{file.extension.replace(".", "").toUpperCase() || "FILE"}</span>
      {icon}
    </span>
  );
}

function GoalActions({
  canRun,
  busy,
  onReview,
  onBuild,
  onTool,
}: {
  canRun: boolean;
  busy: boolean;
  onReview: () => void;
  onBuild: () => void;
  onTool: () => void;
}) {
  const actions = [
    {
      title: "Check input files",
      text: "Open Dev proof for exact file list, hashes, and blocked reasons.",
      icon: <ImageIcon size={35} aria-hidden="true" />,
      onClick: onReview,
      help: HELP.reviewAction,
    },
    {
      title: "Preview work plan",
      text: "Review what the job would create before Start job appears.",
      icon: <Box size={35} aria-hidden="true" />,
      onClick: onBuild,
      help: HELP.buildAction,
      disabled: !canRun,
    },
    {
      title: "Open tools",
      text: "Focus the local tools carousel; opening a tool is not output proof.",
      icon: <Wrench size={35} aria-hidden="true" />,
      onClick: onTool,
      help: HELP.toolAction,
    },
  ];
  return (
    <section className="goal-actions" aria-label="Next actions">
      <div className="next-actions-heading">
        <strong>Next actions</strong>
        <small>Shortcuts for files, preview, and tools.</small>
      </div>
      {actions.map((action) => (
        <article key={action.title} className={`goal-card ${action.disabled ? "disabled" : ""}`}>
          <button
            className="goal-main"
            type="button"
            aria-label={action.title}
            onClick={action.onClick}
            disabled={busy || action.disabled}
          >
            <span className="goal-icon">{action.icon}</span>
            <span>
              <strong>{action.title}</strong>
              <small>{action.text}</small>
            </span>
          </button>
          <ContextHelp content={action.help} />
        </article>
      ))}
    </section>
  );
}

function RoutePreviewStrip({ selectedRoute }: { selectedRoute: string }) {
  const steps = [
    { label: "Input files", icon: <ImageIcon size={22} aria-hidden="true" /> },
    { label: "Work plan", icon: <Route size={22} aria-hidden="true" /> },
    { label: "Job output", icon: <Box size={22} aria-hidden="true" /> },
    { label: "Proof bundle", icon: <ClipboardList size={22} aria-hidden="true" /> },
  ];
  return (
    <section className="route-strip" aria-label="Work preview">
      <div className="route-flow" tabIndex={0} aria-label="Work preview steps">
        {steps.map((step, index) => (
          <span className="route-flow-item" key={step.label}>
            <span>
              {step.icon}
              {step.label}
            </span>
            {index < steps.length - 1 && <ChevronRight size={18} aria-hidden="true" />}
          </span>
        ))}
      </div>
      <div className="preview-note">
        <strong>Work preview</strong>
        <span>{selectedRoute || "Select a work plan"} - originals stay unchanged, output goes to a dated job folder.</span>
      </div>
    </section>
  );
}

function ToolDock({
  tools,
  summary,
  selectedRoute,
  intake,
  selectedFile,
  toolHandoffs,
  busy,
  onToolOpen,
  onToolOutputOpen,
  selectedToolName,
  onSelectTool,
  onMode,
}: {
  tools: ToolHealth[];
  summary: ReturnType<typeof summarizeTools>;
  selectedRoute: string;
  intake: IntakeState;
  selectedFile: IntakeFile | null;
  toolHandoffs: ToolHandoff[];
  busy: boolean;
  onToolOpen: (tool: ToolHealth) => void;
  onToolOutputOpen: (tool: string, outputKey: string) => void;
  selectedToolName: string;
  onSelectTool: (name: string) => void;
  onMode: (mode: string) => void;
}) {
  const [launchMode, setLaunchMode] = useState<ToolLaunchMode>("work-plan");
  const eligible = orderTools(tools).filter((tool) => tool.iconUrl || isPrimaryTool(tool.tool));
  const ordered = carouselToolsForRoute(tools, selectedRoute);
  const selectedIndex = Math.max(0, ordered.findIndex((tool) => tool.tool === selectedToolName));
  const activeTool = ordered[selectedIndex] || ordered[0];
  const launchPreview = activeTool ? toolLaunchPreview(activeTool, selectedFile, selectedRoute, intake, launchMode) : null;
  const activeHandoff = activeTool ? toolHandoffForTool(toolHandoffs, activeTool.tool, selectedFile, selectedRoute) : null;

  function moveTool(delta: number) {
    if (!ordered.length) return;
    const nextIndex = (selectedIndex + delta + ordered.length) % ordered.length;
    onSelectTool(ordered[nextIndex].tool);
  }

  return (
    <section className="tool-dock" id="tools" aria-labelledby="tool-dock-heading">
      <div className="section-heading tool-dock-heading">
        <h2 id="tool-dock-heading" aria-label="Tools">
          Tools
          <ContextHelp content={HELP.tools} />
        </h2>
        <span className="chip" title={`${summary.detected} fully detected tool(s)`}>
          {activeTool ? `${selectedIndex + 1} of ${ordered.length}` : `0 of ${eligible.length}`}
        </span>
      </div>
      {activeTool && (
        <div className="tool-carousel-shell" aria-live="polite">
          <button className="tool-cycle-button" type="button" onClick={() => moveTool(-1)} aria-label="Previous tool">
            <ChevronLeft size={24} aria-hidden="true" />
          </button>
          <article className="tool-carousel-card" aria-label={`${displayToolName(activeTool.tool)} tool`}>
            <div className="tool-carousel-icon">
              <ToolIcon tool={activeTool} />
            </div>
            <div className="tool-carousel-copy">
              <div className="tool-carousel-title">
                <span>
                  <strong>{displayToolName(activeTool.tool)}</strong>
                  <small>{activeTool.role}</small>
                </span>
                <StatusPill status={activeTool.health} />
              </div>
              <div className="tool-carousel-chips" aria-label="Tool proof">
                <span>{toolHealthLabel(activeTool)}</span>
                <span>{formatStatusLabel(activeTool.automationStatus)}</span>
                <span>{activeTool.launchKind}</span>
              </div>
              <p>{activeTool.launchReason}</p>
              {activeHandoff?.nativeOutputKey && (
                <ToolNativeOutputAction
                  handoff={activeHandoff}
                  busy={busy}
                  onOpenNativeOutput={onToolOutputOpen}
                />
              )}
              <p className="tool-boundary">{activeTool.blockedClaims}</p>
              <div className="tool-detail-grid" aria-label={`${displayToolName(activeTool.tool)} details`}>
                <span>
                  <strong>Use</strong>
                  <small>{toolBeginnerUse(activeTool.tool)}</small>
                </span>
                <span>
                  <strong>Probe</strong>
                  <small>{formatStatusLabel(activeTool.probeStatus)}</small>
                </span>
                <span>
                  <strong>Source</strong>
                  <small>{activeTool.sourceReference}</small>
                </span>
                <span>
                  <strong>Launch target</strong>
                  <small>{displayPathTail(activeTool.launchPathDisplay)}</small>
                </span>
              </div>
              {launchPreview && (
                <div className="tool-launch-composer" aria-label="Tool launch setup preview">
                  <div className="tool-launch-mode-row" role="group" aria-label="Tool open mode">
                    {([
                      ["tool-only", "Tool", <Wrench size={13} aria-hidden="true" />],
                      ["selected-input", "Selected", <FileText size={13} aria-hidden="true" />],
                      ["work-plan", "Preset", <SlidersHorizontal size={13} aria-hidden="true" />],
                    ] as const).map(([mode, label, icon]) => (
                      <button
                        key={mode}
                        className={launchMode === mode ? "active" : ""}
                        type="button"
                        onClick={() => setLaunchMode(mode)}
                        aria-pressed={launchMode === mode}
                      >
                        {icon}
                        {label}
                      </button>
                    ))}
                  </div>
                  <div className="tool-launch-preview">
                    <span className="tool-launch-flow">
                      <strong>{launchPreview.title}</strong>
                      <small>{launchPreview.flow}</small>
                    </span>
                    <span className={`tool-launch-proof ${launchPreview.statusClass}`}>
                      <Eye size={13} aria-hidden="true" />
                      {launchPreview.status}
                    </span>
                    <p>{launchPreview.detail}</p>
                  </div>
                  {activeHandoff && (
                    <ToolHandoffCard
                      handoff={activeHandoff}
                      selectedFile={selectedFile}
                    />
                  )}
                </div>
              )}
              <div className="tool-carousel-actions">
                {activeTool.launchable ? (
                  <button
                    className="primary-button compact"
                    type="button"
                    onClick={() => onToolOpen(activeTool)}
                    disabled={busy}
                    aria-label={`Open ${displayToolName(activeTool.tool)}`}
                  >
                    <ExternalLink size={15} aria-hidden="true" />
                    Open {displayToolName(activeTool.tool)}
                  </button>
                ) : (
                  <span className="blocked-inline">Blocked until workflow proof exists</span>
                )}
                <button className="secondary-button compact" type="button" onClick={() => onMode("tool")}>
                  <Wrench size={14} aria-hidden="true" />
                  Tool details
                </button>
              </div>
            </div>
          </article>
          <button className="tool-cycle-button" type="button" onClick={() => moveTool(1)} aria-label="Next tool">
            <ChevronRight size={24} aria-hidden="true" />
          </button>
        </div>
      )}
      <div className="tool-carousel-footer">
        <span>{eligible.length} local tools. Preview the launch setup here; Dev keeps the raw inventory.</span>
        <div className="tool-dot-row" aria-label="Tool carousel position">
          {ordered.map((tool, index) => (
            <button
              key={tool.tool}
              className={index === selectedIndex ? "active" : ""}
              type="button"
              onClick={() => onSelectTool(tool.tool)}
              aria-label={`Show ${displayToolName(tool.tool)}`}
            >
              <span />
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function ToolNativeOutputAction({
  handoff,
  busy,
  onOpenNativeOutput,
}: {
  handoff: ToolHandoff;
  busy: boolean;
  onOpenNativeOutput: (tool: string, outputKey: string) => void;
}) {
  const nativeOutputReady = handoff.nativeOutputLaunchStatus === "latest_native_output_ready";
  return (
    <div className="tool-handoff-native">
      <span>
        <strong>Latest native output</strong>
        <small>
          {nativeOutputReady
            ? "Ready to open from the latest completed job."
            : "Run the matching work plan before opening this tool output."}
        </small>
      </span>
      <button
        className="secondary-button compact"
        type="button"
        disabled={busy || !nativeOutputReady}
        onClick={() => onOpenNativeOutput(handoff.tool, handoff.nativeOutputKey)}
      >
        <ExternalLink size={14} aria-hidden="true" />
        {handoff.nativeOutputLabel || "Open latest native output"}
      </button>
    </div>
  );
}

function ToolHandoffCard({
  handoff,
  selectedFile,
}: {
  handoff: ToolHandoff;
  selectedFile: IntakeFile | null;
}) {
  const selectedName = selectedFile ? selectedFile.name : "No selected input";
  return (
    <div className="tool-handoff-card" aria-label="Selected tool handoff contract">
      <div className="tool-handoff-head">
        <span>
          <strong>Selected-file handoff</strong>
          <small>{selectedName}</small>
        </span>
        <span className={`handoff-state ${handoffStatusClass(handoff.status)}`}>{handoff.statusLabel}</span>
      </div>
      <div className="tool-handoff-grid">
        <span>
          <strong>Formats</strong>
          <small>{handoff.inputFormats.join(", ")}</small>
        </span>
        <span>
          <strong>Tool open</strong>
          <small>{friendlyHandoffStatus(handoff.toolOpenStatus)}</small>
        </span>
        <span>
          <strong>File launch</strong>
          <small>{friendlyHandoffStatus(handoff.directFileLaunchStatus)}</small>
        </span>
      </div>
      <p>{handoff.previewContract}</p>
      <p>{handoff.outputContract}</p>
    </div>
  );
}

function ToolIcon({ tool }: { tool: ToolHealth }) {
  if (tool.iconUrl) {
    return <img src={tool.iconUrl} alt="" />;
  }
  return <span className="tool-fallback">{initials(displayToolName(tool.tool))}</span>;
}

function ActivityTimeline({
  intake,
  selectedRoute,
  latestOutputCount,
}: {
  intake: IntakeState;
  selectedRoute: string;
  latestOutputCount: number;
}) {
  const steps = [
    { label: "Files", detail: `${intake.counts.total} item(s)`, icon: <CheckCircle2 size={22} aria-hidden="true" />, done: intake.counts.total > 0 },
    { label: "Plan", detail: selectedRoute || "none", icon: <Route size={22} aria-hidden="true" />, done: selectedRoute !== "none" },
    { label: "Preview", detail: "Ready to review", icon: <Play size={22} aria-hidden="true" />, done: false },
    { label: "Tool", detail: "Only when needed", icon: <Wrench size={22} aria-hidden="true" />, done: false },
    { label: "Outputs", detail: `${latestOutputCount} available`, icon: <FolderOpen size={22} aria-hidden="true" />, done: latestOutputCount > 0 },
  ];
  return (
    <section className="activity-timeline" aria-label="Activity timeline">
      <h2>Workbench progress</h2>
      <div className="timeline-row">
        {steps.map((step) => (
          <article className={`timeline-card ${step.done ? "done" : ""}`} key={step.label}>
            {step.icon}
            <span>
              <strong>{step.label}</strong>
              <small>{step.detail}</small>
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}

function LatestOutputSummary({
  job,
  routes,
  intake,
  busy,
  onOpen,
}: {
  job: LatestJob;
  routes: RouteCard[];
  intake: IntakeState;
  busy: boolean;
  onOpen: (kind: string) => void;
}) {
  if (!job.exists || job.availableOutputs.length === 0) {
    return null;
  }
  const quickOutputs = prioritizeOutputs(job.availableOutputs).slice(0, 5);
  const folderOutput = job.availableOutputs.find((output) => output.key === "folder");
  const primaryOutput = primaryJobOutput(job);
  const jobLabel = latestJobPlanLabel(job, routes);
  return (
    <section className="latest-output-summary" aria-label="Latest job output">
      <div className="latest-output-copy">
        <span className="latest-output-icon">
          <FolderOpen size={24} aria-hidden="true" />
        </span>
        <span>
          <strong>Latest output proof: {jobLabel}</strong>
          <small>
            Created {primaryOutput?.label || `${job.availableOutputs.length} openable outputs`}. Originals stayed unchanged.
          </small>
        </span>
      </div>
      <div className="latest-output-facts" aria-label="Completed job facts">
        <span>
          <strong>What ran</strong>
          <small>{jobLabel}</small>
        </span>
        <span>
          <strong>Main result</strong>
          <small>{primaryOutput?.label || "Openable job output"}</small>
        </span>
        <span>
          <strong>Where it is</strong>
          <small>{folderOutput ? displayPathTail(folderOutput.pathDisplay) : "Latest job folder"}</small>
        </span>
      </div>
      <JobProgressStrip
        files={intake.counts.total}
        plan={jobLabel}
        outputCount={job.availableOutputs.length}
      />
      <p className="latest-output-next">
        {jobBoundaryCopy(job.selectedRoute)}
      </p>
      <div className="latest-output-actions" aria-label="Latest job output actions">
        {quickOutputs.map((output) => (
          <button className="secondary-button compact" key={output.key} type="button" onClick={() => onOpen(output.openKind)} disabled={busy}>
            <ExternalLink size={15} aria-hidden="true" />
            <span>
              <strong>{friendlyOutputAction(output)}</strong>
              <small>{outputActionHint(output)}</small>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

function JobProgressStrip({
  files,
  plan,
  outputCount,
}: {
  files: number;
  plan: string;
  outputCount: number;
}) {
  const steps = [
    { label: "Inputs", detail: `${files} file${files === 1 ? "" : "s"}`, done: files > 0 },
    { label: "Work plan", detail: plan, done: Boolean(plan) },
    { label: "Output", detail: `${outputCount} ready`, done: outputCount > 0 },
  ];
  return (
    <div className="job-progress-strip" aria-label="Completed job progress">
      {steps.map((step) => (
        <span className={step.done ? "done" : ""} key={step.label}>
          <CheckCircle2 size={16} aria-hidden="true" />
          <strong>{step.label}</strong>
          <small>{step.detail}</small>
        </span>
      ))}
    </div>
  );
}

function ContextInspector({
  file,
  state,
  selectedTool,
  canRun,
  busy,
  onRun,
}: {
  file: IntakeFile | null;
  state: AppState;
  selectedTool: ToolHealth | null;
  canRun: boolean;
  busy: boolean;
  onRun: () => void;
}) {
  const selectedRoute = state.intake.selectedRoute;
  return (
      <aside className="context-inspector" role="region" aria-label="Job preview and proof">
      <div className="section-heading">
        <span className="section-title-copy">
          <h2>
            Work preview
            <ContextHelp content={HELP.inspector} />
          </h2>
          <small>What will happen, what output means, and what stays blocked.</small>
        </span>
      </div>
      {file ? (
        <article className="selected-card preview-card">
          <span className="preview-card-label">Raw selected input</span>
          <FilePreview file={file} />
          <div className="preview-card-copy">
            <span className="file-type-chip">{file.extension.replace(".", "").toUpperCase() || formatClassification(file.classification)}</span>
            <strong>{file.name}</strong>
            <span>
              {formatClassification(file.classification)} - {file.sizeLabel}
            </span>
          </div>
        </article>
      ) : (
        <article className="selected-card empty">
          <Upload size={38} aria-hidden="true" />
          <strong>No selected file</strong>
          <span>Drop files to inspect a work plan.</span>
        </article>
      )}
      <section className="inspector-block">
        <h3>
          Plan and boundary
          <ContextHelp content={HELP.routeStatus} />
        </h3>
        <p className="route-message">{state.intake.message}</p>
        <div className="route-proof-chips" aria-label="Route proof summary">
          <span className={selectedRoute.status === "blocked" ? "proof-chip blocked" : "proof-chip ready"}>
            <span className={selectedRoute.status === "blocked" ? "status-dot blocked" : "status-dot"}>
              {formatStatusLabel(selectedRoute.status)}
            </span>
          </span>
          <span className="proof-chip" title={selectedRoute.target}>
            Plan: <strong>{selectedRoute.target}</strong>
          </span>
          <span className="proof-chip" title={selectedRoute.routeId}>
            Proof: <strong>{shortGate(selectedRoute.routeId)}</strong>
          </span>
        </div>
        <div className="boundary-callout">
          <strong>Boundary</strong>
          <span>{selectedRoute.blockedClaims}</span>
        </div>
        {file && (
          <div className="hash-line">
            <strong>Hash</strong>
            <code title={file.sha256 || "not available"}>{shortHash(file.sha256)}</code>
          </div>
        )}
      </section>
      <section className="inspector-block work-preview-block">
        <h3>Expected output preview</h3>
        <div className="work-preview-flow" aria-label="Work preview flow">
          <span>Raw input</span>
          <ChevronRight size={16} aria-hidden="true" />
          <span>{selectedRoute.label || "Selected work plan"}</span>
          <ChevronRight size={16} aria-hidden="true" />
          <span>Generated output</span>
        </div>
        <p>
          The Selected input panel shows the raw file. This preview explains the expected generated output before running. Latest output proof opens the completed job output; for Blender reference work, the image can still look like the input because the output is a reference board and a Blender work scene built from that image.
        </p>
      </section>
      <section className="inspector-block explanation-block">
        <h3>Input meaning</h3>
        <p>{file ? fileBeginnerInfo(file.classification).plain : "No file is selected yet."}</p>
      </section>
      <section className="inspector-block explanation-block">
        <h3>Tool context</h3>
        <p>
          {selectedTool
            ? `${displayToolName(selectedTool.tool)}: ${selectedTool.role}. Tool launch and preview behavior need workflow-specific proof before they can prove output behavior.`
            : "No local tool is selected yet."}
        </p>
      </section>
      <section className="inspector-block next-step">
        <h3>Next step</h3>
        <p>{state.intake.nextAction}</p>
        <button className="primary-button" type="button" onClick={onRun} disabled={!canRun || busy}>
          <Play size={17} aria-hidden="true" />
          Preview work plan
        </button>
      </section>
    </aside>
  );
}

function WorkFlowPanel({
  state,
  selectedFile,
  selectedTool,
  toolHandoffs,
}: {
  state: AppState;
  selectedFile: IntakeFile | null;
  selectedTool: ToolHealth | null;
  toolHandoffs: ToolHandoff[];
}) {
  const selectedRoute = state.intake.selectedRoute;
  const fileInfo = selectedFile ? fileBeginnerInfo(selectedFile.classification) : null;
  const primaryOutput = primaryJobOutput(state.latestJob);
  const folderOutput = state.latestJob.availableOutputs.find((output) => output.key === "folder");
  const selectedHandoff = selectedTool ? toolHandoffForTool(toolHandoffs, selectedTool.tool, selectedFile, selectedRoute.target) : null;
  return (
    <div className="work-flow-panel">
      <CapabilityPanel matrix={state.capabilityMatrix} />
      <section className="workflow-proof-card" aria-label="Selected input readout" tabIndex={0}>
        <div className="workflow-card-head">
          <span>
            <strong>Selected input</strong>
            <small>What Makers Anvil thinks the dropped or chosen file is.</small>
          </span>
          <StatusPill status={selectedRoute.status} />
        </div>
        <div className="workflow-fact-grid">
          <span>
            <strong>File type</strong>
            <small>{selectedFile ? formatClassification(selectedFile.classification) : "Waiting for input"}</small>
          </span>
          <span>
            <strong>Ready plan</strong>
            <small>{selectedRoute.label || "No ready work plan yet"}</small>
          </span>
          <span>
            <strong>Input proof</strong>
            <small>{selectedFile ? shortHash(selectedFile.sha256) : state.ingress.status}</small>
          </span>
        </div>
        <p>{fileInfo ? fileInfo.plain : "Add source files so the app can classify them and choose a proven work plan."}</p>
      </section>
      <section className="workflow-proof-card" aria-label="Job result readout" tabIndex={0}>
        <div className="workflow-card-head">
          <span>
            <strong>Latest output proof</strong>
            <small>What happened after the last job and what the buttons open.</small>
          </span>
          <span className={state.latestJob.availableOutputs.length ? "plan-state-pill ready" : "plan-state-pill"}>
            {state.latestJob.availableOutputs.length ? `${state.latestJob.availableOutputs.length} outputs` : "No output"}
          </span>
        </div>
        <div className="workflow-fact-grid">
          <span>
            <strong>Latest plan</strong>
            <small>{state.latestJob.selectedRoute || selectedRoute.target}</small>
          </span>
          <span>
            <strong>Main output</strong>
            <small>{primaryOutput?.label || "No completed output yet"}</small>
          </span>
          <span>
            <strong>Job folder</strong>
            <small>{folderOutput ? displayPathTail(folderOutput.pathDisplay) : "Waiting for a job"}</small>
          </span>
        </div>
        <p>{jobBoundaryCopy(state.latestJob.selectedRoute || selectedRoute.target)}</p>
      </section>
      <section className="workflow-proof-card" aria-label="Tool handoff status" tabIndex={0}>
        <div className="workflow-card-head">
          <span>
            <strong>Tool handoff</strong>
            <small>What can be opened now, and what still needs a proven file-launch contract.</small>
          </span>
          <span className="plan-state-pill">Preview only</span>
        </div>
        <p>
          {selectedTool && selectedHandoff
            ? `${displayToolName(selectedTool.tool)}: ${selectedHandoff.previewContract} Direct selected-file launch is ${friendlyHandoffStatus(selectedHandoff.directFileLaunchStatus)}.`
            : selectedTool
              ? `${displayToolName(selectedTool.tool)} can be opened from the Tools pane. Opening the selected input inside the tool still needs a tool-specific launch contract before the app can claim that handoff.`
            : "No local tool is selected yet."}
        </p>
        {selectedHandoff && (
          <div className="workflow-handoff-proof">
            <span>
              <strong>Preset</strong>
              <small>{selectedHandoff.presetName}</small>
            </span>
            <span>
              <strong>Output</strong>
              <small>{selectedHandoff.outputContract}</small>
            </span>
          </div>
        )}
      </section>
    </div>
  );
}

function PlansPanel({
  state,
  routes,
  selectedRoute,
  busy,
  onPreview,
}: {
  state: AppState;
  routes: RouteCard[];
  selectedRoute: string;
  busy: boolean;
  onPreview: (target: RouteTarget) => void;
}) {
  const selectedRouteCard = routes.find((route) => route.target === selectedRoute) || routes.find((route) => route.target === "auto");
  return (
    <section className="route-lane work-plan-studio" aria-label="Work plans">
      <div className="section-heading">
        <span className="section-title-copy">
          <h3>Work plans</h3>
          <small>Choose the current job path, preview it, or keep not-ready lanes visible for planning.</small>
        </span>
        <ContextHelp content={HELP.routeQueue} />
      </div>
      <div className="work-plan-current" aria-label="Selected work plan">
        <span>
          <strong>{selectedRouteCard?.label || state.intake.selectedRoute.label}</strong>
          <small>{state.intake.nextAction}</small>
        </span>
        <StatusPill status={state.intake.selectedRoute.status} />
      </div>
      <div className="route-list" tabIndex={0} aria-label="Work plan list">
        {routes.map((route) => {
          const runnable = route.status === "enabled" && routeTargets.includes(route.target as RouteTarget);
          const matches = route.target === selectedRoute || route.target === "auto";
          const info = routeBeginnerInfo(route.target);
          return (
            <article className={`route-row ${matches ? "selected" : ""}`} key={route.target}>
              <span className={route.status === "blocked" ? "route-icon blocked" : "route-icon"}>
                {routeIcon(route.target)}
              </span>
              <span className="route-copy">
                <strong>{route.label}</strong>
                <small>{friendlyProofText(route.outputStatus || route.missingGate || "Plan selection only")}</small>
                <span className="route-beginner-copy">{info.plain}</span>
              </span>
              <span className="route-proof-note">
                <strong>{route.status === "blocked" ? "Needs proof" : "Creates"}</strong>
                <small>{route.status === "blocked" ? info.needs : info.creates}</small>
              </span>
              <span className="route-row-actions">
                <StatusPill status={route.status} />
                {runnable && route.target !== "auto" ? (
                  <button
                    className="secondary-button compact"
                    type="button"
                    onClick={() => onPreview(route.target as RouteTarget)}
                    disabled={busy || !matches}
                  >
                    <Play size={15} aria-hidden="true" />
                    {matches ? "Preview plan" : "Waiting"}
                  </button>
                ) : (
                  <span className="blocked-inline">{route.status === "blocked" ? "Not ready" : "Auto"}</span>
                )}
              </span>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function CapabilityPanel({ matrix }: { matrix: AppState["capabilityMatrix"] }) {
  const featured = prioritizeCapabilityLanes(matrix.lanes);
  const summary = [
    { label: "Inputs", value: `${matrix.summary.totalFiles}` },
    { label: "Ready files", value: `${matrix.summary.supportedFiles}` },
    { label: "Tools", value: `${matrix.summary.launchableToolCount}/${matrix.summary.detectedToolCount}` },
    { label: "Outputs", value: `${matrix.summary.latestOutputCount}` },
  ];
  return (
    <section className="capability-panel" aria-label="Current Makers Anvil capability status" tabIndex={0}>
      <div className="section-heading tight">
        <span className="section-title-copy">
          <h3>What Makers Anvil can handle now</h3>
          <small>Live truth for file intake, tools, and blocked work.</small>
        </span>
        <span className={matrix.summary.canPreview ? "plan-state-pill ready" : "plan-state-pill"}>
          {matrix.summary.canPreview ? "Preview ready" : "Waiting"}
        </span>
      </div>
      <div className="capability-summary" aria-label="Capability summary">
        {summary.map((item) => (
          <span key={item.label}>
            <strong>{item.value}</strong>
            <small>{item.label}</small>
          </span>
        ))}
      </div>
      <div className="ingress-method-row" aria-label="Input methods">
        {matrix.ingressMethods.map((method) => (
          <span className={`ingress-method ${method.status}`} key={method.id} title={method.detail}>
            <strong>{method.label}</strong>
            <small>{method.statusLabel}</small>
          </span>
        ))}
      </div>
      <div className="capability-lanes" aria-label="File class capability lanes">
        {featured.map((lane) => (
          <article className={`capability-lane ${lane.status}`} key={lane.id} aria-label={`${lane.label}: ${lane.statusLabel}`}>
            <span className="capability-lane-head">
              <strong>{lane.label}</strong>
              <small>{lane.statusLabel}</small>
            </span>
            <p>{lane.whatWorks}</p>
            <span className="capability-plan">
              <strong>{lane.currentCount}</strong>
              <small>{lane.primaryPlan}</small>
            </span>
            <div className="capability-tools" aria-label={`${lane.label} tools`}>
              {lane.tools.length ? (
                lane.tools.map((tool) => (
                  <span key={tool.name} title={`${tool.name}: ${tool.status}, ${tool.launch}`}>
                    {tool.name}
                  </span>
                ))
              ) : (
                <span>No tool needed yet</span>
              )}
            </div>
          </article>
        ))}
      </div>
      <p className="capability-honesty">{matrix.honesty[1]}</p>
    </section>
  );
}

function GranularPanel({
  state,
  log,
  events,
  eventLogPath,
  onOpen,
  onRefreshEvents,
}: {
  state: AppState;
  log: string[];
  events: UserActionEvent[];
  eventLogPath: string;
  onOpen: (kind: string) => void;
  onRefreshEvents: () => Promise<void>;
}) {
  return (
    <section className="granular-layout">
      <div>
        <h3>Intake Files</h3>
        <div className="file-list">
          {state.intake.files.map((file) => (
            <article className="file-row" key={file.pathDisplay}>
              {iconForClassification(file.classification, 20)}
              <span>
                <strong>{file.name}</strong>
                <small>
                  {formatClassification(file.classification)} / {file.sizeLabel} / {file.sha256 || "no hash"}
                </small>
              </span>
            </article>
          ))}
        </div>
      </div>
      <div>
        <h3>Proof and Outputs</h3>
        <div className="proof-drawer">
          <dl className="inspector-grid">
            <div>
              <dt>Old launcher untouched</dt>
              <dd>{String(state.launcher.oldPanelUntouched)}</dd>
            </div>
            <div>
              <dt>Switch allowed</dt>
              <dd>{String(state.launcher.switchAllowed)}</dd>
            </div>
            <div>
              <dt>Latest job plan</dt>
              <dd>{state.latestJob.selectedRoute || "none"}</dd>
            </div>
            <div>
              <dt>Staging manifest</dt>
              <dd>{state.ingress.status}</dd>
            </div>
            <div>
              <dt>Batch kind</dt>
              <dd>{state.ingress.routePlan.batchKind}</dd>
            </div>
          </dl>
          <section className="staging-manifest" aria-label="Staging manifest">
            <h3>Capability matrix</h3>
            <dl className="inspector-grid">
              <div>
                <dt>Total files</dt>
                <dd>{state.capabilityMatrix.summary.totalFiles}</dd>
              </div>
              <div>
                <dt>Preview ready</dt>
                <dd>{String(state.capabilityMatrix.summary.canPreview)}</dd>
              </div>
              <div>
                <dt>Detected tools</dt>
                <dd>{state.capabilityMatrix.summary.detectedToolCount}</dd>
              </div>
              <div>
                <dt>Launchable tools</dt>
                <dd>{state.capabilityMatrix.summary.launchableToolCount}</dd>
              </div>
            </dl>
            <div className="capability-proof-list" aria-label="Capability lane proof">
              {state.capabilityMatrix.lanes.map((lane) => (
                <article key={lane.id}>
                  <strong>
                    {lane.label}: {lane.statusLabel}
                  </strong>
                  <small>{lane.proof}</small>
                  <span>{lane.blocked}</span>
                </article>
              ))}
            </div>
            <h3>Staging manifest</h3>
            <dl className="inspector-grid">
              <div>
                <dt>Stage</dt>
                <dd>{state.ingress.stageId}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{state.ingress.sourceKind}</dd>
              </div>
              <div>
                <dt>Files</dt>
                <dd>{state.ingress.fileCount}</dd>
              </div>
              <div>
                <dt>Auto-run</dt>
                <dd>{String(state.ingress.routePlan.autoRunAllowed)}</dd>
              </div>
              <div>
                <dt>JSON</dt>
                <dd>{state.ingress.manifestJsonPathDisplay}</dd>
              </div>
              <div>
                <dt>CSV</dt>
                <dd>{state.ingress.manifestCsvPathDisplay}</dd>
              </div>
              <div>
                <dt>Originals</dt>
                <dd>{state.ingress.safety.originalsPreserved ? "preserved" : "not proven"}</dd>
              </div>
              <div>
                <dt>Archive extraction</dt>
                <dd>{state.ingress.safety.archiveExtractionEnabled ? "enabled" : "blocked"}</dd>
              </div>
              <div>
                <dt>Folder import</dt>
                <dd>{state.ingress.safety.folderImportEnabled ? "enabled" : "blocked"}</dd>
              </div>
              <div>
                <dt>Clipboard paste</dt>
                <dd>{state.ingress.safety.clipboardPasteEnabled ? "enabled" : "blocked"}</dd>
              </div>
            </dl>
            {state.ingress.archiveInventory && state.ingress.archiveInventory.archiveCount > 0 ? (
              <dl className="inspector-grid" aria-label="Archive inventory summary">
                <div>
                  <dt>Archives</dt>
                  <dd>{state.ingress.archiveInventory.archiveCount}</dd>
                </div>
                <div>
                  <dt>Inventoried</dt>
                  <dd>{state.ingress.archiveInventory.inventoriedArchiveCount}</dd>
                </div>
                <div>
                  <dt>Archive entries</dt>
                  <dd>{state.ingress.archiveInventory.totalEntries}</dd>
                </div>
                <div>
                  <dt>Unsafe paths</dt>
                  <dd>{state.ingress.archiveInventory.unsafeEntryCount}</dd>
                </div>
                <div>
                  <dt>Nested archives</dt>
                  <dd>{state.ingress.archiveInventory.nestedArchiveCount}</dd>
                </div>
                <div>
                  <dt>Extract</dt>
                  <dd>{state.ingress.archiveInventory.extractionEnabled ? "enabled" : "blocked"}</dd>
                </div>
              </dl>
            ) : null}
            <p className="muted">{state.ingress.routePlan.reason}</p>
            {state.ingress.archiveInventory && state.ingress.archiveInventory.archiveCount > 0 ? (
              <p className="muted">{state.ingress.archiveInventory.note}</p>
            ) : null}
          </section>
          <div className="output-actions">
            {state.latestJob.availableOutputs.map((output) => (
              <button className="secondary-button" key={output.key} type="button" onClick={() => onOpen(output.openKind)}>
                <ExternalLink size={15} aria-hidden="true" />
                {output.label}
              </button>
            ))}
          </div>
          <pre>{log.length ? log.join("\n\n") : "No job output captured in this app session yet."}</pre>
        </div>
        <section className="event-journal" aria-label="User test journal">
          <div className="section-heading tight">
            <h3>User test journal</h3>
            <button className="secondary-button compact" type="button" onClick={onRefreshEvents}>
              <RefreshCw size={14} aria-hidden="true" />
              Refresh
            </button>
          </div>
          <p className="muted">Local app actions recorded for debugging after you test buttons, plans, and outputs.</p>
          <small className="journal-path">{eventLogPath || "Journal file will appear after the first recorded action."}</small>
          <div className="event-list">
            {events.length > 0 ? (
              events
                .slice()
                .reverse()
                .slice(0, 8)
                .map((event, index) => (
                  <article className={`event-row ${event.status}`} key={`${event.timestampUtc}-${event.action}-${index}`}>
                    <span className="event-status">{event.status}</span>
                    <span>
                      <strong>{event.action}</strong>
                      <small>
                        {formatEventTime(event.timestampUtc)} / {event.surface}
                      </small>
                      <code>{formatEventDetail(event.detail)}</code>
                    </span>
                  </article>
                ))
            ) : (
              <p className="muted">No local app actions recorded yet.</p>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}

function RunPreview({
  route,
  intake,
  onCancel,
  onConfirm,
  busy,
}: {
  route: RouteCard;
  intake: IntakeState;
  onCancel: () => void;
  onConfirm: () => void;
  busy: boolean;
}) {
  return (
    <section className="run-preview-panel" aria-label="Work plan preview">
      <div>
        <strong>Work plan preview: {route.label}</strong>
        <p>{routeBeginnerInfo(route.target).creates} Originals stay unchanged. Output goes to a dated job folder.</p>
      </div>
      <dl>
        <div>
          <dt>Input</dt>
          <dd>{intake.counts.supported} supported file(s)</dd>
        </div>
        <div>
          <dt>Output</dt>
          <dd>{route.outputStatus || "Work-plan boundary required"}</dd>
        </div>
        <div>
          <dt>Boundary</dt>
          <dd>Reference/review output only. No design correctness claim.</dd>
        </div>
      </dl>
      <div className="run-preview-actions">
        <button className="secondary-button" type="button" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button className="primary-button compact" type="button" onClick={onConfirm} disabled={busy}>
          <Play size={16} aria-hidden="true" />
          Start job
        </button>
      </div>
    </section>
  );
}

function buildSearchResults(state: AppState | null, query: string): SearchResult[] {
  const term = query.trim().toLowerCase();
  if (!state || !term) return [];

  const results: SearchResult[] = [];
  for (const file of state.intake.files) {
    if (matchesSearch(term, [file.name, file.pathDisplay, file.classification, file.route.label, file.route.target])) {
      results.push({
        id: `file-${file.pathDisplay}`,
        group: "File",
        label: file.name,
        detail: `${formatClassification(file.classification)} - ${file.sizeLabel} - ${fileBeginnerInfo(file.classification).plain}`,
        target: { type: "file", name: file.name },
      });
    }
  }

  for (const route of state.routes) {
    if (matchesSearch(term, [route.label, route.target, route.status, route.outputStatus || "", route.missingGate || ""])) {
      results.push({
        id: `route-${route.target}`,
        group: "Plan",
        label: route.label,
        detail: route.status === "enabled" ? routeBeginnerInfo(route.target).creates : `Blocked: ${friendlyProofText(route.missingGate || "work-plan proof required")}`,
        target: { type: "route", target: route.target },
      });
    }
  }

  for (const tool of orderTools(state.tools)) {
    if (matchesSearch(term, [tool.tool, displayToolName(tool.tool), tool.role, tool.health, tool.automationStatus, toolBeginnerUse(tool.tool)])) {
      results.push({
        id: `tool-${tool.tool}`,
        group: "Tool",
        label: displayToolName(tool.tool),
        detail: tool.launchable ? `Open tool - ${toolBeginnerUse(tool.tool)}` : `Show tool status - ${tool.launchReason}`,
        target: { type: "tool", tool: tool.tool },
      });
    }
  }

  for (const output of prioritizeOutputs(state.latestJob.availableOutputs)) {
    if (matchesSearch(term, [output.label, output.key, output.openKind, output.pathDisplay, state.latestJob.selectedRoute || ""])) {
      results.push({
        id: `output-${output.key}`,
        group: "Output",
        label: output.label,
        detail: output.pathDisplay,
        target: { type: "output", openKind: output.openKind },
      });
    }
  }

  const modes = [
    { mode: "goal" as const, label: "Work Flow", detail: "What the app thinks the input is, what will happen next, and what the last job created." },
    { mode: "plans" as const, label: "Plans", detail: "Full work-plan queue with ready and not-ready routes." },
    { mode: "granular" as const, label: "Dev", detail: "Raw proof drawer, intake list, outputs, and user test journal." },
  ];
  for (const mode of modes) {
    if (matchesSearch(term, [mode.mode, mode.label, mode.detail])) {
      results.push({ id: `mode-${mode.mode}`, group: "Mode", label: mode.label, detail: mode.detail, target: { type: "mode", mode: mode.mode } });
    }
  }

  return results.slice(0, 10);
}

function matchesSearch(term: string, values: string[]) {
  return values.some((value) => value.toLowerCase().includes(term));
}

function searchActionLabel(result: SearchResult) {
  if (result.target.type === "tool") return "Open";
  if (result.target.type === "output") return "Open";
  if (result.target.type === "route") return "Preview";
  if (result.target.type === "file") return "Select";
  return "Show";
}

function formatEventTime(timestampUtc: string) {
  const parsed = new Date(timestampUtc);
  if (Number.isNaN(parsed.getTime())) {
    return timestampUtc;
  }
  return parsed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatEventDetail(detail: Record<string, unknown>) {
  const entries = Object.entries(detail || {}).slice(0, 4);
  if (!entries.length) {
    return "no detail";
  }
  return entries
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
    .join(" / ");
}

function prioritizeCapabilityLanes(lanes: CapabilityLane[]) {
  const preferredOrder = ["images", "meshes", "cad", "archives", "electronics", "print", "simulation", "documents"];
  const rank = new Map(preferredOrder.map((id, index) => [id, index]));
  return lanes
    .slice()
    .sort((a, b) => {
      if (a.currentCount !== b.currentCount) return b.currentCount - a.currentCount;
      return (rank.get(a.id) ?? 99) - (rank.get(b.id) ?? 99);
    })
    .slice(0, 6);
}

function fileBeginnerInfo(classification: IntakeFile["classification"]) {
  const labels: Record<IntakeFile["classification"], { plain: string }> = {
    image: { plain: "Image files can become visual reference planes inside a Blender scene." },
    mesh: { plain: "Mesh files can be opened as draft geometry for inspection and review." },
    cad: { plain: "CAD files can become derivative review packages; no dimensions or CAD truth are validated." },
    electronics: { plain: "Electronics files are recognized, but board/schematic routing is still blocked." },
    slicer: { plain: "Slicer files are recognized, but printer/profile routing is still blocked." },
    simulation: { plain: "Simulation or data files are recognized, but solver routing is still blocked." },
    document: { plain: "Documents are reference material until promoted into requirements or tasks." },
    archive: { plain: "Archives are staged unopened; extraction stays blocked until safe archive proof exists." },
    unsupported: { plain: "This file type has no verified work plan yet." },
  };
  return labels[classification];
}

function routeBeginnerInfo(target: string) {
  const labels: Record<string, { plain: string; creates: string; needs: string }> = {
    auto: {
      plain: "Auto checks the file types and chooses a proven image, mesh, or CAD derivative work plan only when it is safe.",
      creates: "Auto does not create output by itself; it chooses the safest proven work plan.",
      needs: "One supported file type in the intake folder.",
    },
    "blender-reference": {
      plain: "Use this when you have images and want a clean Blender reference scene.",
      creates: "This creates a Blender reference scene and review files from image inputs.",
      needs: "PNG, JPG, WEBP, BMP, TIF, or TIFF files.",
    },
    "mesh-review": {
      plain: "Use this when you have mesh files and want a draft review package.",
      creates: "This creates a Blender/FreeCAD review bundle from mesh inputs.",
      needs: "STL, OBJ, PLY, GLB, GLTF, or 3MF files.",
    },
    "cad-review": {
      plain: "Use this when you have CAD files and want a safe review package without conversion claims.",
      creates: "This copies CAD files into a dated review bundle with a manifest, review note, preview note, and design-task brief.",
      needs: "STEP, STP, IGES, IGS, BREP, FCStd, or OpenSCAD files only.",
    },
    "cad-derivative": {
      plain: "Use this when you have CAD files and want checked derivative outputs for review.",
      creates:
        "This copies CAD files into a dated package and attempts review-only STEP/BREP/STL or SCAD-to-STL derivatives with a manifest, comparison report, and tool log.",
      needs: "CAD-only intake plus detected FreeCADCmd for STEP/IGES/BREP/FCStd or OpenSCAD for SCAD.",
    },
    cad: {
      plain: "CAD truth and source-of-truth conversion are still not ready. Use CAD derivative only for review outputs.",
      creates: "No accepted CAD source model is created until CAD truth proof is built.",
      needs: "Units, scale, topology, and source/derivative comparison proof.",
    },
    electronics: {
      plain: "Electronics intake is visible for planning, but not executable yet.",
      creates: "No electronics output is created until the ECAD work-plan proof is built.",
      needs: "KiCad work-plan contract, checks, and output rules.",
    },
    print: {
      plain: "Print/slice intake is visible for planning, but not executable yet.",
      creates: "No print output is created until printer, material, and profile proof exists.",
      needs: "Slicer work-plan contract plus printer/material/profile proof.",
    },
    simulation: {
      plain: "Simulation intake is visible for planning, but not executable yet.",
      creates: "No solver result is created until simulation proof exists.",
      needs: "Solver, boundary condition, mesh, and validation rules.",
    },
    "archive-staging": {
      plain: "Archives can be recorded in the intake manifest, but they are not extracted yet.",
      creates: "No extracted files are created until archive safety proof exists.",
      needs: "Path traversal checks, size limits, nested archive policy, and manifest proof.",
    },
  };
  return labels[target] || {
    plain: "This work plan has no verified action yet.",
    creates: "No output is created until work-plan proof exists.",
    needs: "A work-plan contract and tests.",
  };
}

function toolLaunchPreview(
  tool: ToolHealth,
  selectedFile: IntakeFile | null,
  selectedRoute: string,
  intake: IntakeState,
  mode: ToolLaunchMode,
) {
  const toolName = displayToolName(tool.tool);
  const routeInfo = routeBeginnerInfo(selectedRoute);
  const preset = toolPresetName(tool.tool, selectedRoute, selectedFile?.classification);
  const selectedFileLabel = selectedFile
    ? `${selectedFile.name} (${formatClassification(selectedFile.classification)}, ${selectedFile.sizeLabel})`
    : "No selected input yet";
  const supportedCount = `${intake.counts.supported} supported file${intake.counts.supported === 1 ? "" : "s"}`;

  if (mode === "tool-only") {
    return {
      title: "Open tool only",
      flow: `${toolName} -> ${displayPathTail(tool.launchPathDisplay)}`,
      status: tool.launchable ? "Launchable" : "Blocked",
      statusClass: tool.launchable ? "ready" : "gated",
      detail: tool.launchable
        ? "This opens the detected GUI tool. It does not pass files or prove output behavior."
        : tool.launchReason,
    };
  }

  if (mode === "selected-input") {
    return {
      title: "Selected input setup",
      flow: `${selectedFileLabel} -> ${toolName} -> ${preset}`,
      status: selectedFile ? "Preview only" : "Select input",
      statusClass: "gated",
      detail: selectedFile
        ? "This shows the intended selected-input handoff. Today the proven backend still opens the tool only, so the selected file will not automatically appear inside the tool until a tool-specific launch contract passes."
        : "Select an intake file first. Direct file-to-tool launch stays not ready until each tool has a tested launch contract.",
    };
  }

  return {
    title: "Work plan preset",
    flow: `${supportedCount} -> ${routeInfo.needs} -> ${preset}`,
    status: selectedRoute === "auto" ? "Plan selection" : "Previewable",
    statusClass: selectedRoute === "auto" ? "gated" : "ready",
    detail:
      selectedRoute === "auto"
        ? "Auto chooses among proven review work plans only when the file mix is safe. It does not create output by itself."
        : `${routeInfo.creates} Preview work plan creates the dated job bundle; Open tool only launches the detected software for manual context.`,
  };
}

function toolHandoffForTool(
  handoffs: ToolHandoff[],
  toolName: string,
  selectedFile: IntakeFile | null,
  selectedRoute: string,
) {
  const selectedClassification = selectedFile?.classification;
  const routeMatches = handoffs.filter((handoff) => handoff.routeTarget === selectedRoute);
  const classMatches = selectedClassification
    ? handoffs.filter((handoff) => handoff.classification === selectedClassification)
    : [];
  if (selectedClassification) {
    return classMatches.find((handoff) => handoff.tool === toolName) || null;
  }
  const pools = [classMatches, routeMatches, handoffs];
  for (const pool of pools) {
    const direct = pool.find((handoff) => handoff.tool === toolName);
    if (direct) return direct;
  }
  for (const pool of pools) {
    const fallback = pool.find((handoff) => handoff.currentCount > 0);
    if (fallback) return fallback;
  }
  return handoffs.find((handoff) => handoff.tool === toolName) || handoffs[0] || null;
}

function friendlyHandoffStatus(status: string) {
  const labels: Record<string, string> = {
    gui_open_proven: "GUI open proven",
    not_proven_file_argument: "Not proven",
    not_required: "Not required",
    missing: "Missing",
    unavailable: "Unavailable",
    blocked: "Blocked",
  };
  return labels[status] || status.replaceAll("_", " ");
}

function handoffStatusClass(status: string) {
  if (status.includes("ready")) return "ready";
  if (status.includes("blocked") || status.includes("missing")) return "blocked";
  return "waiting";
}

function toolPresetName(tool: string, selectedRoute: string, classification?: IntakeFile["classification"]) {
  if (tool === "Blender" && selectedRoute === "blender-reference") return "Reference scene layout";
  if (tool === "Blender" && selectedRoute === "mesh-review") return "Draft mesh review view";
  if (tool === "MeshLab" && classification === "mesh") return "Manual mesh inspection";
  if (tool === "FreeCADCmd" && (classification === "cad" || selectedRoute.includes("cad"))) return "CAD review derivative checks";
  if (tool === "OpenSCAD" && (classification === "cad" || selectedRoute.includes("cad"))) return "Scripted CAD review";
  if (tool === "KiCad CLI") return "Electronics route gated";
  if (tool === "LTspice") return "Circuit simulation route gated";
  if (["PrusaSlicer", "CuraEngine", "OrcaSlicer"].includes(tool)) return "Slicer route gated";
  if (["Gmsh", "ParaView pvpython"].includes(tool)) return "Simulation/data route gated";
  if (classification) return `${formatClassification(classification)} review context`;
  return "General tool context";
}

function toolBeginnerUse(tool: string) {
  const labels: Record<string, string> = {
    Blender: "Visual reference scenes, layout, inspection, and rendering.",
    FreeCADCmd: "Parametric CAD checks and future CAD automation.",
    "KiCad CLI": "Circuit board and schematic project checks.",
    OpenSCAD: "Scripted parametric CAD models.",
    "ParaView pvpython": "Simulation and field-data visualization.",
    PrusaSlicer: "Prepare verified models for 3D printing.",
    CuraEngine: "Slice models for Cura-style print workflows.",
    OrcaSlicer: "Slice models for modern printer profiles.",
    Gmsh: "Generate meshes for geometry and simulation work.",
    MeshLab: "Inspect and repair mesh files manually.",
    LTspice: "Circuit simulation for electronics work.",
    "Docker CLI": "Container runtime control after daemon proof.",
  };
  return labels[tool] || "Detected tool; workflow-specific use is not defined yet.";
}

function toolHealthLabel(tool: ToolHealth) {
  if (tool.health === "detected") return "Ready where plans allow";
  if (tool.health === "manual") return "Manual use only";
  if (tool.health === "candidate") return "Needs plan proof";
  if (tool.health === "blocked") return "Blocked";
  return "Missing";
}

function summarizeTools(state: AppState | null) {
  if (!state) return { detected: 0, manual: 0, candidate: 0, blocked: 0 };
  return {
    detected: state.tools.filter((tool) => tool.health === "detected").length,
    manual: state.tools.filter((tool) => tool.health === "manual").length,
    candidate: state.tools.filter((tool) => tool.health === "candidate").length,
    blocked: state.tools.filter((tool) => tool.health === "blocked").length,
  };
}

function orderTools(tools: ToolHealth[]) {
  const order = [
    "Blender",
    "FreeCADCmd",
    "KiCad CLI",
    "OpenSCAD",
    "ParaView pvpython",
    "PrusaSlicer",
    "CuraEngine",
    "OrcaSlicer",
    "Gmsh",
    "MeshLab",
    "LTspice",
  ];
  return [...tools].sort((left, right) => {
    const a = order.indexOf(left.tool);
    const b = order.indexOf(right.tool);
    return (a === -1 ? 99 : a) - (b === -1 ? 99 : b) || left.tool.localeCompare(right.tool);
  });
}

function carouselToolsForRoute(tools: ToolHealth[], selectedRoute: string) {
  const byName = new Map(tools.map((tool) => [tool.tool, tool]));
  const routePriority: Record<string, string[]> = {
    "blender-reference": ["Blender", "FreeCADCmd", "MeshLab", "Gmsh"],
    "mesh-review": ["Blender", "MeshLab", "FreeCADCmd", "Gmsh"],
    "cad-review": ["FreeCADCmd", "OpenSCAD", "Gmsh", "Blender"],
    "cad-derivative": ["FreeCADCmd", "OpenSCAD", "Gmsh", "Blender"],
    electronics: ["KiCad CLI", "LTspice", "Arduino CLI"],
    print: ["PrusaSlicer", "OrcaSlicer", "CuraEngine", "MeshLab"],
    simulation: ["Gmsh", "ParaView pvpython", "FreeCADCmd"],
  };
  const priority = routePriority[selectedRoute] || ["Blender", "FreeCADCmd", "KiCad CLI", "OpenSCAD"];
  const chosen: ToolHealth[] = [];
  for (const name of priority) {
    const tool = byName.get(name);
    if (tool && (tool.iconUrl || isPrimaryTool(tool.tool))) {
      chosen.push(tool);
    }
  }
  for (const tool of orderTools(tools)) {
    if (!chosen.some((item) => item.tool === tool.tool) && (tool.iconUrl || isPrimaryTool(tool.tool))) {
      chosen.push(tool);
    }
  }
  return chosen;
}

function prioritizeOutputs(outputs: LatestJob["availableOutputs"]) {
  const order = ["folder", "preview", "blend", "review", "comparison", "manifest", "toolLog", "inventory", "designTask"];
  return [...outputs].sort((left, right) => {
    const leftIndex = order.indexOf(left.key);
    const rightIndex = order.indexOf(right.key);
    return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex) || left.label.localeCompare(right.label);
  });
}

function primaryJobOutput(job: LatestJob) {
  return prioritizeOutputs(job.availableOutputs).find((output) => ["preview", "blend", "comparison", "review", "folder"].includes(output.key));
}

function latestJobPlanLabel(job: LatestJob, routes: RouteCard[], fallbackTarget = "") {
  const selected = job.selectedRoute || fallbackTarget;
  if (!selected) return "latest job";
  const route = routes.find((item) => item.target === selected);
  if (route?.label) return route.label;
  const normalized = selected.replaceAll("-", " ");
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function jobBoundaryCopy(selectedRoute: string) {
  const labels: Record<string, string> = {
    "blender-reference":
      "For a Blender reference job, the output preview is a reference board made from the input image and the Blender file is an image-plane work scene with camera/guides. It is not CAD, measurement proof, or manufacturing-ready output.",
    "mesh-review":
      "For a mesh review job, outputs are a draft review package for inspection. They do not prove repair, print readiness, tolerances, or manufacturing correctness.",
    "cad-review":
      "For a CAD review job, outputs preserve and package CAD inputs for review. They do not prove source-of-truth CAD, dimensions, materials, tolerances, or build readiness.",
    "cad-derivative":
      "For a CAD derivative review job, outputs are comparison/review evidence only. They do not prove CAD truth, accepted units, manufacturing readiness, or physical correctness.",
  };
  return labels[selectedRoute] || "This output is a review/proof bundle for the selected work plan. It does not prove CAD, print, simulation, manufacturing, build, flight, or physical readiness.";
}

function outputOpenNotice(kind: string, pathDisplay: string) {
  const messages: Record<string, string> = {
    Folder: "Opened latest job folder.",
    Review: "Opened review note.",
    Preview: "Opened generated preview image.",
    Blend: "Opened Blender work scene. This is reference/review output, not CAD proof.",
    Inventory: "Opened scene inventory.",
    DesignTask: "Opened design task brief.",
    Manifest: "Opened derivative manifest.",
    ToolLog: "Opened tool log.",
    Comparison: "Opened comparison report. It is review evidence, not CAD truth.",
  };
  return `${messages[kind] || "Opened output."} ${pathDisplay}`;
}

function friendlyOutputAction(output: LatestJob["availableOutputs"][number]) {
  const labels: Record<string, string> = {
    folder: "Open job folder",
    preview: "View preview image",
    blend: "Open Blender scene",
    review: "Read review note",
    inventory: "Scene inventory",
    designTask: "Design task brief",
    comparison: "Comparison report",
    manifest: "Manifest",
    toolLog: "Tool log",
  };
  return labels[output.key] || output.label.replace(/^Open\s+/i, "");
}

function outputActionHint(output: LatestJob["availableOutputs"][number]) {
  const hints: Record<string, string> = {
    folder: "All files from this run.",
    preview: "Generated reference board.",
    blend: "Image-plane work scene.",
    review: "Human-readable proof note.",
    inventory: "Scene object list.",
    designTask: "Reference-to-design brief.",
    comparison: "Review evidence only.",
    manifest: "Generated file list.",
    toolLog: "Captured tool output.",
  };
  return hints[output.key] || output.openKind;
}

function isPrimaryTool(tool: string) {
  return [
    "Blender",
    "FreeCADCmd",
    "KiCad CLI",
    "OpenSCAD",
    "ParaView pvpython",
    "PrusaSlicer",
    "CuraEngine",
    "OrcaSlicer",
    "Gmsh",
    "MeshLab",
    "LTspice",
  ].includes(tool);
}

function displayToolName(tool: string) {
  const labels: Record<string, string> = {
    FreeCADCmd: "FreeCAD",
    "KiCad CLI": "KiCad",
    "ParaView pvpython": "ParaView",
    CuraEngine: "Cura",
  };
  return labels[tool] || tool;
}

function initials(text: string) {
  return text
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

function formatClassification(classification: IntakeFile["classification"]) {
  const labels: Record<IntakeFile["classification"], string> = {
    image: "Image",
    mesh: "Mesh",
    cad: "CAD",
    electronics: "Electronics",
    slicer: "Slicer",
    simulation: "Simulation/data",
    document: "Document",
    archive: "Archive",
    unsupported: "Unsupported",
  };
  return labels[classification];
}

function shortGate(routeId: string) {
  if (!routeId) return "proof pending";
  if (routeId.includes("BLENDER-REFERENCE")) return "DMI-BLENDER-001";
  if (routeId.includes("BLENDER-MESH")) return "DMI-MESH-002";
  if (routeId.includes("CAD-DERIVATIVE")) return "MA-CAD-DERIV-001";
  if (routeId.includes("CAD-REVIEW")) return "MA-CAD-REVIEW-001";
  return routeId;
}

function shortHash(hash: string) {
  if (!hash) return "not available";
  if (hash.length <= 24) return hash;
  return `${hash.slice(0, 12)}...${hash.slice(-8)}`;
}

function displayPathTail(pathDisplay: string) {
  if (!pathDisplay) return "Not set";
  const parts = pathDisplay.split(/[\\/]/).filter(Boolean);
  return parts.slice(-2).join("\\") || pathDisplay;
}

function formatStatusLabel(status: string) {
  return status.replaceAll("_", " ");
}

function friendlyProofText(value: string) {
  return value.replace(/\bgates?\b/gi, (match) => (match.toLowerCase().endsWith("s") ? "proof rules" : "proof"));
}

function iconForClassification(classification: IntakeFile["classification"], size = 24): ReactNode {
  const props = { size, "aria-hidden": true as const };
  if (classification === "image") return <ImageIcon {...props} />;
  if (classification === "mesh") return <Box {...props} />;
  if (classification === "cad") return <Package {...props} />;
  if (classification === "electronics") return <CircuitBoard {...props} />;
  if (classification === "slicer") return <Printer {...props} />;
  if (classification === "simulation") return <Wind {...props} />;
  if (classification === "document") return <FileText {...props} />;
  if (classification === "archive") return <Package {...props} />;
  return <Database {...props} />;
}

function routeIcon(target: string) {
  if (target === "blender-reference") return <ImageIcon size={20} aria-hidden="true" />;
  if (target === "mesh-review") return <Box size={20} aria-hidden="true" />;
  if (target === "cad" || target === "cad-review" || target === "cad-derivative") return <Package size={20} aria-hidden="true" />;
  if (target === "electronics") return <CircuitBoard size={20} aria-hidden="true" />;
  if (target === "print") return <Printer size={20} aria-hidden="true" />;
  if (target === "simulation") return <Wind size={20} aria-hidden="true" />;
  if (target === "auto") return <Activity size={20} aria-hidden="true" />;
  return <Cpu size={20} aria-hidden="true" />;
}

const HELP: Record<string, HelpContent> = {
  workspace: {
    title: "Makers Anvil",
    summary: "Local workbench for intake, work plans, tool launch, outputs, and proof.",
    purpose: "Keep the user flow visual and simple while preserving work-plan proof behind the scenes.",
    input: "Drop-folder files, local tool detection, latest job outputs, and work-plan state.",
    output: "A workbench view with previews, plan status, tool icons, and safe next actions.",
    blocker: "Clean-machine install, packaged release, CAD truth, and electronics/slicer/simulation work remain blocked.",
    boundary: "This control panel does not make engineering, manufacturing, solver, or physical readiness claims.",
  },
  startGuide: {
    title: "Intake status",
    summary: "A live status view: files, type, and next safe action.",
    purpose: "Keep the main screen understandable without requiring a manual or guessing what to click next.",
    input: "Current intake files and selected work plan.",
    output: "Plain-language next steps and honest plan status.",
    blocker: "If a plan is not proven, the guide says it is blocked instead of pretending it works.",
    boundary: "The guide explains workflow only; it does not validate engineering correctness.",
  },
  references: {
    title: "Selected input",
    summary: "Shows the selected raw source file without mixing it with generated outputs.",
    purpose: "Let the user cycle files and confirm the exact input before a work plan runs.",
    input: "Files in the active intake folder.",
    output: "A selected preview with classification, size, plan, status, and hash summary.",
    blocker: "Non-image previews remain deterministic icons until workflow-specific preview generation exists.",
    boundary: "Input previews are not dimensions, CAD truth, or simulation evidence.",
  },
  routeStatus: {
    title: "Current plan",
    summary: "Turn the current file mix into one clear next action.",
    purpose: "Show whether the selected work plan is ready, blocked, or review-only.",
    input: "File classifications, work-plan proof, and latest job state.",
    output: "A plain next step plus work-plan boundary and proof details.",
    blocker: "Mixed or unsupported batches stay blocked until workflow-specific proof exists.",
    boundary: "Ready means runnable work plan only, not build or design correctness.",
  },
  routeQueue: {
    title: "Work plans",
    summary: "Only proven work plans can run or preview.",
    purpose: "Give the plan list its own workspace so allowed, waiting, and blocked jobs are readable.",
    input: "Current plan cards and intake state.",
    output: "Preview plan or Waiting buttons for allowed review jobs; blocked labels for work that needs proof first.",
    blocker: "CAD truth, electronics, print, and simulation work need their own contracts.",
    boundary: "Blocked work plans are visible for planning but do not execute.",
  },
  tools: {
    title: "Tools",
    summary: "Cycle through available local tools without filling the workbench.",
    purpose: "Help users recognize which installed tools are available and open the right one without fake logos.",
    input: "Current local tool detection and extracted icon assets.",
    output: "A carousel using installed-app icons or exact-name fallback initials.",
    blocker: "A missing executable or icon extraction failure must not create an invented logo.",
    boundary: "Detected tools do not prove workflow correctness or output validity.",
  },
  inspector: {
    title: "Work preview",
    summary: "Expected output meaning, current plan, selected tool context, and boundaries.",
    purpose: "Keep the plan, generated-output meaning, selected local tool, and blocked claims close to the workbench.",
    input: "Selected intake file, selected work plan, and selected tool.",
    output: "Job-preview detail panel with hash, plan, tool context, boundary, and next step.",
    blocker: "Tool-specific previews wait for workflow-specific proof.",
    boundary: "Preview details are local state, not engineering validation.",
  },
  reviewAction: {
    title: "Check input files",
    summary: "Inspect before running.",
    purpose: "Review current files and work-plan boundaries.",
    input: "Selected intake files.",
    output: "Dev plan/file details.",
    blocker: "No files means there is nothing to review.",
    boundary: "Review does not modify originals.",
  },
  buildAction: {
    title: "Preview work plan",
    summary: "Review a work plan before it can run.",
    purpose: "Open a job preview for the selected runnable work plan.",
    input: "Image-only, mesh-only, or CAD-only intake state.",
    output: "Reference/review job bundle after confirmation.",
    blocker: "Mixed, unsupported, electronics, print, simulation, and CAD truth work remains blocked.",
    boundary: "The output is reference or draft review only.",
  },
  toolAction: {
    title: "Open tools",
    summary: "Focus the verified local tools area.",
    purpose: "Move focus to the Tools carousel without running conversion.",
    input: "Local tool detection state.",
    output: "Selected tool context and detection boundaries.",
    blocker: "Tool launch automation remains workflow-specific.",
    boundary: "Opening a tool does not prove any design.",
  },
};
