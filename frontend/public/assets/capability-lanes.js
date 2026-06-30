/**
 * Purpose: Render a compact capability comparison from the backend matrix.
 * Used by: The unframed Capability lanes band below local tool detection.
 * Inputs: ``makers-anvil.api.capability-matrix.v1`` JSON contract.
 * Outputs: Five stable lane rows plus ingress and honesty summaries.
 * Side effects: Replaces children inside owned capability DOM regions.
 * Safety: Text nodes prevent markup injection and no action control is rendered.
 * Failure behavior: Missing lanes render an honest unavailable message.
 * Related proof: Matrix schema/service tests and browser viewport checks.
 */

/**
 * Purpose: Create an element with optional class and safe text content.
 * Inputs: HTML tag, class token string, and display text.
 * Outputs: Detached DOM element ready for composition.
 * How it works: Uses createElement and textContent without HTML parsing.
 * Side effects: Allocates one browser DOM node only.
 * Failure behavior: Missing text becomes an empty string.
 * Safety: User-derived file metadata can never become executable markup.
 * Example: ``element('span', 'lane-count', '1 file')`` creates safe text.
 * Related proof: Frontend purity tests prohibit unsafe dynamic HTML here.
 */
function element(tag, className, text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = String(text ?? "");
  return node;
}

/**
 * Purpose: Build one stable capability lane from a validated lane record.
 * Inputs: Lane id, route, tool summary, counts, examples, and boundaries.
 * Outputs: An article containing comparable input/route/tool/proof columns.
 * How it works: Composes only fixed semantic elements and safe text nodes.
 * Side effects: Allocates detached DOM nodes.
 * Failure behavior: Missing optional values display zero or unavailable text.
 * Safety: Status labels are informative and never clickable.
 * Example: The image lane can show one preview-ready PNG and zero tools.
 * Related proof: Browser lane-count and overflow checks.
 */
function buildLane(lane) {
  const row = element("article", "capability-lane");
  const identity = element("div", "capability-lane-identity");
  identity.append(element("strong", "", lane.label), element("span", `lane-status ${lane.status}`, lane.status.replace("-", " ")));
  const inputs = element("div", "capability-lane-cell");
  inputs.append(element("span", "lane-label", "Inputs"), element("strong", "", `${lane.currentCount} current`), element("small", "", (lane.inputExamples || []).slice(0, 5).join("  ")));
  const route = element("div", "capability-lane-cell");
  route.append(element("span", "lane-label", "Plan"), element("strong", "", lane.route?.label || "Not mapped"), element("small", "", lane.route?.toolFamily || "No tool family"));
  const tools = element("div", "capability-lane-cell");
  tools.append(element("span", "lane-label", "Tools"), element("strong", "", `${lane.toolSummary?.detectedCount || 0}/${lane.toolSummary?.candidateCount || 0} detected`), element("small", "", "Detection only"));
  const proof = element("div", "capability-lane-cell");
  proof.append(element("span", "lane-label", "Outputs"), element("strong", "", `${lane.plannedOutputCount || 0} planned`), element("small", "", "Execution blocked"));
  row.append(identity, inputs, route, tools, proof);
  row.title = lane.nextStep || "Execution remains blocked.";
  return row;
}

/**
 * Purpose: Render the complete capability matrix into stable workbench regions.
 * Inputs: Valid matrix response or a conservative fallback object.
 * Outputs: Updated summary, ingress labels, lanes, and honesty footer.
 * How it works: Clears owned regions then appends one safe row per lane.
 * Side effects: Mutates only capability-band DOM children and text.
 * Failure behavior: Empty lanes show a single unavailable status line.
 * Safety: Rendering cannot authorize intake, execute routes, or launch tools.
 * Example: Called after each coherent API refresh.
 * Related proof: Frontend source tests and desktop/mobile screenshots.
 */
export function renderCapabilityMatrix(matrix = {}) {
  const lanes = Array.isArray(matrix.lanes) ? matrix.lanes : [];
  const target = document.querySelector("#capability-lane-list");
  const summary = matrix.summary || {};
  document.querySelector("#capability-matrix-state").textContent = matrix.claimState || "unknown";
  document.querySelector("#capability-matrix-state").className = `badge ${String(matrix.claimState || "unknown").replace(/\s+/g, "-")}`;
  document.querySelector("#capability-matrix-summary").textContent = `${summary.previewReadyLaneCount || 0}/${summary.laneCount || 0} lanes preview-ready`;
  document.querySelector("#capability-ingress").textContent = (matrix.ingressMethods || []).map((item) => `${item.label}: ${item.enabled ? "available" : "blocked"}`).join(" · ");
  target.replaceChildren();
  if (!lanes.length) {
    target.append(element("p", "capability-empty", "Capability lanes are unavailable."));
  } else {
    lanes.forEach((lane) => target.append(buildLane(lane)));
  }
  document.querySelector("#capability-honesty").textContent = (matrix.honesty || ["Execution remains blocked."]).join(" · ");
}
