# `god_function.py` — God Function Detector

What this file does: detects functions that are too long or have too many parameters.

## Dependencies

- Imported by: `smells/__init__.py`, `complexity.py`

## Public API

- `god_function(file_path, node, thresholds)` → list[DebtReport]

## Notes

Default threshold: 50 lines per function.
