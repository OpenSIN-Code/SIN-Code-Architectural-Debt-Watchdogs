"""Background daemon that unifies all the watchdogs.

Docs: daemon.py.doc.md
"""
from __future__ import annotations

import json
import threading
import time

from .circuit_breaker import BreakerConfig, BreakerTripped, CircuitBreaker
from .complexity import ComplexityAnalyzer
from .cost_tracker import CostTracker


# Default poll interval (seconds). 30s is a reasonable trade-off
# between responsiveness and CPU on a quiet repo.
_DEFAULT_POLL_INTERVAL = 30

# Debt-score spike threshold: emit a `debt_spike` alert when the
# current score exceeds the baseline by this many points.
_SPIKE_THRESHOLD = 20

# Default exclusion set, mirrored in `cli.py` so the one-shot `scan`
# and the background `watch` see the same project shape.
_DEFAULT_EXCLUDE = {"venv", ".venv", "node_modules", ".git", "__pycache__"}


class WatchdogDaemon:
    """Background watchdog that polls the repo for debt / cost spikes.

    On every tick the daemon re-runs the complexity analyzer, computes
    a fresh debt score, and forwards totals to the circuit breaker.
    """

    DEFAULT_EXCLUDE = _DEFAULT_EXCLUDE

    def __init__(self, repo_root: str = ".", poll_interval: int = _DEFAULT_POLL_INTERVAL):
        """Initialize the daemon.

        Args:
            repo_root: Path to the project to monitor.
            poll_interval: Seconds between polls.
        """
        self.repo_root = repo_root
        self.poll_interval = poll_interval
        self.analyzer = ComplexityAnalyzer()
        self.cost = CostTracker()
        self.breaker = CircuitBreaker(BreakerConfig())
        self._running = False
        self.alerts: list[dict] = []
        self._thread: threading.Thread | None = None

    def start(self) -> threading.Thread:
        """Start the polling thread. Returns the thread object."""
        self._running = True
        # `daemon=True` so the thread doesn't block process exit
        # even if `stop()` is forgotten.
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        """Signal the loop to exit at the next tick. Does not block."""
        self._running = False

    def _loop(self) -> None:
        """Main polling loop. Runs in a daemon thread."""
        # Compute the baseline once at start so we can detect a
        # *relative* debt drift, not just an absolute one.
        baseline = self.analyzer.debt_score(
            self.analyzer.analyze(self.repo_root, exclude=self.DEFAULT_EXCLUDE)
        )
        while self._running:
            try:
                reports = self.analyzer.analyze(
                    self.repo_root, exclude=self.DEFAULT_EXCLUDE
                )
                current = self.analyzer.debt_score(reports)
                total_cost = self.cost.total_for()["total_usd"]
                self.breaker.check(
                    current_cost=total_cost, current_debt=current["score"]
                )
                # Compare against the baseline + threshold; the
                # baseline is captured at start so a quiet pre-existing
                # level of debt doesn't mask a fresh regression.
                if current["score"] > baseline["score"] + _SPIKE_THRESHOLD:
                    self._alert("debt_spike", current)
            except BreakerTripped as exc:
                self._alert("breaker_tripped", {"reason": str(exc)})
                # A trip is fatal — the loop must stop. We could
                # restart after `cooldown_seconds` but the user
                # should fix the underlying issue first.
                break
            except Exception as exc:
                # Catch-all so a single failed tick doesn't kill the loop.
                self._alert("error", {"reason": str(exc)})
            time.sleep(self.poll_interval)

    def _alert(self, kind: str, data: dict) -> None:
        """Record an alert and print it to stdout.

        Args:
            kind: One of `debt_spike`, `breaker_tripped`, `error`.
            data: Free-form payload (debt score, reason string, etc.).
        """
        entry = {"kind": kind, "timestamp": time.time(), "data": data}
        self.alerts.append(entry)
        print(f"[ADW ALERT] {kind}: {json.dumps(data)}")
