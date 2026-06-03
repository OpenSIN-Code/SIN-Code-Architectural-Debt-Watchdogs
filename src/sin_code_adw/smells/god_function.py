"""God function detector.

Docs: god_function.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


# Default thresholds. 50 lines and 40 statements is a "smells too big"
# heuristic — these are conservative for the kind of code we expect
# to see in the SIN-Code stack.
_DEFAULT_FUNCTION_LINES = 50
_DEFAULT_FUNCTION_STATEMENTS = 40


def detect(file_path: Path, node: ast.AST, thresholds: dict[str, Any]) -> list[DebtReport]:
    """Flag functions that are too long or too complex.

    Args:
        file_path: File containing the function.
        node: Candidate AST node.
        thresholds: Dict of thresholds; reads `function_lines` and `function_statements`.

    Returns:
        0, 1, or 2 `DebtReport` records depending on which thresholds are breached.
    """
    reports = []
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Non-function nodes are silently ignored; this detector only
        # runs on function-shaped AST nodes.
        return reports

    # `end_lineno` was added in Python 3.8; on older versions we fall
    # back to a 1-line estimate. The fallback is rare in practice today
    # but kept for forward-compat.
    lines = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
    if lines > thresholds.get("function_lines", _DEFAULT_FUNCTION_LINES):
        reports.append(
            DebtReport(
                file=str(file_path),
                category="smell",
                severity="medium",
                metric="function_lines",
                value=lines,
                message=f"God function: {lines} lines exceeds threshold {thresholds['function_lines']}",
                line=node.lineno,
            )
        )

    # Statement count is a cheap proxy for cyclomatic complexity.
    # It over-counts (nested function defs add their statements) but
    # is a good pre-filter before running the more expensive
    # `ComplexityAnalyzer` on the same file.
    stmt_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.stmt))
    if stmt_count > thresholds.get("function_statements", _DEFAULT_FUNCTION_STATEMENTS):
        reports.append(
            DebtReport(
                file=str(file_path),
                category="smell",
                severity="medium",
                metric="function_statements",
                value=stmt_count,
                message=f"God function: {stmt_count} statements",
                line=node.lineno,
            )
        )

    return reports
