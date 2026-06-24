# Code Explainability Standard

## Goal

Any careful developer, reviewer, or AI model should be able to determine what a file owns, why it exists, how data moves through it, which invariants matter, and what remains unsafe or unproven without relying on private chat history.

## Required Explanation Layers

### Every File

- Python files require a structured module docstring naming purpose, who uses it, inputs, outputs, side effects, safety, failure behavior, and related proof.
- JavaScript, CSS, SVG, HTML, YAML, and workflow files require the same structured context in a leading comment supported by section comments for major logical regions.
- JSON, TOML, license, ignore, and Markdown files must have a complete entry in `state/source_manifest.json` because those formats either do not safely support comments or are better governed by the central ownership map.

### Every Python Component

Every class, constructor, function, method, private helper, and test function requires a docstring. A useful docstring states the observable responsibility and, when relevant, inputs, output, side effects, containment, and failure behavior. Private names are not exempt because future maintainers still need to understand them.

### Every Frontend Function

Every top-level JavaScript function requires nearby JSDoc that explains its purpose and relevant input, output, rendering, trust, or failure behavior. File-level comments alone are not enough.

### Every Non-Obvious Block

Add a nearby comment when code enforces a safety boundary, validates containment, intentionally avoids an action, translates between contracts, retries asynchronous behavior, or uses a choice that a maintainer might otherwise "simplify" incorrectly.

### Every Structured Contract

Schemas, config files, and state files require a source-manifest explanation. New fields must be named clearly and constrained by schema or verifier checks. Safety booleans must not be loose truth strings.

### Every Behavior

Tests must read as executable examples. Test names and docstrings explain the rule being proved. Assertions should expose the contract, not internal implementation trivia.

## What Not To Do

Every line must be explainable to a new learner. Obvious syntax may be explained once by the surrounding component or block instead of receiving a duplicate sentence, while decisions, trust transitions, state changes, containment checks, and failure branches require nearby reasoning.

Do not leave historical chat instructions, personal paths, secrets, speculative claims, or obsolete implementation plans inside source comments.

The requirement is met through structured file headers, descriptive names, types, schemas, component documentation, block-level reasoning comments, executable examples, the source walkthrough, and the implementation guide. A maintainer must be able to answer what, why, who calls it, where data comes from/goes, when effects occur, how failures behave, and which proof protects it.

## Durable Learning Paths

- `docs/IMPLEMENTATION_GUIDE.md` traces folders, layers, request flow, contracts, safety, extension recipes, and debugging.
- `docs/SOURCE_WALKTHROUGH.md` gives the file-by-file reading order and connects source blocks to contracts and tests.
- `docs/PREVIOUS_APP_REFERENCE_STUDY.md` preserves accepted prototype design knowledge without a runtime dependency.
- `docs/LEARNING_RESOURCES.md` maps local examples to stable external references.
- `docs/PASS_REPORT_TEMPLATE.md` defines the proof every completed pass must leave for the next contributor.
- `state/source_manifest.json` maps every individual tracked file to its purpose and maintenance rules.

## Change Checklist

For every changed file:

1. Confirm its source-manifest entry still matches its responsibility.
2. Update file-level purpose text if ownership changed.
3. Update all affected component docstrings and frontend JSDoc when behavior or failure modes changed.
4. Add or revise reasoning comments around new non-obvious blocks.
5. Update tests as readable examples.
6. Update architecture when dependencies or data flow changed.
7. Run `python scripts/check_explainability.py`.

The project verifier treats explainability failures as build failures.
