"""Debt scoring algorithm.

Docs: debt_score.py.doc.md
"""

from __future__ import annotations

import math
from typing import Any

from .report import DebtReport


# Top offenders returned by `compute`. Ten files is the standard
# "show me the worst" window for a code-health dashboard.
_TOP_OFFENDERS_LIMIT = 10


class DebtScorer:
    """Convert a list of `DebtReport` items into a 0-100 score and letter grade.

    The score uses a soft log curve: low counts of debt are weighted
    linearly, then saturate near 100. The exact formula is
    `min(100, weight * log1p(weight + 1))`.
    """

    # Severity weights. Geometric (1/3/9) so a single high-severity
    # issue counts as much as nine low-severity issues, mirroring
    # common debt-prioritization rubrics.
    WEIGHTS = {
        "low": 1,
        "medium": 3,
        "high": 9,
    }

    def compute(self, reports: list[DebtReport]) -> dict[str, Any]:
        """Aggregate reports into a score + breakdown + offenders.

        Args:
            reports: List of `DebtReport` items from the analyzer.

        Returns:
            Dict with keys: `total` (float, 0-100), `breakdown`
            (per-category counts and weights), `top_offenders`
            (top 10 files by aggregate weight), `grade` (A-F).
        """
        if not reports:
            return {
                "total": 0.0,
                "breakdown": {},
                "top_offenders": [],
                "grade": "A",
            }

        total_weight = sum(self.WEIGHTS.get(r.severity, 1) for r in reports)
        # Scale to 0-100 using a soft log curve. `log1p(w+1)` keeps
        # the score growing but bounded; `min(100, ...)` clamps.
        total = min(100.0, round(total_weight * math.log1p(total_weight + 1), 2))

        # Per-category aggregate (count + total weight).
        breakdown: dict[str, dict[str, Any]] = {}
        for r in reports:
            cat = r.category
            if cat not in breakdown:
                breakdown[cat] = {"count": 0, "weight": 0}
            breakdown[cat]["count"] += 1
            breakdown[cat]["weight"] += self.WEIGHTS.get(r.severity, 1)

        # Top offenders by aggregate weight. Ties are broken by
        # dict insertion order (first occurrence wins).
        offender_weights: dict[str, int] = {}
        for r in reports:
            offender_weights[r.file] = offender_weights.get(r.file, 0) + self.WEIGHTS.get(r.severity, 1)
        top_offenders = sorted(
            [{"file": k, "weight": v} for k, v in offender_weights.items()],
            key=lambda x: x["weight"],
            reverse=True,
        )[:_TOP_OFFENDERS_LIMIT]

        grade = self._grade(total)

        return {
            "total": total,
            "breakdown": breakdown,
            "top_offenders": top_offenders,
            "grade": grade,
        }

    def _grade(self, total: float) -> str:
        """Map a 0-100 score to a letter grade.

        Bands chosen to roughly match academic grading:
        - A: < 10 (essentially clean)
        - B: < 25 (manageable)
        - C: < 45 (worth tackling)
        - D: < 70 (urgent)
        - F: >= 70 (critical)
        """
        if total < 10:
            return "A"
        if total < 25:
            return "B"
        if total < 45:
            return "C"
        if total < 70:
            return "D"
        return "F"
