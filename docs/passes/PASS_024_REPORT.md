# PASS-024 Report - Verified Image Previews

## Goal

Restore the previous working application's selected-image preview experience without exposing source paths or serving unverified user content.

## Implemented

- Added a strict schema-backed preview policy for authorized app-owned raster copies with a 25 MiB response ceiling.
- Added a focused preview service that reloads the authorized record, resolves only generated contained storage, bounds the read, and rechecks exact length plus SHA-256 on every request.
- Added conservative PNG, JPEG, GIF, WebP, BMP, and TIFF signature checks; SVG, HTML, scripts, archives, non-images, and suffix-only trust remain excluded.
- Added read-only `GET /api/intake/previews/policy` and dynamic `GET /api/intake/previews/{intakeId}` routes.
- Added binary API transport with generated response names, ETags, `no-store`, `nosniff`, and same-origin resource policy.
- Updated the portable React adapter to create preview URLs only for authorized image records carrying integrity proof.
- Updated the promoted media board to render accessible image previews and fall back to its generated file icon if decoding fails.
- Added isolated service, API, real loopback HTTP, frontend-adapter, and React behavior tests.

## Safety Boundaries

- No source path or original source filename is used by the preview endpoint.
- No browser-provided path reaches the filesystem.
- Metadata-only records have no preview URL.
- Preview reads cannot mutate records or content, execute routes, launch tools, open external programs, extract archives, or hand a selected file to another process.
- Content-type and malware-clean claims remain unproven; the feature claims only bounded raster signature and integrity verification for local visual display.

## Completion

- Full real application: `82.5000%`
- Windows local application: `86.0000%`
- Packaged release: `30.0000%`
- Clean-machine proof: `5.0000%`
- macOS/Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`

## Verification

- Focused preview service/API/HTTP tests: passed, 4 tests.
- Frontend Vitest: passed, 22 tests across 2 files.
- TypeScript and Vite production build: passed.
- Live app-owned PNG: passed as `image/png`, 222,982 bytes, generated `preview.png`, `no-store`, and `nosniff`, with no path-bearing response metadata.
- Full Python suite: passed, 167 tests.
- Every-line learning guide: passed for 166 selected sources and 36,752 explained lines at closeout.
- Explainability verifier: passed for all 220 tracked/pending product files at closeout.
- Project verifier: all API, required-file, JSON, status, portability, reference, forbidden-text, and explanation groups passed.
- Native desktop smoke: passed with PASS-024, `82.5%`, current preview-capable API build, guarded mutation scopes, and full route execution false.
- Fresh Windows one-file build: succeeded; packaged `MakersAnvil.exe --smoke` passed with bundled PASS-024 source, policy, schema, and React resources.
- GitHub Actions run `28543861272`: Windows verification, Ubuntu verification, macOS verification, and Windows executable build all passed.
- Browser screenshot proof: not claimed because the in-app browser was unavailable.

## Next Pass

PASS-025 adds an in-app contained proof/report viewer and proof-gated output interaction without enabling arbitrary operating-system file opening.
