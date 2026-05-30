# SIN-Code Architectural Debt Watchdogs (ADW)

The Meta-Guardian. Watches all other tools, code complexity, and agent costs. Circuit breaker for agents.

## Features
- Cyclomatic complexity and maintainability analysis (radon)
- API cost tracking with model-specific pricing
- Circuit breaker for agent loops (iterations, cost, debt)
- Background watchdog daemon with alerts
- CLI for human monitoring

## Install
```bash
pip install -e .
```

## Usage
```bash
adw scan .                              # scan current repo
adw watch . --interval 30               # run daemon
adw record gpt-4o 1000 500 my-agent     # record cost
adw costs --agent my-agent              # show costs
```

## Architecture
- `ComplexityAnalyzer`: Radon-based code metrics
- `CostTracker`: Persistent JSONL cost logging
- `CircuitBreaker`: Configurable limits with automatic tripping
- `WatchdogDaemonmon`: Background polling with alerts
