# `deep_nesting.py` — Deep Nesting Detector

What this file does: detects functions with excessive nesting depth.

## Dependencies

- Imported by: `smells/__init__.py`, `complexity.py`

## Public API

- `deep_nesting(file_path, node, thresholds)` → list[DebtReport]

## Notes

Default threshold: 4 levels of nesting.
