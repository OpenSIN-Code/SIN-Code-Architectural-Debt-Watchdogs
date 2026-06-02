"""Debt scoring algorithm.

Docs: debt_score.py.doc.md
"""

from __future__ import annotations

from typing import Any

from .report import DebtReport


class DebtScorer:
    """Convert a list of DebtReport items into a 0-100 score and letter grade."""

    # Severity weights
    WEIGHTS = {
        "low": 1,
        "medium": 3,
        "high": 9,
    }

    def compute(self, reports: list[DebtReport]) -> dict[str, Any]:
        if not reports:
            return {
                "total": 0.0,
                "breakdown": {},
                "top_offenders": [],
                "grade": "A",
            }

        total_weight = sum(self.WEIGHTS.get(r.severity, 1) for r in reports)
        # Scale to 0-100 using a soft log curve
        total = min(100.0, round(total_weight * math.log1p(total_weight + 1), 2))

        breakdown: dict[str, dict[str, Any]] = {}
        for r in reports:
            cat = r.category
            if cat not in breakdown:
                breakdown[cat] = {"count": 0, "weight": 0}
            breakdown[cat]["count"] += 1
            breakdown[cat]["weight"] += self.WEIGHTS.get(r.severity, 1)

        # Top offenders by weight
        offender_weights: dict[str, int] = {}
        for r in reports:
            offender_weights[r.file] = offender_weights.get(r.file, 0) + self.WEIGHTS.get(r.severity, 1)
        top_offenders = sorted(
            [{"file": k, "weight": v} for k, v in offender_weights.items()],
            key=lambda x: x["weight"],
            reverse=True,
        )[:10]

        grade = self._grade(total)

        return {
            "total": total,
            "breakdown": breakdown,
            "top_offenders": top_offenders,
            "grade": grade,
        }

    def _grade(self, total: float) -> str:
        if total < 10:
            return "A"
        if total < 25:
            return "B"
        if total < 45:
            return "C"
        if total < 70:
            return "D"
        return "F"


import math
