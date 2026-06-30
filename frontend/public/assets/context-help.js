/**
 * Purpose: Provide one accessible reusable contextual-help popover.
 * Used by: Help buttons placed beside major Makers Anvil workbench headings.
 * Inputs: Schema-backed help topics and buttons carrying ``data-help-topic`` ids.
 * Outputs: A positioned dialog containing reviewed summary and boundary text.
 * Side effects: Updates popover DOM, focus, and resize/outside-click listeners.
 * Safety: All topic text uses ``textContent`` and no maker action is available.
 * Failure behavior: Missing topics close the popover rather than inventing guidance.
 * Related proof: Frontend source tests and browser keyboard/viewport checks.
 */

let topicIndex = new Map();
let activeTrigger = null;

/**
 * Purpose: Position the popover beside its trigger while keeping it on screen.
 * Inputs: Current trigger rectangle, popover size, and browser viewport dimensions.
 * Outputs: Updated fixed ``left`` and ``top`` presentation values.
 * How it works: Prefers the trigger's right side and clamps both coordinates.
 * Side effects: Writes two inline CSS positioning properties.
 * Failure behavior: Missing trigger or hidden popover makes the function a no-op.
 * Safety: Geometry changes presentation only and cannot alter application state.
 * Example: A right-edge help button places the popover to its left.
 * Related proof: Desktop/mobile browser screenshot and overlap checks.
 */
function positionPopover() {
  const popover = document.querySelector("#context-help-popover");
  if (!activeTrigger || !popover || popover.hidden) return;
  const triggerRect = activeTrigger.getBoundingClientRect();
  const popoverRect = popover.getBoundingClientRect();
  const gutter = 12;
  const preferredLeft = triggerRect.right + gutter;
  const left = preferredLeft + popoverRect.width <= window.innerWidth - gutter
    ? preferredLeft
    : Math.max(gutter, triggerRect.left - popoverRect.width - gutter);
  const top = Math.min(Math.max(gutter, triggerRect.top), window.innerHeight - popoverRect.height - gutter);
  popover.style.left = `${left}px`;
  popover.style.top = `${Math.max(gutter, top)}px`;
}

/**
 * Purpose: Close contextual help and optionally restore keyboard focus.
 * Inputs: Boolean indicating whether the previously active trigger regains focus.
 * Outputs: Hidden popover, cleared expanded state, and cleared active trigger.
 * How it works: Updates ARIA/hidden state before releasing the trigger reference.
 * Side effects: Changes DOM visibility and may move browser focus.
 * Failure behavior: Repeated close calls safely do nothing beyond clearing state.
 * Safety: Closing help never sends a request or changes persisted preferences.
 * Example: Escape closes the dialog and returns focus to its information button.
 * Related proof: Browser keyboard assertions.
 */
function closeHelp(restoreFocus = false) {
  const popover = document.querySelector("#context-help-popover");
  const trigger = activeTrigger;
  if (popover) popover.hidden = true;
  if (trigger) trigger.setAttribute("aria-expanded", "false");
  activeTrigger = null;
  if (restoreFocus && trigger) trigger.focus();
}

/**
 * Purpose: Open one reviewed help topic from the schema-backed topic index.
 * Inputs: Clicked help button containing a known ``data-help-topic`` id.
 * Outputs: Visible labelled dialog with title, summary, and current boundary.
 * How it works: Looks up the topic, writes text safely, then positions the dialog.
 * Side effects: Updates DOM, ARIA expanded state, and active trigger memory.
 * Failure behavior: Unknown ids close existing help and produce no misleading text.
 * Safety: Uses textContent exclusively and exposes no executable control.
 * Example: Intake help explains explicit authorization and blocked folder import.
 * Related proof: Frontend rendering and browser interaction tests.
 */
function openHelp(trigger) {
  const topic = topicIndex.get(trigger.dataset.helpTopic);
  const popover = document.querySelector("#context-help-popover");
  if (!topic || !popover) {
    closeHelp();
    return;
  }
  if (activeTrigger && activeTrigger !== trigger) activeTrigger.setAttribute("aria-expanded", "false");
  activeTrigger = trigger;
  document.querySelector("#context-help-title").textContent = topic.title;
  document.querySelector("#context-help-summary").textContent = topic.summary;
  document.querySelector("#context-help-boundary").textContent = topic.boundary;
  trigger.setAttribute("aria-expanded", "true");
  popover.hidden = false;
  positionPopover();
  document.querySelector("#context-help-close").focus();
}

/**
 * Purpose: Initialize help controls once and replace their topic data on refresh.
 * Inputs: Valid public help-topic array and current context-help preference.
 * Outputs: Bound help buttons whose visibility follows the saved preference.
 * How it works: Rebuilds an id map and marks buttons once with listener state.
 * Side effects: Adds click/keyboard/resize listeners and changes button visibility.
 * Failure behavior: Invalid topic arrays become an empty map and close help.
 * Safety: Event handlers control only the local explanatory popover.
 * Example: Disabling contextHelp hides all information buttons immediately.
 * Related proof: Preference rendering and keyboard browser tests.
 */
export function configureContextHelp(topics, enabled) {
  topicIndex = new Map((Array.isArray(topics) ? topics : []).map((topic) => [topic.id, topic]));
  document.querySelectorAll("[data-help-topic]").forEach((button) => {
    button.hidden = !enabled;
    if (button.dataset.helpBound === "true") return;
    button.dataset.helpBound = "true";
    button.addEventListener("click", () => openHelp(button));
  });
  if (!enabled) closeHelp();
}

document.querySelector("#context-help-close")?.addEventListener("click", () => closeHelp(true));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && activeTrigger) closeHelp(true);
});
document.addEventListener("pointerdown", (event) => {
  const popover = document.querySelector("#context-help-popover");
  if (activeTrigger && popover && !popover.contains(event.target) && !activeTrigger.contains(event.target)) closeHelp();
});
window.addEventListener("resize", positionPopover);
