# Code Explainability Standard

## Goal

Any careful developer, reviewer, or AI model should be able to determine what a file owns, why it exists, how data moves through it, which invariants matter, and what remains unsafe or unproven without relying on private chat history.

## Required Explanation Layers

### Every File

- Python files require a module docstring.
- JavaScript and CSS files require a leading block comment describing purpose, inputs, outputs, and safety boundaries.
- HTML requires an opening purpose comment and section comments for major interface regions.
- YAML and workflow files require a leading purpose comment.
- JSON, TOML, SVG, license, ignore, and Markdown files must have a complete entry in `state/source_manifest.json` because some formats do not safely support comments.

### Every Public Python Component

Public classes, functions, methods, and test functions require docstrings. A useful docstring states the observable responsibility and, when relevant, inputs, output, side effects, containment, and failure behavior.

### Every Non-Obvious Block

Add a nearby comment when code enforces a safety boundary, validates containment, intentionally avoids an action, translates between contracts, retries asynchronous behavior, or uses a choice that a maintainer might otherwise "simplify" incorrectly.

### Every Structured Contract

Schemas, config files, and state files require a source-manifest explanation. New fields must be named clearly and constrained by schema or verifier checks. Safety booleans must not be loose truth strings.

### Every Behavior

Tests must read as executable examples. Test names and docstrings explain the rule being proved. Assertions should expose the contract, not internal implementation trivia.

## What Not To Do

Do not add comments such as "increment the counter" above `counter += 1`. Line-by-line narration duplicates syntax, hides the important reasoning, and becomes stale after edits. Explain meaningful units and decisions instead. This provides more usable detail than commenting every token.

Do not leave historical chat instructions, personal paths, secrets, speculative claims, or obsolete implementation plans inside source comments.

## Change Checklist

For every changed file:

1. Confirm its source-manifest entry still matches its responsibility.
2. Update file-level purpose text if ownership changed.
3. Update public docstrings when behavior or failure modes changed.
4. Add or revise reasoning comments around new non-obvious blocks.
5. Update tests as readable examples.
6. Update architecture when dependencies or data flow changed.
7. Run `python scripts/check_explainability.py`.

The project verifier treats explainability failures as build failures.
