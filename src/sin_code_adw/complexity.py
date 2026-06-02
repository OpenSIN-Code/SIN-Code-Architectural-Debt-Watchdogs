"""Analyze cyclomatic, cognitive, and Halstead complexity.

Docs: complexity.py.doc.md
"""

from __future__ import annotations

import ast
import math
import os
from pathlib import Path
from typing import Any

from .report import DebtReport
from .debt_score import DebtScorer
from .smells import god_function, long_file, circular_import, dead_code, deep_nesting as deep_nesting_fn


class ComplexityAnalyzer:
    """Static analysis for complexity metrics and code smells.

    Default thresholds: cyclomatic=10, cognitive=15, file_lines=500, function_lines=50.
    """

    def __init__(self, thresholds: dict | None = None):
        self.thresholds = {
            "cyclomatic": 10,
            "cognitive": 15,
            "file_lines": 500,
            "function_lines": 50,
            "halstead_volume": 1500,
            "halstead_difficulty": 20,
            "deep_nesting": 4,
            "fan_in": 20,
        }
        if thresholds:
            self.thresholds.update(thresholds)
        self._scorer = DebtScorer()

    # ── Public API ──────────────────────────────────────────────────────

    def analyze(self, root: str | Path, exclude: set[str] | None = None) -> list[DebtReport]:
        """Return list of debt items found in *root*."""
        root = Path(root)
        exclude = exclude or set()
        reports: list[DebtReport] = []

        python_files = self._collect_python_files(root, exclude)

        # Build fan-in index for coupling analysis
        fan_in_map = self._build_fan_in_index(python_files)

        for file_path in python_files:
            try:
                source = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            # File-level smells
            file_line_count = len(source.splitlines())
            reports.extend(long_file(file_path, file_line_count, self.thresholds))

            # Per-function / per-class complexity
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    reports.extend(god_function(file_path, node, self.thresholds))
                    reports.extend(deep_nesting_fn(file_path, node, self.thresholds))
                    reports.extend(self._halstead_report(file_path, node))
                    reports.extend(self._cyclomatic_report(file_path, node))
                    reports.extend(self._cognitive_report(file_path, node))

            # Circular imports
            reports.extend(circular_import(file_path, tree, python_files))

            # Dead code
            reports.extend(dead_code(file_path, tree, python_files))

            # High fan-in
            stem = file_path.stem
            fi = fan_in_map.get(stem, 0)
            if fi > self.thresholds["fan_in"]:
                reports.append(
                    DebtReport(
                        file=str(file_path),
                        category="coupling",
                        severity="high",
                        metric="fan_in",
                        value=fi,
                        message=f"High fan-in: imported by {fi} files",
                        line=1,
                    )
                )

        return reports

    def debt_score(self, reports: list[DebtReport]) -> dict[str, Any]:
        """Return overall debt score {total, breakdown, top_offenders, grade}."""
        return self._scorer.compute(reports)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _collect_python_files(self, root: Path, exclude: set[str]) -> list[Path]:
        files = []
        for p in root.rglob("*.py"):
            if any(part in exclude for part in p.parts):
                continue
            files.append(p)
        return sorted(files)

    def _build_fan_in_index(self, files: list[Path]) -> dict[str, int]:
        """Map module name → number of files that import it."""
        counts: dict[str, int] = {}
        for fp in files:
            try:
                tree = ast.parse(fp.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        counts[alias.name] = counts.get(alias.name, 0) + 1
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    counts[mod] = counts.get(mod, 0) + 1
        return counts

    # ── Cyclomatic complexity ────────────────────────────────────────────

    def _cyclomatic_report(self, file_path: Path, node: ast.AST) -> list[DebtReport]:
        score = self._cyclomatic_score(node)
        if score > self.thresholds["cyclomatic"]:
            return [
                DebtReport(
                    file=str(file_path),
                    category="complexity",
                    severity="high",
                    metric="cyclomatic",
                    value=score,
                    message=f"Cyclomatic complexity {score} exceeds threshold {self.thresholds['cyclomatic']}",
                    line=getattr(node, "lineno", 1),
                )
            ]
        return []

    def _cyclomatic_score(self, node: ast.AST) -> int:
        """McCabe-style cyclomatic complexity (1 + decision points)."""
        score = 1
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Assert, ast.ExceptHandler)):
                score += 1
            elif isinstance(child, (ast.And, ast.Or)):
                score += 1
            elif isinstance(child, ast.comprehension):
                score += 1
        return score

    # ── Cognitive complexity ─────────────────────────────────────────────

    def _cognitive_report(self, file_path: Path, node: ast.AST) -> list[DebtReport]:
        score = self._cognitive_score(node)
        if score > self.thresholds["cognitive"]:
            return [
                DebtReport(
                    file=str(file_path),
                    category="complexity",
                    severity="medium",
                    metric="cognitive",
                    value=score,
                    message=f"Cognitive complexity {score} exceeds threshold {self.thresholds['cognitive']}",
                    line=getattr(node, "lineno", 1),
                )
            ]
        return []

    def _cognitive_score(self, node: ast.AST, nesting: int = 0) -> int:
        """Simplified Sonar-style cognitive complexity."""
        score = 0
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.ExceptHandler)):
                score += 1 + nesting
                score += self._cognitive_score(child, nesting + 1)
            elif isinstance(child, (ast.And, ast.Or)):
                score += 1
            elif isinstance(child, ast.FunctionDef):
                # nested function adds 1 + nesting
                score += 1 + nesting
                score += self._cognitive_score(child, nesting + 1)
            else:
                score += self._cognitive_score(child, nesting)
        return score

    # ── Halstead metrics ───────────────────────────────────────────────

    def _halstead_report(self, file_path: Path, node: ast.AST) -> list[DebtReport]:
        h = self._halstead_metrics(node)
        reports = []
        if h["volume"] > self.thresholds["halstead_volume"]:
            reports.append(
                DebtReport(
                    file=str(file_path),
                    category="complexity",
                    severity="medium",
                    metric="halstead_volume",
                    value=h["volume"],
                    message=f"Halstead volume {h['volume']:.1f} exceeds threshold {self.thresholds['halstead_volume']}",
                    line=getattr(node, "lineno", 1),
                )
            )
        if h["difficulty"] > self.thresholds["halstead_difficulty"]:
            reports.append(
                DebtReport(
                    file=str(file_path),
                    category="complexity",
                    severity="medium",
                    metric="halstead_difficulty",
                    value=h["difficulty"],
                    message=f"Halstead difficulty {h['difficulty']:.1f} exceeds threshold {self.thresholds['halstead_difficulty']}",
                    line=getattr(node, "lineno", 1),
                )
            )
        return reports

    def _halstead_metrics(self, node: ast.AST) -> dict[str, float]:
        """Compute Halstead Volume, Difficulty, and Effort for a node."""
        operators = set()
        operands = set()
        n1 = n2 = N1 = N2 = 0

        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, ast.operator):
                name = type(child).__name__
                operators.add(name)
                n1 += 1
                N1 += 1
            elif isinstance(child, ast.unaryop):
                name = type(child).__name__
                operators.add(name)
                n1 += 1
                N1 += 1
            elif isinstance(child, ast.boolop):
                name = type(child).__name__
                operators.add(name)
                n1 += 1
                N1 += 1
            elif isinstance(child, ast.cmpop):
                name = type(child).__name__
                operators.add(name)
                n1 += 1
                N1 += 1
            elif isinstance(child, ast.Name):
                operands.add(child.id)
                n2 += 1
                N2 += 1
            elif isinstance(child, ast.Constant):
                operands.add(repr(child.value))
                n2 += 1
                N2 += 1

        eta1 = max(len(operators), 1)
        eta2 = max(len(operands), 1)
        N = max(n1 + n2, 1)
        volume = N * math.log2(eta1 + eta2) if (eta1 + eta2) > 1 else 0.0
        difficulty = (eta1 / 2) * (N2 / max(eta2, 1))
        effort = volume * difficulty
        return {"volume": volume, "difficulty": difficulty, "effort": effort}
