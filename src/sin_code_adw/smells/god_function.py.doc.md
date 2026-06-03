# smells/god_function.py

Detect functions that are too long or have too many statements.

## What it does

Two checks per function:

1. **Length**: the function's `end_lineno - lineno + 1` exceeds
   `thresholds["function_lines"]` (default 50).
2. **Statement count**: the function contains more than
   `thresholds["function_statements"]` (default 40) AST statements.

Either trigger emits a `DebtReport` with severity `medium`.

## Dependencies

- `report.py` — `DebtReport`

## Public API

| Symbol | Purpose |
|--------|---------|
| `detect(file_path, node, thresholds)` | Run the check (returns 0-2 reports) |

## Known caveats

- Statement count includes nested function definitions and class
  bodies, which can inflate the count for DSL-style code.
- `end_lineno` is only available on Python 3.8+; on older versions
  the function falls back to `lineno`, which yields `1` line.
- Cyclomatic complexity is a *better* proxy for "too much logic"
  than raw statement count; this detector is a cheap pre-filter.
