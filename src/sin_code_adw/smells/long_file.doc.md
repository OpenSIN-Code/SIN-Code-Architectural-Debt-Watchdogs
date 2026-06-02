# `long_file.py` — Long File Detector

What this file does: detects files that exceed a line count threshold.

## Dependencies

- Imported by: `smells/__init__.py`, `complexity.py`

## Public API

- `long_file(file_path, line_count, thresholds)` → list[DebtReport]

## Notes

Default threshold: 500 lines per file.
