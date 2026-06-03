"""Dead code detector.

Docs: dead_code.doc.md
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ..report import DebtReport


def detect(file_path: Path, tree: ast.AST, all_files: list[Path]) -> list[DebtReport]:
    """Find unreachable code and unused top-level definitions.

    Two checks are run per file:
    1. **Unreachable code** inside any function/async function body:
       statements that follow a `return` / `raise` / `break` / `continue`.
    2. **Unused top-level definitions**: public (non-`_`-prefixed)
       functions or classes not referenced from any other file.

    Args:
        file_path: The file under analysis.
        tree: Pre-parsed AST of `file_path`.
        all_files: Every Python file in the project.

    Returns:
        List of `DebtReport` records (possibly empty).
    """
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

    # Unused top-level functions/classes. `__init__.py` is skipped
    # because its top-level names are part of the package's public API
    # and may be re-exported without being directly imported.
    if file_path.name != "__init__.py":
        defined = _top_level_names(tree)
        used = _names_used_in_project(file_path, all_files)
        for name in defined:
            # Underscore-prefixed names are private (convention);
            # we don't flag them as dead.
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
    """Naive check: statements after `return`/`raise`/`break`/`continue` in the same block.

    The `if`-reset is intentional: a conditional `return` does NOT
    terminate the block (the other branch may still execute). A
    future refinement could use a proper control-flow graph.
    """
    unreachable: list[int] = []
    for body in [getattr(node, "body", []), getattr(node, "orelse", [])]:
        terminated = False
        for stmt in body:
            if terminated and isinstance(stmt, ast.stmt):
                unreachable.append(getattr(stmt, "lineno", 1))
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                terminated = True
            elif isinstance(stmt, ast.If):
                # Reset after an `if` block: the other branch may still execute.
                terminated = False
    return unreachable


def _top_level_names(tree: ast.AST) -> set[str]:
    """Return the set of top-level function / class names in a module."""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _names_used_in_project(file_path: Path, all_files: list[Path]) -> set[str]:
    """Simple check: does any other file import this file or reference its names?

    We match both `from own_module import X` and bare-name references
    (`ast.Name`). The latter is noisy (a local variable shadows a
    top-level name sometimes), but the false-positive rate is
    acceptable for a heuristic.
    """
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
