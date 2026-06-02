"""Tests for sin_code_adw.

Docs: tests/__init__.py.doc.md
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from sin_code_adw.complexity import ComplexityAnalyzer
from sin_code_adw.cost_tracker import CostTracker
from sin_code_adw.debt_score import DebtScorer
from sin_code_adw.report import DebtReport
from sin_code_adw.trends import TrendAnalyzer


# ── Helpers ─────────────────────────────────────────────────────────


def write_code(tmp_path: Path, filename: str, code: str) -> Path:
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(code)
    return p


# ── ComplexityAnalyzer ───────────────────────────────────────────────


class TestComplexityAnalyzer:
    def test_analyze_empty_repo(self, tmp_path):
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        assert reports == []

    def test_cyclomatic_threshold(self, tmp_path):
        code = """
def foo(x):
    if x > 0:
        if x < 10:
            if x % 2 == 0:
                if x % 3 == 0:
                    return 1
                elif x % 5 == 0:
                    return 2
                else:
                    return 3
            elif x % 7 == 0:
                return 4
            else:
                return 5
        elif x < 20:
            if x % 2 == 0:
                return 6
            else:
                return 7
        else:
            return 8
    elif x == 0:
        if x == 0:
            return 0
        else:
            return -2
    else:
        return -1
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        cyclo = [r for r in reports if r.metric == "cyclomatic"]
        assert len(cyclo) == 1
        assert cyclo[0].value > 10

    def test_cognitive_threshold(self, tmp_path):
        code = """
def bar(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                while i < 10:
                    if i == 5:
                        break
                    i += 1
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer(thresholds={"cognitive": 5})
        reports = analyzer.analyze(tmp_path)
        cog = [r for r in reports if r.metric == "cognitive"]
        assert len(cog) == 1
        assert cog[0].value > 5

    def test_halstead_volume(self, tmp_path):
        code = """
def calc(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t):
    return (a + b) * (c - d) / (e + f) + (g - h) * (i + j) * (k + l) / (m + n) + (o + p) * (q - r) / (s + t)
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer(thresholds={"halstead_volume": 50})
        reports = analyzer.analyze(tmp_path)
        vol = [r for r in reports if r.metric == "halstead_volume"]
        assert len(vol) == 1
        assert vol[0].value > 50

    def test_long_file(self, tmp_path):
        lines = ["x = 1"] * 600
        write_code(tmp_path, "test.py", "\n".join(lines))
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        lf = [r for r in reports if r.metric == "file_lines"]
        assert len(lf) == 1
        assert lf[0].value == 600

    def test_god_function(self, tmp_path):
        lines = ["    x = 1"] * 60
        code = "def big():\n" + "\n".join(lines)
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        gf = [r for r in reports if r.metric == "function_lines"]
        assert len(gf) == 1
        assert gf[0].value > 50

    def test_deep_nesting(self, tmp_path):
        code = """
def nested(x):
    if x:
        for i in range(10):
            if i:
                while i < 5:
                    if i == 3:
                        pass
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer(thresholds={"deep_nesting": 3})
        reports = analyzer.analyze(tmp_path)
        dn = [r for r in reports if r.metric == "deep_nesting"]
        assert len(dn) == 1
        assert dn[0].value > 3

    def test_unreachable_code(self, tmp_path):
        code = """
def dead(x):
    return x
    y = 2
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        unc = [r for r in reports if r.metric == "unreachable_code"]
        assert len(unc) == 1

    def test_exclude_dirs(self, tmp_path):
        write_code(tmp_path / "node_modules", "test.py", "x = 1")
        write_code(tmp_path, "main.py", "x = 1")
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path, exclude={"node_modules"})
        files = {r.file for r in reports}
        assert "node_modules" not in " ".join(files)


# ── DebtScore ────────────────────────────────────────────────────────


class TestDebtScore:
    def test_empty_reports(self):
        scorer = DebtScorer()
        result = scorer.compute([])
        assert result["total"] == 0.0
        assert result["grade"] == "A"

    def test_single_high_report(self):
        scorer = DebtScorer()
        reports = [
            DebtReport("a.py", "complexity", "high", "cyclomatic", 15, "msg", 1),
        ]
        result = scorer.compute(reports)
        assert result["total"] > 0
        assert result["grade"] in {"A", "B", "C", "D", "F"}

    def test_top_offenders(self):
        scorer = DebtScorer()
        reports = [
            DebtReport("a.py", "smell", "high", "x", 1, "msg", 1),
            DebtReport("a.py", "smell", "high", "y", 2, "msg", 2),
            DebtReport("b.py", "smell", "low", "z", 3, "msg", 3),
        ]
        result = scorer.compute(reports)
        assert result["top_offenders"][0]["file"] == "a.py"

    def test_grade_boundaries(self):
        scorer = DebtScorer()
        assert scorer._grade(5) == "A"
        assert scorer._grade(15) == "B"
        assert scorer._grade(30) == "C"
        assert scorer._grade(55) == "D"
        assert scorer._grade(80) == "F"


# ── CostTracker ──────────────────────────────────────────────────────


class TestCostTracker:
    def test_track_llm_call(self):
        ct = CostTracker()
        cost = ct.track_llm_call("gpt-3.5-turbo", 1000, 500)
        assert cost.service == "gpt-3.5-turbo"
        assert cost.amount > 0
        assert cost.unit == "USD"

    def test_track_infra(self):
        ct = CostTracker()
        cost = ct.track_infra("ec2", 10, "t3.micro")
        assert cost.service == "ec2:t3.micro"
        assert cost.amount > 0

    def test_get_total(self):
        ct = CostTracker()
        ct.track_llm_call("gpt-3.5-turbo", 1000, 500)
        ct.track_infra("ec2", 10, "t3.micro")
        assert ct.get_total() > 0

    def test_get_breakdown(self):
        ct = CostTracker()
        ct.track_llm_call("gpt-3.5-turbo", 1000, 500)
        ct.track_llm_call("gpt-3.5-turbo", 2000, 1000)
        ct.track_infra("ec2", 1, "t3.small")
        bd = ct.get_breakdown()
        assert "gpt-3.5-turbo" in bd
        assert "ec2:t3.small" in bd
        assert bd["gpt-3.5-turbo"]["count"] == 2

    def test_save_and_load_baseline(self, tmp_path):
        ct = CostTracker()
        ct.track_llm_call("gpt-3.5-turbo", 1000, 500)
        path = tmp_path / "baseline.yaml"
        ct.save_baseline(path)
        assert path.exists()
        loaded = ct.load_baseline(path)
        assert loaded["total"] > 0
        assert "gpt-3.5-turbo" in loaded["breakdown"]

    def test_custom_pricing(self, tmp_path):
        pricing = {"my-model": {"input": 0.1, "output": 0.2}}
        path = tmp_path / "pricing.yaml"
        path.write_text("my-model:\n  input: 0.1\n  output: 0.2\n")
        ct = CostTracker(str(path))
        cost = ct.track_llm_call("my-model", 1000, 500)
        assert cost.amount == pytest.approx(0.2)


# ── Trends ───────────────────────────────────────────────────────────


class TestTrends:
    def test_save_snapshot(self, tmp_path):
        ta = TrendAnalyzer(snapshot_dir=tmp_path)
        reports = [
            DebtReport("a.py", "smell", "low", "x", 1, "msg", 1),
        ]
        snap = ta.save_snapshot(reports, "v1")
        assert snap.exists()

    def test_compare(self, tmp_path):
        ta = TrendAnalyzer(snapshot_dir=tmp_path)
        baseline = [
            DebtReport("a.py", "smell", "low", "x", 1, "msg", 1),
        ]
        snap = ta.save_snapshot(baseline, "v1")
        current = [
            DebtReport("a.py", "smell", "low", "x", 1, "msg", 1),
            DebtReport("b.py", "smell", "high", "y", 2, "msg", 2),
        ]
        delta = ta.compare(current, snap)
        assert delta["new"] == 1
        assert delta["resolved"] == 0
        assert delta["unchanged"] == 1

    def test_compare_resolved(self, tmp_path):
        ta = TrendAnalyzer(snapshot_dir=tmp_path)
        baseline = [
            DebtReport("a.py", "smell", "low", "x", 1, "msg", 1),
        ]
        snap = ta.save_snapshot(baseline, "v1")
        current = []
        delta = ta.compare(current, snap)
        assert delta["resolved"] == 1


# ── DebtReport ───────────────────────────────────────────────────────


class TestDebtReport:
    def test_to_dict(self):
        r = DebtReport("f.py", "cat", "high", "metric", 42, "msg", 3, {"extra": 1})
        d = r.to_dict()
        assert d["file"] == "f.py"
        assert d["value"] == 42
        assert d["meta"] == {"extra": 1}


# ── End-to-end ───────────────────────────────────────────────────────


class TestEndToEnd:
    def test_full_pipeline(self, tmp_path):
        code = """
def complex(x):
    if x > 0:
        if x < 10:
            for i in range(x):
                if i % 2 == 0:
                    while i < 5:
                        i += 1
            return 1
        else:
            return 2
    return 0
"""
        write_code(tmp_path, "main.py", code)
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        score = analyzer.debt_score(reports)
        assert score["total"] >= 0
        assert score["grade"] in {"A", "B", "C", "D", "F"}
        assert "breakdown" in score
        assert "top_offenders" in score

    def test_cost_tracker_pipeline(self, tmp_path):
        ct = CostTracker()
        ct.track_llm_call("gpt-3.5-turbo", 2000, 1000)
        ct.track_infra("ec2", 24, "t3.medium")
        assert ct.get_total() > 0
        path = tmp_path / "cost.yaml"
        ct.save_baseline(path)
        loaded = ct.load_baseline(path)
        assert loaded["total"] == ct.get_total()

    def test_analyzer_thresholds_override(self, tmp_path):
        code = """
def small(x):
    if x:
        return 1
    return 0
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer(thresholds={"cyclomatic": 1})
        reports = analyzer.analyze(tmp_path)
        assert any(r.metric == "cyclomatic" for r in reports)

    def test_circular_import(self, tmp_path):
        write_code(tmp_path, "a.py", "from b import foo\n")
        write_code(tmp_path, "b.py", "from a import bar\n")
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        circ = [r for r in reports if r.metric == "circular_import"]
        assert len(circ) >= 1

    def test_dead_code_unused(self, tmp_path):
        code = """
def unused_func():
    pass

x = 1
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        dead = [r for r in reports if r.metric == "unused_definition"]
        assert len(dead) >= 1

    def test_high_fan_in(self, tmp_path):
        for i in range(25):
            write_code(tmp_path, f"mod_{i}.py", f"import target\n")
        write_code(tmp_path, "target.py", "x = 1\n")
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(tmp_path)
        fan = [r for r in reports if r.metric == "fan_in"]
        assert len(fan) >= 1

    def test_debt_score_breakdown_categories(self, tmp_path):
        code = """
def big(x):
    if x:
        if x > 1:
            if x > 2:
                if x > 3:
                    if x > 4:
                        pass
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer(thresholds={"deep_nesting": 2})
        reports = analyzer.analyze(tmp_path)
        score = analyzer.debt_score(reports)
        assert "smell" in score["breakdown"] or "complexity" in score["breakdown"]

    def test_analyze_str_path(self, tmp_path):
        write_code(tmp_path, "main.py", "x = 1\n")
        analyzer = ComplexityAnalyzer()
        reports = analyzer.analyze(str(tmp_path))
        assert isinstance(reports, list)

    def test_halstead_difficulty(self, tmp_path):
        code = """
def calc(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t):
    return (a + b) * (c - d) / (e + f) + (g - h) * (i + j) * (k + l) / (m + n) + (o + p) * (q - r) / (s + t)
"""
        write_code(tmp_path, "test.py", code)
        analyzer = ComplexityAnalyzer(thresholds={"halstead_difficulty": 1})
        reports = analyzer.analyze(tmp_path)
        diff = [r for r in reports if r.metric == "halstead_difficulty"]
        assert len(diff) >= 1

    def test_trend_multiple_snapshots(self, tmp_path):
        ta = TrendAnalyzer(snapshot_dir=tmp_path)
        r1 = [DebtReport("a.py", "smell", "low", "x", 1, "msg", 1)]
        r2 = [DebtReport("a.py", "smell", "low", "x", 1, "msg", 1), DebtReport("b.py", "smell", "low", "y", 2, "msg", 2)]
        s1 = ta.save_snapshot(r1, "v1")
        delta = ta.compare(r2, s1)
        assert delta["new"] == 1

    def test_cost_tracker_default_pricing(self):
        ct = CostTracker()
        cost = ct.track_llm_call("default", 1000, 1000)
        assert cost.amount == pytest.approx(0.003)

    def test_report_meta(self):
        r = DebtReport("f.py", "cat", "high", "m", 1, "msg", 1, {"foo": "bar"})
        d = r.to_dict()
        assert d["meta"]["foo"] == "bar"
