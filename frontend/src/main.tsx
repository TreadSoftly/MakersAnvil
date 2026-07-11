/**
 * Purpose: Mount the Makers Anvil React application into the one trusted document root.
 * Used by: Vite development, production builds, the local server, and the native desktop window.
 * Inputs: The root element from index.html plus App and the shared stylesheet.
 * Outputs: One React StrictMode tree containing the complete Makers Anvil workbench.
 * Side effects: Creates the browser UI inside the existing root element.
 * Safety: No API mutation, path access, process launch, or file authorization occurs here.
 * Failure behavior: A missing root fails immediately instead of rendering into an unintended node.
 * Related proof: npm build, App.test.tsx, runtime-resource tests, and desktop smoke mode.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
