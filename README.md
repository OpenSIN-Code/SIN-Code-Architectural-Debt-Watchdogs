# SIN-Code Architectural Debt Watchdogs (ADW)

> Python package for analyzing architectural debt, code smells, and tracking costs. Keeps technical debt visible and measurable.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

Part of the [SIN-Code](https://github.com/OpenSIN-Code) agent-engineering stack. Install all subsystems together via the [SIN-Code Bundle](https://github.com/OpenSIN-Code/SIN-Code-Bundle).

## Features

- **Complexity analysis** — cyclomatic, cognitive, and Halstead metrics per function
- **Code smells** — detect god functions, long files, circular imports, dead code, deep nesting
- **Debt scoring** — aggregate findings into a single score with grade and top offenders
- **Cost tracking** — record LLM token costs and infrastructure costs with breakdowns
- **Watchdog daemon** — continuous monitoring with configurable intervals
- **MCP server** — expose debt analysis tools to AI agents via the Model Context Protocol

## Installation

```bash
pip install -e .
```

Optional MCP server support:
```bash
pip install -e ".[mcp]"
```

See [INSTALL.md](./INSTALL.md) for detailed setup instructions.

## Usage

### Library

```python
from sin_code_adw import ComplexityAnalyzer, CostTracker

# Analyze complexity and smells
analyzer = ComplexityAnalyzer()
reports = analyzer.analyze(".", exclude={"node_modules", ".venv", ".git"})
baseline = analyzer.debt_score(reports)
print(baseline)
# {'total': 42.5, 'breakdown': {...}, 'top_offenders': [...], 'grade': 'C'}

# Track costs
tracker = CostTracker()
tracker.track_llm_call("gpt-4", input_tokens=1000, output_tokens=500)
tracker.track_infra("ec2", hours=2.5, instance_type="t3.medium")
print(tracker.get_total())       # 0.142
print(tracker.get_breakdown())   # {'gpt-4': {...}, 'ec2:t3.medium': {...}}
```

### CLI

```bash
# Scan repository for debt
adw scan

# Show tracked costs
adw costs

# Record a cost entry
adw record gpt-4 1000 500 --agent claude --task refactor

# Run watchdog daemon
adw watch --interval 60
```

## Testing

```bash
pytest tests/ -v
```

## MCP Server

Run the MCP server for agent integration:

```bash
python -m sin_code_adw.mcp_server
```

Tools exposed:
- `analyze_debt(path=".")` — analyze architectural debt in a codebase path
- `analyze_complexity(path=".")` — analyze code complexity metrics
- `detect_smells(path=".")` — detect code smells in the project

## Integration

ADW is designed to work as part of the SIN-Code ecosystem:

- **SIN-Code Bundle** — orchestrates all subsystems from a single CLI (`sin`)
- **Semantic Codebase Knowledge Graphs (SCKG)** — cross-reference debt with graph topology
- **Intent-Based Diffing (IBD)** — flag debt changes in pull requests
- **Orchestration** — run debt scans as scheduled tasks in agent workflows

## License

MIT — see [LICENSE](./LICENSE).
