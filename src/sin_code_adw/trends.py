"""Trend analysis over time.

Docs: trends.py.doc.md
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
from datetime import datetime
import json

from .report import DebtReport


class TrendAnalyzer:
    """Compare current debt reports against a previous snapshot."""

    def __init__(self, snapshot_dir: str | Path | None = None):
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else Path(".adw_snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, reports: list[DebtReport], label: str | None = None) -> Path:
        """Persist current reports as JSON snapshot."""
        label = label or datetime.now().isoformat()
        path = self.snapshot_dir / f"{label}.json"
        data = [r.to_dict() for r in reports]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def compare(self, current: list[DebtReport], baseline_path: Path) -> dict[str, Any]:
        """Return delta between current reports and baseline snapshot."""
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_raw = json.load(f)

        baseline = [DebtReport(**r) for r in baseline_raw]
        current_set = {self._key(r) for r in current}
        baseline_set = {self._key(r) for r in baseline}

        new_items = current_set - baseline_set
        resolved_items = baseline_set - current_set
        unchanged = current_set & baseline_set

        return {
            "new": len(new_items),
            "resolved": len(resolved_items),
            "unchanged": len(unchanged),
            "new_details": [self._find(current, k) for k in new_items],
            "resolved_details": [self._find(baseline, k) for k in resolved_items],
        }

    def _key(self, r: DebtReport) -> str:
        return f"{r.file}:{r.line}:{r.metric}:{r.message}"

    def _find(self, reports: list[DebtReport], key: str) -> dict[str, Any]:
        for r in reports:
            if self._key(r) == key:
                return r.to_dict()
        return {}
