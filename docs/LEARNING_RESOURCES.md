# Makers Anvil Learning Resources

## How To Use This Map

Start with local code, schemas, tests, and the implementation guide because they define this application's actual behavior. External documentation explains the underlying technologies but does not override local safety policy or prove that a Makers Anvil feature works.

For each topic, read the local files first, run the named tests, then use the external reference when a language or platform concept needs more background.

For any source file, open its section in `docs/LINE_BY_LINE_CODE_GUIDE.md` to study the exact source text and plain-language explanation at matching line numbers. The file hash and counts in `state/learning_coverage.json` prove that the guide matches the current source. Run `python scripts/build_learning_guide.py --check` before trusting an older local copy.

## Python Structure And Documentation

Local study path:

1. `backend/src/makers_anvil_backend/api/app.py` for small typed records and route dispatch.
2. `backend/src/makers_anvil_backend/services/` for dependency injection and focused services.
3. `tests/test_api.py` and the service tests for executable usage examples.
4. `scripts/check_explainability.py` for AST-based docstring enforcement.
5. `scripts/build_learning_guide.py` for the rules that produce per-line context-aware explanations.

References:

- Python documentation strings: <https://docs.python.org/3/tutorial/controlflow.html#documentation-strings>
- Python type hints: <https://docs.python.org/3/library/typing.html>
- Python data classes: <https://docs.python.org/3/library/dataclasses.html>

## Files, Paths, And Containment

Local study path:

1. `services/runtime_paths.py` for private OS-specific root resolution.
2. `services/workspace_config.py` for relative app-owned directory validation.
3. `tests/test_portability.py` and `tests/test_workspace_config.py` for relocation and traversal examples.

References:

- Python `pathlib`: <https://docs.python.org/3/library/pathlib.html>
- OWASP path traversal: <https://owasp.org/www-community/attacks/Path_Traversal>

## HTTP And API Boundaries

Local study path:

1. `server.py` for loopback HTTP and static serving.
2. `api/app.py` for read routing, guarded intake/preferences POST patterns, media checks, and error responses.
3. `tests/test_api.py` and `tests/test_server.py` for expected behavior.
4. `services/authorized_intake.py` and `tests/test_authorized_intake.py` for consent, same-origin checks, exact streaming, hashing, rollback, and replay prevention.
5. `services/local_request_guard.py` for the shared process token, Origin/Host match, loopback, and Fetch Metadata boundary.

References:

- Python `http.server`: <https://docs.python.org/3/library/http.server.html>
- HTTP semantics: <https://www.rfc-editor.org/rfc/rfc9110>
- MDN Fetch API: <https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API>
- MDN using Fetch: <https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch>
- MDN Fetch Metadata: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Fetch_metadata>
- MDN CORS guide: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS>
- OWASP File Upload Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html>
- Python temporary files: <https://docs.python.org/3/library/tempfile.html>
- Python atomic replacement with `os.replace`: <https://docs.python.org/3/library/os.html#os.replace>

## JSON And JSON Schema

Local study path:

1. Match a file under `config/` to its policy schema under `schemas/`.
2. Match a service response to its API schema.
3. Read `scripts/verify_project.py` to see how cross-file invariants are enforced.

References:

- JSON Schema getting started: <https://json-schema.org/learn/getting-started-step-by-step>
- JSON Schema 2020-12 specification: <https://json-schema.org/specification>

## Browser Rendering And Safety

Local study path:

1. `frontend/src/App.tsx` for the promoted semantic regions and interaction flow.
2. `frontend/src/api.ts` for portable state adaptation and guarded mutations.
3. `frontend/src/styles.css` for the accepted visual system, motion, and responsive layout.
4. `frontend/src/App.test.tsx` for twenty executable workflow and safety examples.
4. Browser smoke tests and screenshots recorded in the current pass report.
5. `context-help.js`, `capability-lanes.js`, `workbench-experience.js`, `contained-execution.js`, and `lifecycle-dry-runs.js` for focused interaction modules.

References:

- Fetch API: <https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API>
- DOM `textContent`: <https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent>
- Web accessibility introduction: <https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/What_is_accessibility>
- WAI-ARIA dialog keyboard and focus guidance: <https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/>
- MDN reduced-motion media feature: <https://developer.mozilla.org/docs/Web/CSS/@media/prefers-reduced-motion>

## Lifecycle Planning And Preservation

Local study path:

1. `config/lifecycle_dry_run_policy.json` for the exact five operations, evidence, blockers, and false effects.
2. `services/lifecycle_dry_run.py` for strict policy validation, non-following bounded metadata inventory, and deterministic plan composition.
3. `schemas/lifecycle-dry-run-*.schema.json` for machine-readable preservation and zero-execution contracts.
4. `lifecycle-dry-runs.js` for text-only command-free rendering.
5. `tests/test_lifecycle_dry_run.py` for empty, populated, no-write, fail-closed, and scan-limit examples.

Use the existing Python filesystem, JSON Schema, browser rendering, testing, and desktop packaging references in this document to follow each layer. PASS-022 selects MSIX as the Windows installer target but deliberately performs no package or machine mutation.

## Windows Installer And Clean-Machine Gates

Local study path:

1. `config/windows_installer_policy.json` for package identity, runtime, preservation, signing, action, and safety truth.
2. `config/clean_machine_scenarios.json` for the exact six required machine workflows.
3. `services/windows_installer.py` for strict validation and nine readiness gates.
4. `scripts/check_clean_machine.py` for the inspection-only harness command.
5. `windows-installer.js` for text-only release evidence rendering.
6. `tests/test_windows_installer.py` for valid, weakened, incomplete, and CLI examples.

References:

- Microsoft MSIX overview: <https://learn.microsoft.com/en-us/windows/msix/overview>
- Microsoft Windows packaging decision overview: <https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/packaging/>
- Microsoft MSIX signing overview: <https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview>
- Microsoft MSIX troubleshooting guide: <https://learn.microsoft.com/en-us/windows/msix/msix-troubleshooting-guide>

## Testing And Verification

Local study path:

1. Read the test whose name matches the capability.
2. Run one focused test with `python -m pytest tests/test_name.py -q`.
3. Run `python scripts/check_explainability.py`.
4. Run `python scripts/build_learning_guide.py --check`.
5. Run `python scripts/verify_project.py`.
6. Run `python -m pytest -q`.

References:

- pytest documentation: <https://docs.pytest.org/en/stable/>
- Python `unittest.mock`: <https://docs.python.org/3/library/unittest.mock.html>

## Git And Continuous Integration

Local study path:

1. `.github/workflows/ci.yml` for the operating-system matrix and proof commands.
2. `docs/CONTINUE_PROTOCOL.md` for commit, push, CI, and report requirements.
3. `docs/PASS_REPORT_TEMPLATE.md` for evidence recording.

References:

- Pro Git: <https://git-scm.com/book/en/v2>
- GitHub Actions: <https://docs.github.com/en/actions>

## Desktop Windows And Packaging

Local study path:

1. `runtime_resources.py` for source-versus-frozen resource discovery.
2. `server.py` for loopback-only binding and owned server construction.
3. `desktop.py` for native-window lifecycle and headless package smoke.
4. `scripts/build_windows_exe.py` for deterministic one-file packaging.
5. `docs/DESKTOP_ARCHITECTURE.md` for selected/deferred architecture and release boundaries.

References:

- pywebview API: <https://pywebview.idepy.com/en/guide/api>
- pywebview freezing: <https://pywebview.idepy.com/en/guide/freezing>
- PyInstaller usage: <https://pyinstaller.org/en/stable/usage.html>
- PyInstaller spec/data files: <https://pyinstaller.org/en/latest/spec-files.html>
- Microsoft WebView2 distribution: <https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution>
- Tauri external sidecars: <https://v2.tauri.app/develop/sidecar/>

## Recommended Learning Loop

1. Pick one visible dashboard panel.
2. Find its HTML region and JavaScript renderer.
3. Find its API path.
4. Find the `AppStateService` method and focused service.
5. Find its config, schemas, and tests.
6. Change nothing; predict one test result and run it.
7. Trace one safety boolean from config through service, API, UI, and verifier.
8. Use `state/source_manifest.json` when a file's role is unclear.

External videos may help with general Python, HTTP, JavaScript, Git, or JSON Schema concepts, but links can age and teaching quality varies. Prefer the official references above and the repository's executable tests for current project truth.
