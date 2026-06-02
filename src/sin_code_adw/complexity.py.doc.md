# complexity.py

What: Static analysis engine for cyclomatic, cognitive, and Halstead complexity plus smell orchestration.

Dependencies: `report.py`, `debt_score.py`, `smells/*`
- `report.py` — `DebtReport` dataclass used for all emitted items.
- `debt_score.py` — `DebtScorer` computes 0-100 score and grade.
- `smells/*` — each smell module exposes a `detect()` function.

Config: `thresholds` dict passed to `__init__`. Defaults are hardcoded in `__init__`.

Usage:
```python
analyzer = ComplexityAnalyzer(thresholds={"cyclomatic": 8})
reports = analyzer.analyze("./src")
score = analyzer.debt_score(reports)
```

Caveats:
- `circular_import` detector is naive (string-matching module names) and may produce false positives.
- Dead code detection only checks top-level functions/classes.
- `fan_in` uses import count across the project; not a full graph analysis.
