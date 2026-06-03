"""Circular import detector.

Docs: circular_import.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


def detect(file_path: Path, tree: ast.AST, all_files: list[Path]) -> list[DebtReport]:
    """Detect simple circular imports via naive module name matching.

    Args:
        file_path: The file under analysis.
        tree: Pre-parsed AST of `file_path`.
        all_files: Every Python file in the project (for cross-file checks).

    Returns:
        A list of `DebtReport` records. Empty if no cycles are found.
    """
    reports = []
    imports = _extract_imports(tree)
    own_module = _module_name(file_path)
    for imp in imports:
        # Walk the project to find any file that itself imports `imp`.
        # For each match, check whether that file also imports us back.
        # The first match per `imp` triggers a report (we `break`).
        for other in all_files:
            if other == file_path:
                continue
            other_module = _module_name(other)
            if other_module == imp:
                # Re-parse `other` for its import list. Swallow parse
                # errors silently — a broken file is the user's problem,
                # not a cycle signal.
                try:
                    other_tree = ast.parse(other.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    continue
                other_imports = _extract_imports(other_tree)
                if own_module in other_imports:
                    reports.append(
                        DebtReport(
                            file=str(file_path),
                            category="smell",
                            severity="high",
                            metric="circular_import",
                            value=1,
                            message=f"Circular import with {other}",
                            line=1,
                        )
                    )
                    break
    return reports


def _extract_imports(tree: ast.AST) -> list[str]:
    """Return the list of imported module names from a parsed AST.

    Includes both `import x.y.z` and `from x.y import z` cases.
    Relative imports (`from . import x`) are ignored because their
    resolved name depends on package context we don't have here.
    """
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _module_name(file_path: Path) -> str:
    """Convert file path to a module name.

    Currently uses just `file_path.stem` (file name without extension).
    This is intentionally naive — a future revision should walk
    parents to construct a dotted package name.
    """
    return file_path.stem
