# `debt_score.py` — Debt Scoring

What this file does: aggregates complexity reports and code smells into a single debt score with grade and top offenders.

## Dependencies

- Imported by: `complexity.py`, tests, MCP server

## Public API

- `DebtScorer.compute(reports)` → `{total, breakdown, top_offenders, grade}`

## Usage

```python
from sin_code_adw.complexity import ComplexityAnalyzer
analyzer = ComplexityAnalyzer()
reports = analyzer.analyze(".")
score = analyzer.debt_score(reports)
```

## Notes

Grades are A (0–20), B (20–40), C (40–60), D (60–80), F (80+). Top offenders are the 10 highest-severity items.
