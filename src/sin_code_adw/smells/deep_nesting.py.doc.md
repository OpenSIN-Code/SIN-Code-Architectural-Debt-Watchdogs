# smells/deep_nesting.py

Detect functions whose control-flow nesting exceeds a threshold.

## What it does

Computes the maximum nesting depth of `if` / `while` / `for` / `with`
/ `except` / `try` blocks inside a function. If that depth exceeds
`thresholds["deep_nesting"]` (default 4), emits a single
`DebtReport` for the function.

## Dependencies

- `report.py` — `DebtReport`

## Public API

| Symbol | Purpose |
|--------|---------|
| `detect(file_path, node, thresholds)` | Run the check |
| `_max_nesting_depth(node)` | Recursive depth computation |

## Known caveats

- Nesting depth is counted per control-flow structure, not per
  indentation level. A `with` does not add depth, but a nested
  `if` inside an `if` does.
- The function does not descend into nested functions / classes for
  separate depth accounting; one function's depth is computed
  from its own top-level scope downward.
