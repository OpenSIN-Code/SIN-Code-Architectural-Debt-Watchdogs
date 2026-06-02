"""Dead code detector.

Docs: smells/dead_code.py.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


def detect(file_path: Path, tree: ast.AST, all_files: list[Path]) -> list[DebtReport]:
    """Find unreachable code and unused top-level definitions."""
    reports = []

    # Unreachable code after return/raise/break/continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            unreachable = _find_unreachable(node)
            for line in unreachable:
                reports.append(
                    DebtReport(
                        file=str(file_path),
                        category="smell",
                        severity="medium",
                        metric="unreachable_code",
                        value=line,
                        message=f"Unreachable code after control-flow statement at line {line}",
                        line=line,
                    )
                )

    # Unused top-level functions/classes
    if file_path.name != "__init__.py":
        defined = _top_level_names(tree)
        used = _names_used_in_project(file_path, all_files)
        for name in defined:
            if name not in used and not name.startswith("_"):
                reports.append(
                    DebtReport(
                        file=str(file_path),
                        category="smell",
                        severity="low",
                        metric="unused_definition",
                        value=name,
                        message=f"Potentially unused top-level definition: {name}",
                        line=1,
                    )
                )

    return reports


def _find_unreachable(node: ast.AST) -> list[int]:
    """Naive check: statements after return/raise/continue/break in same block."""
    unreachable: list[int] = []
    for body in [getattr(node, "body", []), getattr(node, "orelse", [])]:
        terminated = False
        for stmt in body:
            if terminated and isinstance(stmt, ast.stmt):
                unreachable.append(getattr(stmt, "lineno", 1))
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                terminated = True
            elif isinstance(stmt, ast.If):
                # reset after if block for simplicity
                terminated = False
    return unreachable


def _top_level_names(tree: ast.AST) -> set[str]:
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _names_used_in_project(file_path: Path, all_files: list[Path]) -> set[str]:
    """Simple check: does any other file import this file or reference its names."""
    used = set()
    own_module = file_path.stem
    for other in all_files:
        if other == file_path:
            continue
        try:
            src = other.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == own_module or node.module == file_path.stem:
                    for alias in node.names:
                        used.add(alias.name)
            elif isinstance(node, ast.Name):
                used.add(node.id)
    return used
