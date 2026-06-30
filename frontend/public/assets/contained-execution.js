/**
 * Purpose: Render and operate the single contained built-in STL preflight.
 * Used by: app.js after intake, execution policy, and execution catalog reads.
 * Inputs: Path-redacted API records, the process-local request token, and refresh callback.
 * Outputs: Eligible source commands, lifecycle rows, proof facts, and bounded notices.
 * Side effects: May POST exact authorize, run, or cooperative-cancel requests on user command.
 * Safety: Never accepts a path, starts a process/tool, generates toolpaths, or opens output.
 * Failure behavior: HTTP/service failures remain visible and trigger no optimistic success state.
 * Related proof: Frontend purity tests, API integration tests, and browser smoke proof.
 */

import { showWorkbenchNotice } from "./workbench-experience.js";

/**
 * Purpose: Send one same-origin contained-execution command with the shared guard token.
 * Inputs: Exact endpoint, in-memory token, and optional schema-shaped JSON payload.
 * Outputs: Parsed successful JSON response.
 * How it works: Uses POST, no-store, the request token, and JSON only when required.
 * Side effects: Invokes one server-authorized contained execution mutation.
 * Failure behavior: Throws the server's path-free message or a stable fallback.
 * Safety: Endpoints originate from committed policy and payloads contain generated ids only.
 * Example: ``postCommand('/api/executions/.../run', token)`` runs one preflight.
 * Related proof: API media-type, body, guard, and unknown-route tests.
 */
async function postCommand(endpoint, token, payload = null) {
  const options = {
    method: "POST",
    cache: "no-store",
    headers: { "X-Makers-Anvil-Request-Token": token },
  };
  if (payload !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(payload);
  }
  const response = await fetch(endpoint, options);
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.message || "Contained preflight command failed.");
  }
  return result;
}

/**
 * Purpose: Build a familiar command button without interpreting runtime text as markup.
 * Inputs: Visible label, CSS class, click callback, and optional accessible title.
 * Outputs: Native button element with one bounded listener.
 * How it works: Assigns properties and registers the supplied local callback.
 * Side effects: Allocates one DOM node and event listener.
 * Failure behavior: Callback errors are handled by the caller's command wrapper.
 * Safety: Labels use textContent; no runtime HTML or executable string is accepted.
 * Example: Creates the Run preflight button for an authorized execution.
 * Related proof: Frontend DOM purity and command-count tests.
 */
function commandButton(label, className, onClick, title = label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.title = title;
  button.addEventListener("click", onClick);
  return button;
}

/**
 * Purpose: Run one user-selected command with notice, refresh, and duplicate-click control.
 * Inputs: Clicked button, promise-returning operation, success text, and refresh callback.
 * Outputs: Promise resolving after success refresh or visible failure notice.
 * How it works: Disables the button during the request and restores it on failure.
 * Side effects: Performs the supplied mutation, updates notice DOM, and may refresh GET state.
 * Failure behavior: Catches request errors and displays their stable message.
 * Safety: It cannot choose an operation; the caller supplies one closed API action.
 * Example: Authorize, Run, and Cancel all use the same busy-state behavior.
 * Related proof: Browser interaction smoke and API failure assertions.
 */
async function performCommand(button, operation, successText, refresh) {
  button.disabled = true;
  try {
    await operation();
    showWorkbenchNotice(successText);
    await refresh();
  } catch (error) {
    button.disabled = false;
    showWorkbenchNotice(error instanceof Error ? error.message : "Contained preflight command failed.", true);
  }
}

/**
 * Purpose: Render eligible STL sources and every contained preflight lifecycle record.
 * Inputs: Policy/catalog/intake snapshots, memory-only token, and whole-state refresh callback.
 * Outputs: Updated badge, summary, source controls, execution rows, and honesty boundary.
 * How it works: Joins records by intake id, creates text-only facts, and binds closed commands.
 * Side effects: Replaces owned DOM children and registers command listeners.
 * Failure behavior: Missing contracts render unavailable/empty rather than enabling actions.
 * Safety: Only authorized app-owned .stl records qualify; full routes and tools stay absent.
 * Example: A copied part.stl can be authorized, preflighted, and shown with five audit events.
 * Related proof: Contained execution service tests and browser viewport verification.
 */
export function renderContainedExecutions(policy, catalog, intake, token, refresh) {
  const state = document.querySelector("#contained-execution-state");
  const summary = document.querySelector("#contained-execution-summary");
  const eligibleTarget = document.querySelector("#contained-execution-eligible");
  const listTarget = document.querySelector("#contained-execution-list");
  const boundary = document.querySelector("#contained-execution-boundary");
  if (!state || !summary || !eligibleTarget || !listTarget || !boundary) {
    return;
  }

  const valid = policy?.schemaVersion === "makers-anvil.config.contained-execution.v1"
    && catalog?.schemaVersion === "makers-anvil.api.contained-execution-catalog.v1";
  state.textContent = valid ? catalog.claimState : "unknown";
  state.className = `badge ${catalog?.claimState === "staged" ? "staged" : "unknown"}`;
  const facts = catalog?.summary || {};
  summary.textContent = `${facts.executionCount || 0} records · ${facts.proofCount || 0} proofs`;
  boundary.textContent = "Built-in STL structure check only · no slicing, G-code, tool launch, output opening, or full route completion";
  eligibleTarget.replaceChildren();
  listTarget.replaceChildren();

  const executions = valid ? catalog.executions || [] : [];
  const usedIntakes = new Set(executions.map((item) => item.record?.source?.intakeId));
  const eligible = (intake?.records || []).filter((record) => record.schemaVersion === "makers-anvil.runtime.authorized-intake-record.v1"
    && record.source?.kind === "mesh" && record.source?.extension === ".stl" && !usedIntakes.has(record.id));
  eligible.forEach((record) => {
    const row = document.createElement("article");
    row.className = "contained-execution-item";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = record.source.displayName;
    const detail = document.createElement("span");
    detail.textContent = "Authorized app copy · ready for preflight consent";
    copy.append(title, detail);
    const button = commandButton("Authorize preflight", "authorize-command", (event) => performCommand(
      event.currentTarget,
      () => postCommand(policy.endpoints.authorize, token, {
        intakeId: record.id,
        routeId: policy.scope.routeId,
        operationId: policy.scope.operationId,
        accepted: true,
      }),
      "STL preflight authorized.",
      refresh,
    ));
    button.disabled = !token;
    row.append(copy, button);
    eligibleTarget.append(row);
  });

  if (!eligible.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No unassigned authorized STL is ready for preflight.";
    eligibleTarget.append(empty);
  }

  executions.forEach((item) => {
    const record = item.record;
    const row = document.createElement("article");
    row.className = "contained-execution-item";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = record.source.displayName;
    const detail = document.createElement("span");
    const auditCount = item.audit?.summary?.eventCount || 0;
    detail.textContent = `${record.lifecycle.state} · ${auditCount} audit events · ${record.proof ? `${record.proof.outcome} proof` : "proof pending"}`;
    copy.append(title, detail);
    const commands = document.createElement("div");
    commands.className = "contained-execution-commands";
    if (record.lifecycle.state === "authorized") {
      commands.append(commandButton("Run preflight", "primary-command", (event) => performCommand(
        event.currentTarget,
        () => postCommand(policy.endpoints.runTemplate.replace("{executionId}", record.id), token),
        "STL preflight completed.",
        refresh,
      )));
    }
    if (["authorized", "running"].includes(record.lifecycle.state)) {
      commands.append(commandButton("×", "intake-cancel", (event) => performCommand(
        event.currentTarget,
        () => postCommand(policy.endpoints.cancelTemplate.replace("{executionId}", record.id), token),
        "STL preflight cancelled.",
        refresh,
      ), "Cancel contained preflight"));
    }
    row.append(copy, commands);
    listTarget.append(row);
  });

  if (!executions.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No contained preflight executions recorded.";
    listTarget.append(empty);
  }
}
