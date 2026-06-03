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


# Default snapshot directory. Hidden + dotfile-prefixed so it
# doesn't clutter `ls` and is easy to `.gitignore` in a project.
_DEFAULT_SNAPSHOT_DIR = ".adw_snapshots"


class TrendAnalyzer:
    """Compare current debt reports against a previous snapshot.

    Snapshots are JSON files stored in `snapshot_dir`. Each snapshot
    is a list of `DebtReport` dicts; the comparison key is
    `file:line:metric:message` (see `_key`).
    """

    def __init__(self, snapshot_dir: str | Path | None = None):
        """Initialize the analyzer.

        Args:
            snapshot_dir: Where to store snapshots. Created if missing.
                Defaults to `.adw_snapshots/` in the cwd.
        """
        self.snapshot_dir = (
            Path(snapshot_dir) if snapshot_dir else Path(_DEFAULT_SNAPSHOT_DIR)
        )
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(
        self, reports: list[DebtReport], label: str | None = None
    ) -> Path:
        """Persist current reports as JSON snapshot.

        Args:
            reports: The reports to snapshot.
            label: Filename stem (without `.json`). Defaults to
                `datetime.now().isoformat()` for easy sorting.

        Returns:
            The path the snapshot was written to.
        """
        # ISO timestamp sorts naturally as a filename, which makes
        # `ls .adw_snapshots/` a usable timeline view.
        label = label or datetime.now().isoformat()
        path = self.snapshot_dir / f"{label}.json"
        data = [r.to_dict() for r in reports]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def compare(self, current: list[DebtReport], baseline_path: Path) -> dict[str, Any]:
        """Return delta between current reports and a baseline snapshot.

        Args:
            current: The fresh `DebtReport` list.
            baseline_path: Path to a snapshot file produced by
                `save_snapshot` (or hand-written matching the schema).

        Returns:
            Dict with counts (`new`, `resolved`, `unchanged`) and the
            corresponding `*_details` lists of full report dicts.
        """
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_raw = json.load(f)

        baseline = [DebtReport(**r) for r in baseline_raw]
        current_set = {self._key(r) for r in current}
        baseline_set = {self._key(r) for r in baseline}

        # Set algebra: items only in `current` are new; only in
        # `baseline` are resolved; in both are unchanged.
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
        """Stable identity for a debt report (used in set diff)."""
        return f"{r.file}:{r.line}:{r.metric}:{r.message}"

    def _find(self, reports: list[DebtReport], key: str) -> dict[str, Any]:
        """Return the first report matching `key`, or `{}` if none."""
        for r in reports:
            if self._key(r) == key:
                return r.to_dict()
        return {}
