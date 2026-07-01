/**
 * Purpose: Prove current portable API records become safe promoted-workbench view models.
 * Used by: Vitest and CI beside the larger React interaction suite.
 * Inputs: Minimal path-redacted current API fixtures and mocked same-origin fetch responses.
 * Outputs: Assertions for authorized preview URLs, metadata-only fallbacks, and private-path absence.
 * Side effects: Replaces fetch only inside the isolated jsdom test process.
 * Safety: No real file, server, source path, token, route, tool, or process is used.
 * Failure behavior: Adapter shape drift or preview widening fails before a frontend build can ship.
 * Related proof: Python intake-preview service/API/HTTP tests and App.test.tsx media rendering.
 */

import { afterEach, describe, expect, test, vi } from "vitest";
import { getState } from "./api";

function currentStateFixture(withAuthorizedStorage = true) {
  return {
    schemaVersion: "makers-anvil.api.state.v1",
    intakeCatalog: {
      claimState: "staged",
      recordsPath: "makers-anvil-data://user/intake/records",
      summary: { recordCount: 1, byKind: { image: 1 } },
      records: [
        {
          schemaVersion: withAuthorizedStorage
            ? "makers-anvil.runtime.authorized-intake-record.v1"
            : "makers-anvil.runtime.intake-record.v1",
          id: "intake-0123456789abcdef0123456789abcdef",
          source: { displayName: "reference.png", extension: ".png", kind: "image", sizeBytes: 24 },
          ...(withAuthorizedStorage
            ? {
                storage: {
                  logicalReference: "makers-anvil-data://user/intake/files/intake-0123456789abcdef0123456789abcdef",
                  sha256: "a".repeat(64),
                  integrityVerified: true,
                },
              }
            : {}),
        },
      ],
    },
    routePreview: {
      summary: { previewCount: 1 },
      previews: [
        {
          source: { intakeId: "intake-0123456789abcdef0123456789abcdef" },
          route: { id: "image-reference-review", label: "Image reference review" },
          readiness: { executionReady: false, blockers: ["Review only"] },
        },
      ],
    },
    toolDetection: { tools: [] },
    containedExecutions: { summary: { proofCount: 0 } },
    capabilityMatrix: { lanes: [], ingressMethods: [], honesty: [] },
    blockedActions: ["external tool launch"],
  };
}

describe("portable API adapter", () => {
  afterEach(() => vi.unstubAllGlobals());

  test("adds a generated same-origin preview URL only to authorized image copies", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify(currentStateFixture(true)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const state = await getState();

    expect(state.intake.files[0].previewUrl).toBe(
      "/api/intake/previews/intake-0123456789abcdef0123456789abcdef",
    );
    expect(state.intake.files[0].pathDisplay).toMatch(/^makers-anvil-data:\/\//);
    const serialized = JSON.stringify(state);
    expect(serialized).not.toContain("C:" + "\\Users\\");
    expect(serialized).not.toContain("/" + "Users/");
    expect(serialized).not.toContain("/" + "home/");
    expect(fetchMock).toHaveBeenCalledWith("/api/state", { cache: "no-store", credentials: "omit" });
  });

  test("keeps metadata-only image records on the non-content fallback", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify(currentStateFixture(false)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const state = await getState();

    expect(state.intake.files[0].previewUrl).toBeUndefined();
    expect(state.intake.files[0].pathDisplay).toBe("makers-anvil-data://user/intake");
  });
});
