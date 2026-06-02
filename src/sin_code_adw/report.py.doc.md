# `report.py` — Debt Report

What this file does: data model for individual debt findings (complexity, smells, coupling).

## Dependencies

- Imported by: `complexity.py`, `smells`, `debt_score.py`, tests

## Types

- `DebtReport` — file, category, severity, metric, value, message, line

## Usage

```python
from sin_code_adw.report import DebtReport
report = DebtReport(file="app.py", category="complexity", severity="high", metric="cyclomatic", value=15, message="Too complex", line=42)
```

## Notes

Severity is one of `low`, `medium`, `high`. Category is one of `complexity`, `smell`, `coupling`.
