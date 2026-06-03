"""Long file detector.

Docs: long_file.doc.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..report import DebtReport


# Default line-count threshold. 500 is the conventional ceiling for
# "single file" code; beyond that, splitting is usually warranted.
_DEFAULT_FILE_LINES = 500


def detect(file_path: Path, line_count: int, thresholds: dict[str, Any]) -> list[DebtReport]:
    """Flag files exceeding the line threshold.

    Args:
        file_path: File under analysis.
        line_count: Total line count (caller-supplied so blank lines
            and comments can be filtered in a future refinement).
        thresholds: Dict of thresholds; reads `file_lines`.

    Returns:
        Single-element list (or empty) of `DebtReport`.
    """
    if line_count > thresholds.get("file_lines", _DEFAULT_FILE_LINES):
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
