# `mcp_server.py` — MCP Server for ADW

What this file does: exposes architectural debt analysis tools to AI agents via the Model Context Protocol.

## Dependencies

- Imported by: CLI, external MCP hosts
- Imports: `debt_score` (DebtScore), `complexity` (ComplexityAnalyzer), `smells` (SmellDetector)

## Tools

- `analyze_debt(path=".")` — analyze architectural debt in a codebase path
- `analyze_complexity(path=".")` — analyze code complexity metrics
- `detect_smells(path=".")` — detect code smells in the project

## Usage

```bash
python -m sin_code_adw.mcp_server
```

Requires `pip install -e ".[mcp]"`.

## Notes

Uses `mcp.server.fastmcp.FastMCP` for tool registration.
