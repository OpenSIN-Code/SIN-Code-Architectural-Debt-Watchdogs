from sin_code_adw.complexity import ComplexityAnalyzer


def test_complexity():
    analyzer = ComplexityAnalyzer()
    with open("test_file.py", "w") as f:
        f.write("def foo():\n    pass\n")
    reports = analyzer.analyze(".", exclude={"venv", ".venv"})
    assert any(r.path == "test_file.py" for r in reports)
