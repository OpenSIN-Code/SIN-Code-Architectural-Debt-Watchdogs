# daemon.py

Background watchdog that polls a repo for debt / cost spikes.

## What it does

`WatchdogDaemon` runs in a daemon thread and re-analyzes the repo at
`poll_interval` seconds. On every tick it:

1. Re-runs `ComplexityAnalyzer.analyze` to refresh debt reports.
2. Computes a fresh debt score and total cost.
3. Calls `CircuitBreaker.check` to abort on a runaway.
4. Emits an alert (`debt_spike`, `breaker_tripped`, or `error`) when
   the debt score has climbed more than 20 points above baseline.

## Dependencies

- `complexity.py` — `ComplexityAnalyzer`
- `cost_tracker.py` — `CostTracker`
- `circuit_breaker.py` — `BreakerConfig`, `BreakerTripped`, `CircuitBreaker`

## Public API

| Symbol | Purpose |
|--------|---------|
| `WatchdogDaemon(repo_root, poll_interval)` | Constructor |
| `start()` | Spawn the polling thread |
| `stop()` | Signal the thread to exit |
| `alerts` | List of emitted alerts (in-memory log) |

## Threshold

The `debt_spike` threshold is `+20` points above the baseline
(debt score at daemon start). Tweak the literal in `_loop` to taste.

## Known caveats

- The baseline is computed *once* at start; if the codebase is
  already in a bad state, the baseline is already high and a
  small regression is invisible.
- Alerts are only logged to stdout + kept in `self.alerts`. There
  is no built-in webhook / Slack integration.
- `time.sleep(self.poll_interval)` is uninterruptible except by a
  signal; `stop()` is checked at the top of the next loop iteration.
