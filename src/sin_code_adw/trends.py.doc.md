# `trends.py` — Debt Trend Tracking

What this file does: snapshot and compare debt scores over time to detect regressions or improvements.

## Dependencies

- Imported by: tests, CLI
- Imports: `complexity`, `report`

## Public API

- `TrendTracker()` — track debt snapshots
- `snapshot(reports, label="main")` — save a named snapshot
- `compare(label_a, label_b)` — delta between two snapshots

## Usage

```python
from sin_code_adw.trends import TrendTracker
tracker = TrendTracker()
tracker.snapshot(reports, label="2024-01-01")
```

## Notes

Snapshots are stored in `.sin/debt-trends.json` by default.
