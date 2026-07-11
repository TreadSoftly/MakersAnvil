/**
 * Purpose: Convert explicit status vocabulary into a compact, consistently colored visual label.
 * Used by: App.tsx across route, tool, capability, execution, and proof summaries.
 * Inputs: One server- or adapter-authored status string.
 * Outputs: A text-preserving span with neutral, ready, warning, or blocked presentation.
 * Side effects: None; the component renders presentation only.
 * Safety: The original status remains visible and color is never the only information carrier.
 * Failure behavior: Unknown status words safely receive the neutral tone.
 * Related proof: App.test.tsx status and forbidden-claim assertions.
 */

interface StatusPillProps {
  status: string;
}

/** Display the original status string with a conservative semantic color tone. */
export function StatusPill({ status }: StatusPillProps) {
  const normalized = status.toLowerCase();
  let tone = "neutral";
  if (normalized.includes("ready") || normalized.includes("detected") || normalized.includes("enabled")) {
    tone = "ready";
  }
  if (normalized.includes("blocked") || normalized.includes("missing")) {
    tone = "blocked";
  }
  if (normalized.includes("manual") || normalized.includes("candidate")) {
    tone = "warn";
  }
  return <span className={`status-pill ${tone}`}>{status}</span>;
}
