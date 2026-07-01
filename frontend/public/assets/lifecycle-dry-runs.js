/**
 * Purpose: Render read-only backup, restore, update, uninstall, and repair previews.
 * Used by: app.js after lifecycle policy/catalog GET requests complete.
 * Inputs: Path-redacted lifecycle policy and current dry-run catalog records.
 * Outputs: Inventory summary, five plan cards, evidence, blockers, and preservation truth.
 * Side effects: Replaces only the owned lifecycle DOM regions.
 * Safety: Creates no command controls and performs no mutation, archive, network, or installer request.
 * Failure behavior: Missing or invalid contracts render unknown/empty truth without enabling actions.
 * Related proof: Frontend purity, target, responsive, and lifecycle API tests.
 */

/**
 * Purpose: Translate lifecycle claim text into an existing safe badge class.
 * Inputs: Claim-state string from a schema-shaped API record.
 * Outputs: One reviewed CSS class token.
 * How it works: Maps preview and proven states explicitly and falls back to unknown.
 * Side effects: None.
 * Failure behavior: Unrecognized text never becomes a success class.
 * Safety: The returned token cannot execute code or authorize an action.
 * Example: ``claimClass('preview-only')`` returns ``preview``.
 * Related proof: Lifecycle badge assertions and shared stylesheet states.
 */
function claimClass(value) {
  if (value === "preview-only") return "preview";
  if (value === "proven") return "proven";
  if (value === "failed") return "failed";
  if (value === "blocked") return "blocked";
  return "unknown";
}

/**
 * Purpose: Format bounded byte totals without exposing files, names, or paths.
 * Inputs: Nonnegative byte count from aggregate lifecycle inventory.
 * Outputs: Compact bytes, KB, MB, or GB label.
 * How it works: Chooses one fixed unit and rounds to at most one decimal place.
 * Side effects: None.
 * Failure behavior: Invalid values display zero bytes conservatively.
 * Safety: Formatting cannot reconstruct source content or identity.
 * Example: ``formatBytes(1536)`` returns ``1.5 KB``.
 * Related proof: Lifecycle renderer text assertions.
 */
function formatBytes(value) {
  const bytes = Number.isFinite(Number(value)) && Number(value) >= 0 ? Number(value) : 0;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

/**
 * Purpose: Render the complete preview-only lifecycle surface from current API truth.
 * Inputs: Policy and catalog mappings fetched from exact read-only endpoints.
 * Outputs: Updated badge, totals, logical target, boundary, and five plan cards.
 * How it works: Validates schema ids, uses safe text nodes, and maps each closed plan.
 * Side effects: Replaces children within lifecycle-owned DOM containers only.
 * Failure behavior: Invalid/missing snapshots show unavailable state and no controls.
 * Safety: No event listener, POST, path, filename, command, or executable action is created.
 * Example: Backup card shows observed source bytes while archive creation remains blocked.
 * Related proof: Lifecycle frontend tests and browser viewport checks.
 */
export function renderLifecycleDryRuns(policy, catalog) {
  const state = document.querySelector("#lifecycle-dry-run-state");
  const summary = document.querySelector("#lifecycle-dry-run-summary");
  const inventory = document.querySelector("#lifecycle-inventory-summary");
  const target = document.querySelector("#lifecycle-backup-target");
  const boundary = document.querySelector("#lifecycle-dry-run-boundary");
  const list = document.querySelector("#lifecycle-dry-run-list");
  if (!state || !summary || !inventory || !target || !boundary || !list) return;

  const validPolicy = policy?.schemaVersion === "makers-anvil.config.lifecycle-dry-run.v1";
  const validCatalog = catalog?.schemaVersion === "makers-anvil.api.lifecycle-dry-run-catalog.v1";
  const claim = validCatalog ? catalog.claimState : "unknown";
  state.textContent = claim;
  state.className = `badge ${claimClass(claim)}`;
  const facts = validCatalog ? catalog.summary || {} : {};
  summary.textContent = `${facts.previewReadyCount || 0}/${facts.operationCount || 0} previews · ${facts.executionReadyCount || 0} executable`;
  inventory.textContent = `${facts.sourceFileCount || 0} app files · ${formatBytes(facts.sourceBytes || 0)} · content unread`;
  target.textContent = validPolicy ? policy.backupTarget : "not proven";
  boundary.textContent = "Planning only · no archive read/write, restore, network, package, installer, software mutation, process, or user-data deletion";
  list.replaceChildren();

  const plans = validCatalog ? catalog.plans || [] : [];
  plans.forEach((plan) => {
    const card = document.createElement("article");
    card.className = "lifecycle-plan-card";
    const heading = document.createElement("div");
    heading.className = "lifecycle-plan-head";
    const title = document.createElement("h4");
    title.textContent = plan.operation.label;
    const badge = document.createElement("span");
    badge.className = `badge ${claimClass(plan.claimState)}`;
    badge.textContent = plan.claimState;
    heading.append(title, badge);
    const planSummary = document.createElement("p");
    planSummary.textContent = plan.operation.summary;
    const evidence = document.createElement("p");
    evidence.className = "lifecycle-plan-fact";
    evidence.textContent = `${plan.steps.length} planned steps · ${plan.requiredEvidence.length} proof requirements`;
    const preservation = document.createElement("p");
    preservation.className = "lifecycle-plan-preservation";
    preservation.textContent = plan.preservation.existingDataPreserved && !plan.preservation.userDataDeletionAllowed
      ? "Existing app data preserved · deletion not allowed"
      : "Preservation not proven";
    const blockers = document.createElement("p");
    blockers.className = "lifecycle-plan-blockers";
    blockers.textContent = `Blocked by: ${plan.readiness.blockers.join(", ")}`;
    card.append(heading, planSummary, evidence, preservation, blockers);
    list.append(card);
  });

  if (!plans.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Lifecycle dry-run plans are unavailable.";
    list.append(empty);
  }
}
