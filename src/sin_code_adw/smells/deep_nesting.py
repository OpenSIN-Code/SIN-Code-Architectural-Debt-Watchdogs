"""Deep nesting detector.

Docs: deep_nesting.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


# Default depth limit. 4 levels of nested control flow is the
# conventional readability ceiling; > 4 typically signals an
# opportunity to extract a helper function.
_DEFAULT_DEPTH_LIMIT = 4

# AST node kinds that increment nesting depth. `Try` is included
# because the `try` block itself is a control-flow boundary even
# though the contained handlers are siblings.
_NESTING_NODES = (ast.If, ast.While, ast.For, ast.With, ast.ExceptHandler, ast.Try)


def detect(file_path: Path, node: ast.AST, thresholds: dict[str, Any]) -> list[DebtReport]:
    """Flag functions with nesting depth > threshold.

    Args:
        file_path: File containing the function.
        node: A function-like AST node (`FunctionDef` / `AsyncFunctionDef`).
        thresholds: Dict of thresholds; reads `deep_nesting`.

    Returns:
        A single-element list (or empty) of `DebtReport`.
    """
    max_depth = _max_nesting_depth(node)
    limit = thresholds.get("deep_nesting", _DEFAULT_DEPTH_LIMIT)
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
    """Compute maximum nesting depth of control structures inside a node.

    The recursive helper uses `iter_child_nodes` rather than `walk` so
    that the root node itself is not double-counted.
    """
    def depth(n: ast.AST, current: int) -> int:
        if isinstance(n, _NESTING_NODES):
            current += 1
        child_max = 0
        for child in ast.iter_child_nodes(n):
            child_max = max(child_max, depth(child, current))
        return max(current, child_max)

    return depth(node, 0)
