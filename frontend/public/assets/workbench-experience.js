/**
 * Purpose: Apply, edit, and explain portable workbench presentation preferences.
 * Used by: The Dev settings panel, notice strip, and recent activity section.
 * Inputs: Experience/activity API records, process token, and refresh callback.
 * Outputs: DOM data attributes, segmented controls, notices, and activity rows.
 * Side effects: One explicit save can POST the complete preference object.
 * Safety: The request is same-origin/token-guarded and contains no path or action.
 * Failure behavior: Failed saves show a notice and retain server-confirmed state.
 * Related proof: Experience API tests and browser interaction checks.
 */

import { configureContextHelp } from "./context-help.js";

let confirmedPreferences = { density: "compact", motion: "full", contextHelp: true };
let saveToken = "";
let refreshAfterSave = async () => {};
let noticeTimer = null;

/**
 * Purpose: Apply server-confirmed presentation preferences to the document root.
 * Inputs: Exact density, motion, and contextual-help values.
 * Outputs: Updated data attributes used by CSS and help visibility.
 * How it works: Assigns only closed server-validated values.
 * Side effects: Changes layout density, animation policy, and help-button display.
 * Failure behavior: Missing values use conservative compact/reduced/help defaults.
 * Safety: Presentation attributes cannot enable maker operations.
 * Example: Reduced motion disables decorative pulses and transitions.
 * Related proof: Browser preference and reduced-motion checks.
 */
function applyPreferences(preferences, helpTopics) {
  confirmedPreferences = {
    density: preferences?.density === "comfortable" ? "comfortable" : "compact",
    motion: preferences?.motion === "full" ? "full" : "reduced",
    contextHelp: preferences?.contextHelp !== false,
  };
  document.documentElement.dataset.density = confirmedPreferences.density;
  document.documentElement.dataset.motion = confirmedPreferences.motion;
  document.documentElement.dataset.contextHelp = String(confirmedPreferences.contextHelp);
  configureContextHelp(helpTopics, confirmedPreferences.contextHelp);
}

/**
 * Purpose: Display a short nonblocking result notice at the top of the shell.
 * Inputs: Reviewed message and success/error tone.
 * Outputs: Visible live-region notice that dismisses automatically.
 * How it works: Resets the prior timer, sets safe text/class, then hides later.
 * Side effects: Updates notice DOM and creates one browser timer.
 * Failure behavior: Missing notice element makes the function a no-op.
 * Safety: Message uses textContent and does not contain source paths.
 * Example: Successful preference save reports "Workbench settings saved."
 * Related proof: Browser live-region interaction checks.
 */
export function showWorkbenchNotice(message, tone = "success") {
  const notice = document.querySelector("#workbench-notice");
  if (!notice) return;
  window.clearTimeout(noticeTimer);
  notice.textContent = message;
  notice.className = `workbench-notice ${tone}`;
  notice.hidden = false;
  noticeTimer = window.setTimeout(() => { notice.hidden = true; }, 4200);
}

/**
 * Purpose: Save the exact settings control values through the guarded endpoint.
 * Inputs: Current radio/toggle controls and process-local token from intake session.
 * Outputs: Updated experience or visible failure notice followed by state refresh.
 * How it works: Builds a complete payload, posts JSON same-origin, and checks status.
 * Side effects: Performs one guarded POST and then invokes the refresh callback.
 * Failure behavior: Error response text is not trusted; a reviewed message is shown.
 * Safety: Payload has three presentation values and no arbitrary key or private data.
 * Example: Save can persist compact, reduced, and contextHelp false together.
 * Related proof: API payload validation and browser save tests.
 */
async function savePreferences() {
  const payload = {
    density: document.querySelector("input[name='density']:checked")?.value || confirmedPreferences.density,
    motion: document.querySelector("input[name='motion']:checked")?.value || confirmedPreferences.motion,
    contextHelp: document.querySelector("#context-help-setting").checked,
  };
  const button = document.querySelector("#save-experience-settings");
  button.disabled = true;
  try {
    const response = await fetch("/api/workbench/experience", {
      method: "POST",
      cache: "no-store",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-Makers-Anvil-Request-Token": saveToken },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("preference save rejected");
    showWorkbenchNotice("Workbench settings saved.");
    await refreshAfterSave();
  } catch (error) {
    showWorkbenchNotice("Workbench settings were not saved.", "error");
  } finally {
    button.disabled = false;
  }
}

/**
 * Purpose: Render confirmed settings and bind the save command once.
 * Inputs: Experience response, local process token, and state-refresh callback.
 * Outputs: Synchronized controls, storage label, help behavior, and bound save.
 * How it works: Applies preferences, checks matching inputs, then stores dependencies.
 * Side effects: Updates controls and may add one click listener.
 * Failure behavior: Missing response fields render conservative defaults.
 * Safety: Token remains in module memory and is never rendered or persisted.
 * Example: Called on every loadState refresh with intake session requestToken.
 * Related proof: Frontend token privacy and settings interaction tests.
 */
export function renderWorkbenchExperience(experience = {}, requestToken = "", refresh = async () => {}) {
  saveToken = requestToken;
  refreshAfterSave = refresh;
  applyPreferences(experience.preferences || confirmedPreferences, experience.helpTopics || []);
  document.querySelectorAll("input[name='density']").forEach((input) => { input.checked = input.value === confirmedPreferences.density; });
  document.querySelectorAll("input[name='motion']").forEach((input) => { input.checked = input.value === confirmedPreferences.motion; });
  document.querySelector("#context-help-setting").checked = confirmedPreferences.contextHelp;
  document.querySelector("#experience-storage").textContent = experience.storage || "app-owned settings";
  const button = document.querySelector("#save-experience-settings");
  if (button.dataset.bound !== "true") {
    button.dataset.bound = "true";
    button.addEventListener("click", savePreferences);
  }
}

/**
 * Purpose: Render recent redacted activity in newest-first order.
 * Inputs: Valid activity-history response with fixed server-authored events.
 * Outputs: Count, logical storage label, and timestamped activity rows.
 * How it works: Creates semantic time/copy nodes with textContent only.
 * Side effects: Replaces children of the activity list and updates two labels.
 * Failure behavior: Empty/missing records show an honest no-activity message.
 * Safety: Event contracts contain no paths, tokens, file content, or arbitrary text.
 * Example: A completed intake copy appears as one fixed reviewed summary.
 * Related proof: Activity schema/service tests and browser rendering checks.
 */
export function renderActivityHistory(history = {}) {
  const events = Array.isArray(history.events) ? history.events : [];
  const target = document.querySelector("#activity-list");
  document.querySelector("#activity-count").textContent = `${events.length} recent`;
  document.querySelector("#activity-location").textContent = history.logicalRoot || "app-owned activity";
  target.replaceChildren();
  if (!events.length) {
    const empty = document.createElement("p");
    empty.className = "activity-empty";
    empty.textContent = "No completed local actions yet.";
    target.append(empty);
    return;
  }
  events.forEach((event) => {
    const row = document.createElement("article");
    row.className = "activity-row";
    const copy = document.createElement("span");
    copy.textContent = event.summary;
    const time = document.createElement("time");
    time.dateTime = event.timestampUtc;
    time.textContent = new Date(event.timestampUtc).toLocaleString();
    row.append(copy, time);
    target.append(row);
  });
}
