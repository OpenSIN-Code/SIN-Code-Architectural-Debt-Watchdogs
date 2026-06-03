# __init__.py

Package entry point for `sin_code_adw` (Architectural Debt Watchdogs).

## What it does

Re-exports the public API (`ComplexityAnalyzer`, `CostTracker`, `DebtReport`).

## Public exports

| Symbol | Source |
|--------|--------|
| `ComplexityAnalyzer` | `complexity.py` |
| `CostTracker` | `cost_tracker.py` |
| `DebtReport` | `report.py` |

## Usage

```python
from sin_code_adw import ComplexityAnalyzer
analyzer = ComplexityAnalyzer()
reports = analyzer.analyze(".")
print(analyzer.debt_score(reports))
```

## Known caveats

- `__all__` is the source of truth for `from sin_code_adw import *`;
  add new public symbols to both the import list and `__all__`.
