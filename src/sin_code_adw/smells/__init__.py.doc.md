# `__init__.py` — Smells Package

What this file does: package-level exports for code smell detectors.

## Dependencies

- Imported by: `complexity.py`, tests

## Exports

- `god_function`, `long_file`, `circular_import`, `dead_code`, `deep_nesting` — detector functions

## Usage

```python
from sin_code_adw.smells import god_function, long_file
```

## Notes

Each detector returns a list of `DebtReport` objects.
