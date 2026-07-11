# Previous App Reference Study

## Why This Exists

`Previous Working MA For References/` is the earlier experimental Makers Anvil dashboard. It reached a useful visual and workflow direction before the clean rebuild began. The folder is large, ignored, personal-workspace evidence. This tracked study preserves its useful lessons so the real app can use them without importing old code or depending on that folder.

## Evidence Reviewed

- The prior `USER_WORKFLOW_MODEL.md` and workbench implementation plans.
- Workbench passes 012-054, especially fullscreen structure, preview unification, action clarity, plan depth, capability health, tool setup, proof flow, stable tab geometry, and visible outputs.
- Prior `App.tsx` component composition and `styles.css` layout/tokens.
- Desktop screenshots at 1600x980 and 1366x768, plus recorded checks at 2560, 2048, 1920, 1280, 1120, 760, 460, and 390 pixel widths.

The review extracts intent. Old readiness percentages and old implementation claims are historical only.

## Product Direction To Keep

### First View

The first screen is the real workbench, not a marketing page. It must make these things immediately visible:

1. Makers Anvil identity and live system health.
2. Source-file intake.
3. Selected input and a useful preview.
4. Relevant installed/known maker tools.
5. Work plans and current workflow state.
6. Latest output and its proof boundary.
7. Clear blocked/not-proven status when work cannot run.

### Desktop Structure

- A narrow left navigation rail for Workbench, Intake, Plans, Tools, Files, Components, Simulation, Outputs, and Settings.
- A compact top bar for product identity, search/command discovery, refresh, notifications, and settings.
- A dense central workbench using stable grid zones rather than a long stack of generic cards.
- A right-side preview/proof inspector that keeps selected input, expected output, tool handoff, and latest proof together.
- Mode tabs for normal workflow, plans, and developer/raw evidence without changing the command deck's outer geometry.
- Local scrolling inside detail regions when necessary; no incoherent whole-page overflow at supported desktop sizes.

### Workflow Language

Prefer direct maker language:

- `Add source files`
- `Selected input`
- `Tools`
- `Work plans`
- `Work flow`
- `Work preview`
- `Latest output proof`
- `Open job folder`
- `Preview plan`

Avoid vague dashboard terms and avoid using `route` as the main beginner-facing word. Internal route IDs may remain stable in schemas and code.

### Visual Direction

- Industrial workbench rather than corporate analytics or science-fiction control room.
- Matte charcoal/near-black structure balanced with readable neutral surfaces.
- Green for healthy/ready state, cyan for information/navigation, restrained gold for identity/attention, and red only for actual errors or blocked danger.
- Real tool icons and real source/output thumbnails when evidence exists; never invented logos or fake previews.
- Compact type and controls sized for repeated work, with card radii no greater than 8px in the real rebuild.
- Motion may communicate health, selection, or progress, but reduced-motion settings must remain respected.

### Interaction Principles

- Preview source material before logs and deep proof data.
- Keep selected-file, selected-tool, selected-plan, expected-output, and latest-proof context synchronized.
- Goal/workflow mode should be easiest for normal users; tool mode and granular/developer evidence remain available without crowding the default view.
- Use explicit status language: planned, ready, blocked, not proven, completed with proof. Never use broad claims such as CAD complete, manufacturing ready, or build ready without their evidence gates.
- Tool launch setup may be previewed before it is authorized. Direct file handoff must remain blocked until a tool-specific adapter is tested.

## Legacy Patterns To Reject

- Personal absolute paths, usernames, cloud-folder assumptions, or source-location runtime data.
- Importing old environments, caches, binaries, generated jobs, or screenshots into the product.
- Copying the old monolithic React/CSS implementation into the clean rebuild.
- Direct selected-file launch, arbitrary command construction, archive extraction, recursive folder import, package management, or tool execution without current safety contracts.
- Old completion/readiness claims, fake tool/output truth, or generated imagery represented as real evidence.
- Duplicate tool surfaces, duplicated selected-file context, unstable tab geometry, clipped text, long empty strips, or page-level overflow.
- Decorative effects that dominate the product, including red-heavy treatments, excessive gradients, or motion without meaning.

## How Future Continue Passes Use This Study

1. Read this tracked study during the required startup sequence.
2. Select only the patterns relevant to the active bounded pass.
3. Inspect a specific ignored screenshot/source file only if this summary lacks necessary detail.
4. Rebuild the behavior inside current architecture, schemas, tests, and safety gates.
5. Capture current-app browser evidence at desktop and mobile sizes.
6. Update this study when a prototype lesson is accepted, rejected, or superseded.

The ignored prototype can disappear and this contract remains sufficient to continue the real application.

## Applied In PASS-015

PASS-015 implemented the first governed translation of this study: a compact rail and command bar, paired source intake/selected-input zones, horizontal tool inventory, stable Work Flow/Plans/Dev command deck, right-side work-preview/output-proof inspector, local desktop scrolling, and stacked narrow-screen flow. It intentionally did not copy the old React component tree, old CSS effects, tool icons, personal paths, or action behavior.
