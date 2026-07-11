/**
 * Purpose: Configure React compilation, deterministic production output, local API proxying, and jsdom tests.
 * Used by: npm frontend development, build, test, CI, local server, and Windows packaging commands.
 * Inputs: First-party src/public files and dependency versions locked by package-lock.json.
 * Outputs: The frontend/dist production bundle or an isolated Vitest environment.
 * Side effects: Build commands replace generated dist files; the dev command may bind loopback port 5174.
 * Safety: API proxying targets loopback only and generated/tests folders are excluded from test discovery.
 * Failure behavior: Type, dependency, transform, or test configuration errors stop the command nonzero.
 * Related proof: npm build, npm test, runtime-resource tests, and Windows package smoke checks.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    manifest: true,
    outDir: "dist",
  },
  server: {
    port: 5174,
    proxy: {
      "/api": "http://127.0.0.1:8765",
    },
  },
  test: {
    environment: "jsdom",
    exclude: ["node_modules/**", "dist/**", "e2e/**", "test-results/**"],
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
  },
});
