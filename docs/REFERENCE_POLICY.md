# Reference Policy

The ignored reference roots contain planning evidence and an earlier working Makers Anvil prototype. They are design inputs, not product source:

- `Refrences For Makers Anvil Application/`
- `References For Makers Anvil Application/`
- `Previous Working MA For References/`

The previous working app is specifically a visual, workflow, wording, and interaction reference. Its accepted lessons are normalized into the tracked [previous-app reference study](PREVIOUS_APP_REFERENCE_STUDY.md), which is the durable source future passes read. The large ignored folder does not need to exist for development, tests, runtime, packaging, or a fresh clone.

Product rules:

- Runtime code must not import from the reference folder.
- Tests must not require the reference folder.
- Packaged app artifacts must not include the reference folder.
- Product files must not carry personal absolute paths or legacy project-specific content.
- Concepts from the reference folder may be reimplemented when they fit the clean product architecture.
- Reference code is never copied blindly; behavior must be rebuilt against current schemas, safety gates, tests, portability rules, and visual checks.
- Personal paths, cached environments, generated output, old tool-launch behavior, and old completion claims are evidence to reject, not patterns to preserve.
- A visual pass may inspect selected old screenshots or source files, but it must record the resulting decision in tracked documentation before relying on it.

All reference folders can be deleted at any time without breaking Makers Anvil.
