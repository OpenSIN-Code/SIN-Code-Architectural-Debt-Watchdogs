"""Debt report dataclass.

Docs: report.py.doc.md
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebtReport:
    """One debt finding produced by the analyzer or a smell detector.

    Attributes:
        file: Path of the offending file (as a string for JSON friendliness).
        category: Logical grouping (`complexity`, `smell`, `coupling`, ...).
        severity: One of `low`, `medium`, `high`. Drives the
            `DebtScorer.WEIGHTS` multiplier.
        metric: The specific metric that tripped the threshold
            (`cyclomatic`, `file_lines`, `fan_in`, ...).
        value: The raw measured value (number, str, etc.).
        message: Human-readable description (for the report UI).
        line: Source line number (1-based; 1 if file-level).
        meta: Free-form supplementary data.
    """

    file: str
    category: str
    severity: str  # low | medium | high
    metric: str
    value: Any
    message: str
    line: int = 1
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to a plain dict (JSON-friendly)."""
        return {
            "file": self.file,
            "category": self.category,
            "severity": self.severity,
            "metric": self.metric,
            "value": self.value,
            "message": self.message,
            "line": self.line,
            "meta": self.meta,
        }
