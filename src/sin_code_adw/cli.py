"""CLI for the Architectural Debt Watchdog.

Docs: cli.py.doc.md
"""
from __future__ import annotations

import json
from typing import Optional

import typer

from .complexity import ComplexityAnalyzer
from .cost_tracker import CostTracker
from .daemon import WatchdogDaemon

app = typer.Typer(help="SIN-Code Architectural Debt Watchdog CLI")

# Directories the scanner always skips. Mirrors `WatchdogDaemon.DEFAULT_EXCLUDE`
# so the one-shot `scan` and the background `watch` see the same project shape.
_EXCLUDE = {"venv", ".venv", "node_modules", ".git", "__pycache__"}

# Number of hotspots shown in the `scan` output. Truncated for readability.
_TOP_HOTSPOTS = 10

# Default `watch` poll interval in seconds. 30s is a reasonable
# tradeoff between responsiveness and CPU usage on a quiet repo.
_DEFAULT_WATCH_INTERVAL = 30


@app.command()
def scan(root: str = "."):
    """Scan repository for architectural debt.

    Prints JSON with `debt`, `files_scanned`, and the top
    `_TOP_HOTSPOTS` hotspots.
    """
    analyzer = ComplexityAnalyzer()
    reports = analyzer.analyze(root, exclude=_EXCLUDE)
    debt = analyzer.debt_score(reports)
    hotspots: list[dict] = []
    for r in reports:
        for h in r.hotspots:
            hotspots.append({"file": r.path, **h})
    typer.echo(
        json.dumps(
            {
                "debt": debt,
                "files_scanned": len(reports),
                "top_hotspots": sorted(
                    hotspots, key=lambda x: -x["complexity"]
                )[:_TOP_HOTSPOTS],
            },
            indent=2,
        )
    )


@app.command()
def costs(agent: Optional[str] = None, task: Optional[str] = None):
    """Show tracked costs (optionally filtered by agent and/or task)."""
    tracker = CostTracker()
    typer.echo(json.dumps(tracker.total_for(agent, task), indent=2))


@app.command()
def record(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    agent: str = "default",
    task: str = "",
):
    """Record a cost entry.

    Use this from a hook or wrapper around your LLM client to feed the
    cost tracker one row at a time.
    """
    tracker = CostTracker()
    entry = tracker.record(model, prompt_tokens, completion_tokens, agent, task)
    typer.echo(json.dumps(entry.__dict__, indent=2))


@app.command()
def watch(root: str = ".", interval: int = _DEFAULT_WATCH_INTERVAL):
    """Run the watchdog daemon in the foreground.

    Blocks the process; press Ctrl+C to stop. Use systemd / a process
    supervisor in production.
    """
    wd = WatchdogDaemon(root, interval)
    wd.start()
    typer.echo(f"[ADW] Watchdog started on {root}. Press Ctrl+C to stop.")
    try:
        import time

        # 1-second sleep granularity keeps Ctrl+C latency low without
        # spinning the CPU. The daemon's own `poll_interval` is what
        # controls how often the analyzer re-runs.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wd.stop()


if __name__ == "__main__":
    app()
