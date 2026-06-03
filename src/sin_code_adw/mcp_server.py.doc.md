# mcp_server.py

FastMCP server exposing the debt watchdog as MCP tools.

## What it does

Wraps `DebtScore.analyze`, `ComplexityAnalyzer`, and a `SmellDetector`
in a `FastMCP` server. Three tools are exposed over stdio:
`analyze_debt`, `analyze_complexity`, `detect_smells`.

## Dependencies

- `debt_score.py` — `DebtScore`
- `complexity.py` — `ComplexityAnalyzer`
- `smells/detectors.py` — `SmellDetector`
- `mcp.server.fastmcp.FastMCP` — optional; soft import.

## Tools

| Tool | Returns | Description |
|------|---------|-------------|
| `analyze_debt(path=".")` | JSON | Total debt score + breakdown |
| `analyze_complexity(path=".")` | JSON | Per-function complexity metrics |
| `detect_smells(path=".")` | JSON | Per-file smell list |

## Usage

```bash
python -m sin_code_adw.mcp_server
```

In `opencode.json` configure the MCP server; the tools become
available to agents.

## Known caveats

- Requires `pip install 'sin-code-adw[mcp]'` for the `mcp` package;
  otherwise `main()` raises a clear `RuntimeError`.
- Each tool call is synchronous and re-creates its analyzer/detector
  from scratch; there is no caching across calls.
- The `mcp_server` file imports a `SmellDetector` from
  `smells/detectors.py` which is not in this repo's current file
  list — verify the import resolves before running.
