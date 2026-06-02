"""God function detector.

Docs: god_function.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


def detect(file_path: Path, node: ast.AST, thresholds: dict[str, Any]) -> list[DebtReport]:
    """Flag functions that are too long or too complex."""
    reports = []
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return reports

    lines = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
    if lines > thresholds.get("function_lines", 50):
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

    # Count statements as a proxy for cyclomatic
    stmt_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.stmt))
    if stmt_count > thresholds.get("function_statements", 40):
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
