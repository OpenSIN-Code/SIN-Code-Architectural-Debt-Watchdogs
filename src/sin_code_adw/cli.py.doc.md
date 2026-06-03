# cli.py

Typer-based CLI for the Architectural Debt Watchdog.

## What it does

Four subcommands:

- `scan` — one-shot analysis of a repo: total debt, files scanned, top hotspots.
- `costs` — show tracked costs (optionally filtered by agent/task).
- `record` — manually add a cost entry.
- `watch` — start the `WatchdogDaemon` polling loop.

## Dependencies

- `complexity.py` — `ComplexityAnalyzer`
- `cost_tracker.py` — `CostTracker`
- `daemon.py` — `WatchdogDaemon`

## Excluded directories

By default the scanner skips: `venv`, `.venv`, `node_modules`, `.git`,
`__pycache__`. Hard-coded in the module; not configurable from the
CLI today.

## Usage

```bash
sin-adw scan .
sin-adw costs --agent scout
sin-adw record gpt-4 1234 567 --task refactor
sin-adw watch . --interval 60
```

## Known caveats

- `watch` blocks the foreground process; run it under systemd / a
  process supervisor in production.
- `record` is the only command that requires a token count; all
  others read the in-memory tracker (which is process-local and
  does not persist across invocations).
