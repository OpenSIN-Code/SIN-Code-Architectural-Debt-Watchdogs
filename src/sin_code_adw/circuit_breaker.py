"""Circuit Breaker for agent loops.

Docs: circuit_breaker.py.doc.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


# Default thresholds. Tuned for a single short agent session
# (5 USD spend, 20 ticks, +20 debt-score drift). Override for long jobs.
_DEFAULT_MAX_COST_USD = 5.0
_DEFAULT_MAX_ITERATIONS = 20
_DEFAULT_MAX_DEBT_INCREASE = 20.0
_DEFAULT_COOLDOWN_SECONDS = 300


class BreakerTripped(Exception):
    """Raised when any threshold in `BreakerConfig` is exceeded."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class BreakerConfig:
    """Threshold configuration for `CircuitBreaker`.

    All defaults are conservative for a single short session.
    """

    max_cost_usd: float = _DEFAULT_MAX_COST_USD
    max_iterations: int = _DEFAULT_MAX_ITERATIONS
    max_debt_increase: float = _DEFAULT_MAX_DEBT_INCREASE
    cooldown_seconds: int = _DEFAULT_COOLDOWN_SECONDS


class CircuitBreaker:
    """Halts agent runs when cost, iteration, or debt thresholds are breached.

    State is per-instance: track the iteration count and starting
    cost/debt, then call `check()` after every tick.
    """

    def __init__(self, config: BreakerConfig | None = None):
        """Initialize the breaker.

        Args:
            config: Threshold config. Defaults to `BreakerConfig()`.
        """
        self.config = config or BreakerConfig()
        self._iterations = 0
        self._start_cost = 0.0
        self._start_debt = 0.0

    def check(
        self,
        current_cost: float = 0.0,
        current_debt: float = 0.0,
        iteration: int | None = None,
    ) -> None:
        """Verify the run is still within budget. Raises if not.

        Args:
            current_cost: Total cost spent so far on this run.
            current_debt: Current total debt score.
            iteration: Iteration counter; if provided, overrides the
                breaker's internal counter. Pass it on every tick to
                stay in sync with the agent loop's own counter.

        Raises:
            BreakerTripped: If any threshold is exceeded.
        """
        if iteration is not None:
            self._iterations = iteration
        if self._iterations >= self.config.max_iterations:
            raise BreakerTripped(
                f"Max iterations {self.config.max_iterations} reached"
            )
        # Compare against the *delta* from the run start, not the absolute
        # value — otherwise a session that starts mid-flight would always trip.
        if current_cost - self._start_cost >= self.config.max_cost_usd:
            raise BreakerTripped(
                f"Cost limit ${self.config.max_cost_usd} exceeded"
            )
        if current_debt - self._start_debt >= self.config.max_debt_increase:
            raise BreakerTripped(
                f"Debt increased by {self.config.max_debt_increase} points"
            )

    def reset(self, start_cost: float = 0.0, start_debt: float = 0.0) -> None:
        """Reset state for a new run.

        Args:
            start_cost: Cost baseline (e.g. spend at run start).
            start_debt: Debt-score baseline.
        """
        self._iterations = 0
        self._start_cost = start_cost
        self._start_debt = start_debt

    def guard(
        self,
        fn: Callable[[], Any],
        cost_fn: Callable[[], float],
        debt_fn: Callable[[], float],
    ) -> Any:
        """Run `fn()` and convert a `BreakerTripped` into a graceful dict.

        Args:
            fn: The callable to run.
            cost_fn: Callable returning the current cost (used for reset).
            debt_fn: Callable returning the current debt (used for reset).

        Returns:
            The result of `fn()` on success, or
            `{"aborted": True, "reason": "..."}` on a trip.
        """
        # Reset baselines from the up-to-date callables so the deltas
        # `check()` measures start at zero.
        self.reset(cost_fn(), debt_fn())
        try:
            return fn()
        except BreakerTripped as exc:
            return {"aborted": True, "reason": str(exc)}
