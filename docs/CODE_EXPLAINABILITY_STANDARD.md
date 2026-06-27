# Code Explainability Standard

## Goal

Any careful developer, reviewer, or AI model should be able to determine what a file owns, why it exists, how data moves through it, which invariants matter, and what remains unsafe or unproven without relying on private chat history.

## Required Explanation Layers

### Every File

- Python files require a structured module docstring naming purpose, who uses it, inputs, outputs, side effects, safety, failure behavior, and related proof.
- JavaScript, CSS, SVG, HTML, YAML, and workflow files require the same structured context in a leading comment supported by section comments for major logical regions.
- JSON, TOML, license, ignore, and Markdown files must have a complete entry in `state/source_manifest.json` because those formats either do not safely support comments or are better governed by the central ownership map.

### Every Python Component

Every class, constructor, function, method, private helper, and test function requires a docstring containing all nine labeled fields: Purpose, Inputs, Outputs, How it works, Side effects, Failure behavior, Safety, Example, and Related proof. Private names are not exempt because future maintainers still need to understand and safely change them.

### Every Frontend Function

Every top-level JavaScript function requires nearby JSDoc containing the same nine labeled fields required for Python components. File-level comments alone are not enough.

### Every Frontend Block

- Every CSS selector, at-rule, and keyframe block requires a nearby teaching comment naming Block purpose, How it works, Example, and Safety.
- Every semantic HTML `aside`, `header`, `main`, `nav`, and `section` block requires a nearby teaching comment naming Block purpose, How it works, Example, and Safety.
- JavaScript control flow and rendering regions retain section or reasoning comments wherever a learner could otherwise miss state flow, trust handling, or failure behavior.

### Every Physical Line

`docs/LINE_BY_LINE_CODE_GUIDE.md` must contain a numbered source rendering and plain-language explanation for every physical line in every implementation, automation, configuration, schema, state, workflow, and contract source selected by `scripts/build_learning_guide.py`. Blank lines are included so guide numbering always matches the real file.

`state/learning_coverage.json` records the exact source hash, line count, explained-line count, and guide anchor for every covered file. The total explained count must equal the total physical-line count. Any source edit that leaves either generated artifact stale fails verification.

JSON and other comment-free formats are not exempt. Their line explanations live in the generated guide so the runtime files remain valid for standard parsers.

### Every Structured Contract

Schemas, config files, and state files require a source-manifest explanation. New fields must be named clearly and constrained by schema or verifier checks. Safety booleans must not be loose truth strings.

### Every Behavior

Tests must read as executable examples. Test names and docstrings explain the rule being proved. Assertions should expose the contract, not internal implementation trivia.

## What Not To Do

Do not claim that a file header alone explains the implementation. Do not skip obvious syntax, blank separators, generated contract fields, private helpers, tests, or styling rules from the line guide. Do not hand-edit generated guide rows or coverage hashes.

Do not leave historical chat instructions, personal paths, secrets, speculative claims, or obsolete implementation plans inside source comments.

The requirement is met through structured file headers, descriptive names, types, schemas, component documentation, block-level reasoning comments, executable examples, the source walkthrough, and the implementation guide. A maintainer must be able to answer what, why, who calls it, where data comes from/goes, when effects occur, how failures behave, and which proof protects it.

## Durable Learning Paths

- `docs/IMPLEMENTATION_GUIDE.md` traces folders, layers, request flow, contracts, safety, extension recipes, and debugging.
- `docs/LINE_BY_LINE_CODE_GUIDE.md` explains every physical implementation and contract line using exact source numbering.
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
4. Add or revise CSS, HTML, section, and reasoning comments around changed blocks.
5. Update tests as readable examples.
6. Update architecture when dependencies or data flow changed.
7. Run `python scripts/build_learning_guide.py` after the final covered source change.
8. Run `python scripts/build_learning_guide.py --check`.
9. Run `python scripts/check_explainability.py`.

The project verifier treats explainability failures as build failures.
