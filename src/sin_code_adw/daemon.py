"""Background-Daemon, der alle Watchdogs vereint."""
from __future__ import annotations

import json
import time
import threading
from pathlib import Path

from .complexity import ComplexityAnalyzer
from .cost_tracker import CostTracker
from .circuit_breaker import CircuitBreaker, BreakerConfig


class WatchdogDaemonmon:
    """Läuft im Hintergrund und eskaliert bei Problemen."""

    def __init__(self, repo_root: str = ".", poll_interval: int = 30):
        self.repo_root = repo_root
        self.poll_interval = poll_interval
        self.analyzer = ComplexityAnalyzer()
        self.cost = CostTracker()
        self.breaker = CircuitBreaker(BreakerConfig())
        self._running = False
        self.alerts: list[dict] = []

    def start(self):
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False

    def _loop(self):
        baseline = self.analyzer.debt_score(self.analyzer.analyze(self.repo_root))
        baseline_cost = self.cost.total_for()["total_usd"]
        while self._running:
            try:
                reports = self.analyzer.analyze(self.repo_root)
                current = self.analyzer.debt_score(reports)
                total_cost = self.cost.total_for()["total_usd"]
                self.breaker.check(current_cost=total_cost, current_debt=current["score"])
                if current["score"] > baseline["score"] + 20:
                    self._alert("debt_spike", current)
            except Exception as e:
                self._alert("breaker_tripped", {"reason": str(e)})
                break
            time.sleep(self.poll_interval)

    def _alert(self, kind: str, data: dict):
        entry = {"kind": kind, "timestamp": time.time(), "data": data}
        self.alerts.append(entry)
        print(f"[ADW ALERT] {kind}: {json.dumps(data, indent=2)}")
