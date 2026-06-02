"""Debt report dataclass.

Docs: report.py.doc.md
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebtReport:
    file: str
    category: str
    severity: str  # low | medium | high
    metric: str
    value: Any
    message: str
    line: int = 1
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
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
