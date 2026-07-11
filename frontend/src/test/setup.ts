/**
 * Purpose: Install DOM-aware Vitest matchers for React workbench tests.
 * Used by: vite.config.ts before each frontend test module executes.
 * Inputs: The Vitest runtime and jsdom environment.
 * Outputs: Extended expect matchers such as toBeInTheDocument and toBeDisabled.
 * Side effects: Extends only the isolated test assertion environment.
 * Safety: Production bundles do not import this file.
 * Failure behavior: Missing matcher dependencies fail test startup immediately.
 * Related proof: App.test.tsx.
 */

import "@testing-library/jest-dom/vitest";
