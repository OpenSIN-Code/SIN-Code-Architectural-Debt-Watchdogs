# circuit_breaker.py

Circuit breaker for capping agent-loop cost / iteration / debt drift.

## What it does

A small kill-switch that any long-running agent loop can poll to
detect runaway behavior. Three limits are enforced:

- `max_iterations` — the agent has run too many ticks.
- `max_cost_usd` — the LLM spend on this run has exceeded a budget.
- `max_debt_increase` — the codebase debt score has climbed too far.

`guard()` wraps a callable and converts a `BreakerTripped` exception
into a `{"aborted": True, "reason": "..."}` dict so the caller can
return gracefully.

## Dependencies

- (none — pure data)

## Public API

| Symbol | Purpose |
|--------|---------|
| `BreakerTripped` | Exception raised on threshold breach |
| `BreakerConfig` | Dataclass for thresholds |
| `CircuitBreaker` | The stateful breaker |
| `CircuitBreaker.check(...)` | Raise if a limit is breached |
| `CircuitBreaker.reset(...)` | Start a new run with new baselines |
| `CircuitBreaker.guard(fn, cost_fn, debt_fn)` | Run `fn` and catch the trip |

## Usage

```python
from sin_code_adw.circuit_breaker import BreakerConfig, CircuitBreaker

breaker = CircuitBreaker(BreakerConfig(max_iterations=10, max_cost_usd=2.0))
for i in range(100):
    breaker.check(iteration=i, current_cost=0.05 * i)
    # ... do work ...
```

## Known caveats

- `check()` does not itself consume a cost budget; the caller must
  call it after every tick with the current totals.
- `BreakerConfig` defaults are tuned for a single short session —
  override for long-running jobs.
- `guard()` swallows `BreakerTripped` and returns a dict; if `fn`
  raises any other exception it still propagates.
