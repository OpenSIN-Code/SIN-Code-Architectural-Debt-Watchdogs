"""Trackt API-Kosten von Agent-Runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# Grobe Pricing (USD pro 1K tokens) - Stand 2026
PRICING = {
    "gpt-4o": {"in": 0.0025, "out": 0.01},
    "o3": {"in": 0.002, "out": 0.008},
    "claude-4-opus": {"in": 0.015, "out": 0.075},
    "claude-3.5-sonnet": {"in": 0.003, "out": 0.015},
    "gemini-2.5-pro": {"in": 0.00125, "out": 0.005},
}


@dataclass
class CostEntry:
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    agent_id: str
    task: str


class CostTracker:
    """Persistente Kosten-Verfolgung pro Agent-Task."""

    def __init__(self, log_path: str = ".sin/costs.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, model: str, prompt_tokens: int, completion_tokens: int,
               agent_id: str = "default", task: str = "") -> CostEntry:
        p = PRICING.get(model, {"in": 0.005, "out": 0.015})
        cost = (prompt_tokens / 1000) * p["in"] + (completion_tokens / 1000) * p["out"]
        entry = CostEntry(
            timestamp=datetime.utcnow().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=round(cost, 6),
            agent_id=agent_id,
            task=task,
        )
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry.__dict__) + "\n")
        return entry

    def total_for(self, agent_id: str | None = None, task: str | None = None) -> dict:
        total = 0.0
        entries = 0
        if not self.log_path.exists():
            return {"total_usd": 0, "entries": 0}
        with open(self.log_path) as f:
            for line in f:
                e = json.loads(line)
                if agent_id and e.get("agent_id") != agent_id:
                    continue
                if task and e.get("task") != task:
                    continue
                total += e.get("cost_usd", 0)
                entries += 1
        return {"total_usd": round(total, 4), "entries": entries}
