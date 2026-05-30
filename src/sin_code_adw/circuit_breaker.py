"""Circuit Breaker für Agent-Loops."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


class BreakerTripped(Exception):
    """Ausnahme wenn ein Limit überschritten wird."""
    pass


@dataclass
class BreakerConfig:
    max_cost_usd: float = 5.0
    max_iterations: int = 20
    max_debt_increase: float = 20.0  # complexity points
    cooldown_seconds: int = 300


class CircuitBreaker:
    """Bricht Agent-Runs ab, wenn Schwellen überschritten werden."""

    def __init__(self, config: BreakerConfig | None = None):
        self.config = config or BreakerConfig()
        self._iterations = 0
        self._start_cost = 0.0
        self._start_debt = 0.0

    def check(self, current_cost: float = 0.0, current_debt: float = 0.0, iteration: int | None = None) -> None:
        if iteration is not None:
            self._iterations = iteration
        if self._iterations >= self.config.max_iterations:
            raise BreakerTripped(f"Max iterations {self.config.max_iterations} reached")
        if current_cost - self._start_cost >= self.config.max_cost_usd:
            raise BreakerTripped(f"Cost limit ${self.config.max_cost_usd} exceeded")
        if current_debt - self._start_debt >= self.config.max_debt_increase:
            raise BreakerTripped(f"Debt increased by {self.config.max_debt_increase} points")

    def reset(self, start_cost: float = 0.0, start_debt: float = 0.0):
        self._iterations = 0
        self._start_cost = start_cost
        self._start_debt = start_debt

    def guard(self, fn: Callable[[], Any], cost_fn: Callable[[], float], debt_fn: Callable[[], float]) -> Any:
        """Wrapper, der fn() ausführt und vor jeder Iteration checkt."""
        self.reset(cost_fn(), debt_fn())
        try:
            return fn()
        except BreakerTripped as e:
            return {"aborted": True, "reason": str(e)}
