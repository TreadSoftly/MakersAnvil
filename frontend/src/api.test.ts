/**
 * Purpose: Prove current portable API records become safe promoted-workbench view models.
 * Used by: Vitest and CI beside the larger React interaction suite.
 * Inputs: Minimal path-redacted current API fixtures and mocked same-origin fetch responses.
 * Outputs: Assertions for previews, execution history, early run identity, cancellation, proof viewing, and private-path absence.
 * Side effects: Replaces fetch only inside the isolated jsdom test process.
 * Safety: No real file, server, source path, token, route, tool, or process is used.
 * Failure behavior: Adapter shape drift or preview widening fails before a frontend build can ship.
 * Related proof: Python intake-preview service/API/HTTP tests and App.test.tsx media rendering.
 */

import { afterEach, describe, expect, test, vi } from "vitest";
import { cancelExecution, getState, openOutput, runRoute } from "./api";

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

  test("maps version-bound launch review without enabling tool launch", async () => {
    const current: Record<string, any> = currentStateFixture(true);
    current.toolDetection = {
      tools: [{
        id: "blender", label: "Blender", families: ["cad-modeler"], claimState: "detected",
        detection: { installed: true },
        version: { claimState: "proven", value: "4.5.0.0", evidenceMethod: "windows-version-resource" },
      }],
    };
    current.toolLaunchCatalog = {
      tools: [{
        id: "blender", reviewReady: true,
        confirmation: { required: true, accepted: false },
        blockedReasons: ["Version metadata does not prove publisher signature or executable trust.", "Explicit launch confirmation has not been accepted or persisted.", "External tool process launch is not enabled in the API."],
      }],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(current), { status: 200, headers: { "Content-Type": "application/json" } })),
    );

    const state = await getState();
    const blender = state.tools[0];

    expect(blender).toMatchObject({
      toolId: "blender", tool: "Blender", launchable: false, launchReviewReady: true,
      versionValue: "4.5.0.0", versionClaimState: "proven", versionEvidenceMethod: "windows-version-resource",
      confirmationRequired: true, confirmationAccepted: false,
    });
    expect(blender.blockedClaims).toContain("External tool process launch is not enabled");
    expect(JSON.stringify(blender)).not.toContain("C:" + "\\Users\\");
  });

  test("maps proof-bearing execution outputs and fetches a closed report endpoint", async () => {
    const current: Record<string, any> = currentStateFixture(true);
    const executionId = "execution-0123456789abcdef0123456789abcdef";
    current.containedExecutions = {
      summary: { proofCount: 1 },
      actions: { cancel: { enabledInApi: true } },
      executions: [{ record: { id: executionId, claimState: "proven", createdUtc: "2026-07-01T20:00:00Z", updatedUtc: "2026-07-01T20:00:02Z", source: { displayName: "fixture.stl" }, operation: { label: "Built-in STL preflight" }, route: { id: "mesh-to-toolpath" }, lifecycle: { state: "completed", completedUtc: "2026-07-01T20:00:02Z" }, workspace: { logicalRoot: `makers-anvil-data://user/executions/${executionId}` }, proof: { outcome: "passed", report: { logicalPath: `makers-anvil-data://user/executions/${executionId}/outputs/stl-preflight-report.json` } } }, cancellation: { state: "not-requested" }, audit: { summary: { eventCount: 5 } } }],
    };
    const artifact = { schemaVersion: "makers-anvil.api.contained-artifact.v1", artifactKind: "report", title: "STL preflight report" };
    const fetchMock = vi.fn(async (url: string) => {
      if (url === "/api/state") return new Response(JSON.stringify(current), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/executions/catalog") return new Response(JSON.stringify({ executions: current.containedExecutions.executions, actions: { viewArtifact: { enabledInApi: true, allowedKinds: ["report", "proof"] } } }), { status: 200, headers: { "Content-Type": "application/json" } });
      return new Response(JSON.stringify(artifact), { status: 200, headers: { "Content-Type": "application/json" } });
    });
    vi.stubGlobal("fetch", fetchMock);

    const state = await getState();
    const result = await openOutput("Report");

    expect(state.latestJob.availableOutputs.map((output) => output.key)).toEqual(["report", "proof"]);
    expect(state.latestJob.selectedRoute).toBe("mesh-review");
    expect(state.executionHistory[0]).toMatchObject({ id: executionId, sourceName: "fixture.stl", lifecycleState: "completed", hasProof: true, canCancel: false, auditEventCount: 5 });
    expect(result.title).toBe("STL preflight report");
    expect(fetchMock).toHaveBeenCalledWith(`/api/executions/${executionId}/artifacts/report`, { cache: "no-store", credentials: "omit" });
  });

  test("sends a guarded bodyless cooperative cancellation request only for a running catalog record", async () => {
    const executionId = "execution-fedcba9876543210fedcba9876543210";
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (url === "/api/intake/session") return new Response(JSON.stringify({ requestToken: "cancel-token" }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/executions/catalog") return new Response(JSON.stringify({ actions: { cancel: { enabledInApi: true } }, executions: [{ record: { id: executionId, lifecycle: { state: "running" } } }] }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/cancel")) return new Response(JSON.stringify({ record: { lifecycle: { state: "running" } }, cancellation: { state: "requested", processSignalSent: false } }), { status: 200, headers: { "Content-Type": "application/json" } });
      return new Response(JSON.stringify({ message: "Unexpected route" }), { status: 404, headers: { "Content-Type": "application/json" } });
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await cancelExecution(executionId);

    expect(result).toEqual({ lifecycleState: "running", cancellationState: "requested", processSignalSent: false });
    expect(fetchMock).toHaveBeenCalledWith(`/api/executions/${executionId}/cancel`, {
      method: "POST", headers: { "X-Makers-Anvil-Request-Token": "cancel-token" }, cache: "no-store", credentials: "omit",
    });
  });

  test("exposes the generated execution id before the run request completes", async () => {
    const executionId = "execution-00112233445566778899aabbccddeeff";
    const intakeId = "intake-00112233445566778899aabbccddeeff";
    const authorized = vi.fn();
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url === "/api/state") return new Response(JSON.stringify({ intakeCatalog: { records: [{ id: intakeId, source: { displayName: "fixture.stl", kind: "mesh", extension: ".stl" } }] } }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/intake/session") return new Response(JSON.stringify({ requestToken: "run-token" }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/executions/policy") return new Response(JSON.stringify({ scope: { routeId: "mesh-to-toolpath", operationId: "built-in-stl-preflight" }, endpoints: { authorize: "/api/executions/authorizations", runTemplate: "/api/executions/{executionId}/run" } }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url === "/api/executions/authorizations") return new Response(JSON.stringify({ record: { id: executionId, source: { displayName: "fixture.stl" } } }), { status: 201, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/run")) return new Response(JSON.stringify({ record: { lifecycle: { state: "cancelled" } } }), { status: 200, headers: { "Content-Type": "application/json" } });
      return new Response(JSON.stringify({ message: "Unexpected route" }), { status: 404, headers: { "Content-Type": "application/json" } });
    }));

    const result = await runRoute("mesh-review", authorized);

    expect(authorized).toHaveBeenCalledWith({ id: executionId, sourceName: "fixture.stl" });
    expect(result).toMatchObject({ executionId, lifecycleState: "cancelled", exitCode: 2, ok: false });
  });
});
