# `circular_import.py` — Circular Import Detector

What this file does: detects circular imports between Python modules.

## Dependencies

- Imported by: `smells/__init__.py`, `complexity.py`

## Public API

- `circular_import(file_path, tree, all_files)` → list[DebtReport]

## Notes

Uses AST import analysis to build a dependency graph and find cycles.
