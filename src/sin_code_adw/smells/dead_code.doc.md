# `dead_code.py` — Dead Code Detector

What this file does: detects unused functions and variables in a module.

## Dependencies

- Imported by: `smells/__init__.py`, `complexity.py`

## Public API

- `dead_code(file_path, tree, all_files)` → list[DebtReport]

## Notes

Conservative heuristic: only flags functions that are never called within the same package.
