# SIN-Code-Architectural-Debt-Watchdogs (ADW)

Python package for analyzing architectural debt, code smells, and tracking costs.

## Quick start

```bash
pip install sin-code-adw
```

```python
from sin_code_adw.complexity import ComplexityAnalyzer
from sin_code_adw.cost_tracker import CostTracker

analyzer = ComplexityAnalyzer()
reports = analyzer.analyze(".", exclude={"node_modules", ".venv", ".git"})
baseline = analyzer.debt_score(reports)
print(baseline)
```

## Modules

- `complexity` — cyclomatic, cognitive, Halstead metrics
- `smells` — god functions, long files, circular imports, dead code, deep nesting
- `cost_tracker` — LLM token costs and infrastructure costs
- `trends` — snapshot and compare debt over time

## Tests

```bash
pytest tests/ -v
```

## License

MIT
