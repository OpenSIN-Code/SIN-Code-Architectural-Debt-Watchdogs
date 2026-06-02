"""Deep nesting detector.

Docs: smells/deep_nesting.py.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


def detect(file_path: Path, node: ast.AST, thresholds: dict[str, Any]) -> list[DebtReport]:
    """Flag functions with nesting depth > threshold."""
    max_depth = _max_nesting_depth(node)
    limit = thresholds.get("deep_nesting", 4)
    if max_depth > limit:
        return [
            DebtReport(
                file=str(file_path),
                category="smell",
                severity="medium",
                metric="deep_nesting",
                value=max_depth,
                message=f"Deep nesting: depth {max_depth} exceeds threshold {limit}",
                line=getattr(node, "lineno", 1),
            )
        ]
    return []


def _max_nesting_depth(node: ast.AST) -> int:
    """Compute maximum nesting depth of control structures inside a node."""
    def depth(n: ast.AST, current: int) -> int:
        if isinstance(n, (ast.If, ast.While, ast.For, ast.With, ast.ExceptHandler, ast.Try)):
            current += 1
        child_max = 0
        for child in ast.iter_child_nodes(n):
            child_max = max(child_max, depth(child, current))
        return max(current, child_max)

    return depth(node, 0)
