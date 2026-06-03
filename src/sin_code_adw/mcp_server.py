"""MCP server for agent integration.

Docs: mcp_server.py.doc.md
"""
from __future__ import annotations

import json

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    # Soft import so the rest of the package remains usable without
    # the MCP dependency installed; `main()` raises a clear error
    # at runtime instead.
    FastMCP = None

from .debt_score import DebtScore
from .complexity import ComplexityAnalyzer
from .smells.detectors import SmellDetector


# Server identity reported to MCP clients in the initialize handshake.
_SERVER_NAME = "sin-code-adw"


def main():
    """Build the FastMCP server and start it on stdio (blocks).

    Raises:
        RuntimeError: If the optional `mcp` package is not installed.
    """
    if FastMCP is None:
        raise RuntimeError("mcp package not installed. Install with: pip install 'sin-code-adw[mcp]'")

    mcp = FastMCP(_SERVER_NAME)

    @mcp.tool()
    def analyze_debt(path: str = ".") -> str:
        """Analyze architectural debt in a codebase path.

        Args:
            path: Root directory of the codebase to analyze (default: cwd).

        Returns:
            JSON-encoded debt score (total, breakdown, top offenders, grade).
        """
        score = DebtScore.analyze(path)
        return json.dumps(score.to_dict(), indent=2)

    @mcp.tool()
    def analyze_complexity(path: str = ".") -> str:
        """Analyze code complexity metrics.

        Args:
            path: Root directory of the codebase to analyze (default: cwd).

        Returns:
            JSON list of `DebtReport` records (per-function / per-file).
        """
        analyzer = ComplexityAnalyzer()
        return json.dumps(analyzer.analyze(path), indent=2)

    @mcp.tool()
    def detect_smells(path: str = ".") -> str:
        """Detect code smells in the project.

        Args:
            path: Root directory of the codebase to analyze (default: cwd).

        Returns:
            JSON list of smell reports.
        """
        detector = SmellDetector()
        return json.dumps(detector.detect(path), indent=2)

    mcp.run()


if __name__ == "__main__":
    main()
