"""Long file detector.

Docs: smells/long_file.py.doc.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..report import DebtReport


def detect(file_path: Path, line_count: int, thresholds: dict[str, Any]) -> list[DebtReport]:
    """Flag files exceeding line threshold."""
    if line_count > thresholds.get("file_lines", 500):
        return [
            DebtReport(
                file=str(file_path),
                category="smell",
                severity="low",
                metric="file_lines",
                value=line_count,
                message=f"Long file: {line_count} lines exceeds threshold {thresholds['file_lines']}",
                line=1,
            )
        ]
    return []
