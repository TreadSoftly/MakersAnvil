/**
 * Purpose: Render Windows installer readiness and clean-machine scenarios as read-only evidence.
 * Used by: The Dev workbench after focused installer API reads complete.
 * Inputs: Schema-backed readiness and clean-machine harness records.
 * Outputs: Text-only gate and scenario cards inside existing semantic regions.
 * Side effects: Replaces DOM children in the two installer evidence lists.
 * Safety: Creates no installer, signing, upgrade, removal, repair, publish, or harness command.
 * Failure behavior: Missing records render conservative zero and blocked text.
 * Related proof: Frontend structure, purity, API, and responsive verifier tests.
 */

/**
 * Purpose: Build one compact truth badge without interpreting it as an action.
 * Inputs: Claim-state text from a validated installer response.
 * Outputs: Span element using the shared badge vocabulary.
 * How it works: Applies text and a known-safe lowercase class.
 * Side effects: Allocates one detached DOM node.
 * Failure behavior: Missing state becomes unknown.
 * Safety: Text-only rendering cannot invoke a package operation.
 * Example: A blocked signing gate receives the blocked badge style.
 * Related proof: Frontend installer card tests.
 */
function badge(claimState) {
  const node = document.createElement("span");
  const state = typeof claimState === "string" ? claimState : "unknown";
  node.className = `badge ${state.replace(" ", "-")}`;
  node.textContent = state;
  return node;
}

/**
 * Purpose: Render one readiness gate with its exact current evidence.
 * Inputs: Gate object containing label, claim state, and evidence text.
 * Outputs: Detached installer evidence row.
 * How it works: Uses textContent for all server-provided values.
 * Side effects: Allocates DOM nodes only.
 * Failure behavior: Absent fields receive conservative fallback labels.
 * Safety: No HTML injection or control element is created.
 * Example: Trusted signature displays blocked and its missing-proof explanation.
 * Related proof: DOM token and purity tests.
 */
function renderGate(gate = {}) {
  const row = document.createElement("article");
  row.className = "installer-evidence-row";
  const head = document.createElement("div");
  const title = document.createElement("strong");
  const evidence = document.createElement("p");
  title.textContent = gate.label || "Unnamed installer gate";
  evidence.textContent = gate.evidence || "Evidence is not proven.";
  head.append(title, badge(gate.claimState));
  row.append(head, evidence);
  return row;
}

/**
 * Purpose: Render one planned clean-machine scenario and its assertion count.
 * Inputs: Scenario object with label, purpose, assertions, and execution state.
 * Outputs: Detached scenario row.
 * How it works: Summarizes array length and uses text-only DOM APIs.
 * Side effects: Allocates DOM nodes only.
 * Failure behavior: Missing arrays become zero assertions and not-run truth.
 * Safety: Scenario cards never become execution controls.
 * Example: Fresh install displays three assertions and not-run.
 * Related proof: Frontend installer structure tests.
 */
function renderScenario(scenario = {}) {
  const row = document.createElement("article");
  row.className = "installer-evidence-row";
  const head = document.createElement("div");
  const title = document.createElement("strong");
  const purpose = document.createElement("p");
  const assertions = Array.isArray(scenario.assertions) ? scenario.assertions : [];
  title.textContent = scenario.label || "Unnamed clean-machine scenario";
  purpose.textContent = `${scenario.purpose || "No purpose recorded."} · ${assertions.length} assertions`;
  head.append(title, badge(scenario.executionState === "not-run" ? "planned" : "unknown"));
  row.append(head, purpose);
  return row;
}

/**
 * Purpose: Synchronize the complete Windows release-foundation evidence panel.
 * Inputs: Installer readiness and clean-machine harness API records.
 * Outputs: Updated totals, identity truth, gates, scenarios, and safety boundary.
 * How it works: Clears two fixed lists and appends text-only rows in API order.
 * Side effects: Mutates only the installer panel DOM.
 * Failure behavior: Missing payloads remain visibly blocked and unproven.
 * Safety: Never creates buttons, links, form fields, commands, or mutation requests.
 * Example: Three of nine foundation gates and zero of six scenarios are shown.
 * Related proof: API consistency and frontend workbench tests.
 */
export function renderWindowsInstaller(readiness = {}, harness = {}) {
  const summary = readiness.summary || {};
  const harnessSummary = harness.summary || {};
  const identity = readiness.identity || {};
  const gateList = document.getElementById("windows-installer-gates");
  const scenarioList = document.getElementById("clean-machine-scenarios");
  const stateBadge = document.getElementById("windows-installer-state");
  const state = typeof readiness.claimState === "string" ? readiness.claimState : "unknown";
  stateBadge.className = `badge ${state.replace(" ", "-")}`;
  stateBadge.textContent = state;
  document.getElementById("windows-installer-summary").textContent = `${summary.passedGateCount || 0}/${summary.gateCount || 0} gates passed · installer blocked`;
  document.getElementById("windows-installer-identity").textContent = `${identity.name || "identity not proven"} · publisher ${identity.publisher || "not-proven"}`;
  document.getElementById("clean-machine-summary").textContent = `${harnessSummary.executedCount || 0}/${harnessSummary.scenarioCount || 0} scenarios run · clean-machine proof false`;
  gateList.replaceChildren(...(Array.isArray(readiness.gates) ? readiness.gates.map(renderGate) : []));
  scenarioList.replaceChildren(...(Array.isArray(harness.scenarios) ? harness.scenarios.map(renderScenario) : []));
  document.getElementById("windows-installer-boundary").textContent = "Foundation only · no installer build/run, signing, registration, upgrade, repair, removal, publication, process, or user-data deletion";
}
