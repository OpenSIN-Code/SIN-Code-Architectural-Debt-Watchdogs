"""Track LLM token costs and infrastructure costs.

Docs: cost_tracker.py.doc.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Cost:
    service: str
    amount: float
    unit: str
    meta: dict = field(default_factory=dict)


class CostTracker:
    """Track costs for LLM calls and infrastructure usage.

    *pricing_file* is a YAML file with model prices per 1k tokens.
    """

    DEFAULT_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "default": {"input": 0.001, "output": 0.002},
    }

    INFRA_RATES = {
        "ec2": {
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
        },
        "gcp": {
            "e2-micro": 0.008,
            "e2-small": 0.016,
            "e2-medium": 0.033,
        },
        "default": {
            "default": 0.05,
        },
    }

    def __init__(self, pricing_file: str | None = None):
        self._pricing: dict[str, Any] = {}
        if pricing_file:
            path = Path(pricing_file)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._pricing = yaml.safe_load(f) or {}
        # Fill defaults for missing keys
        for k, v in self.DEFAULT_PRICING.items():
            self._pricing.setdefault(k, v)
        self._costs: list[Cost] = []

    # ── Public API ──────────────────────────────────────────────────────

    def track_llm_call(self, model: str, input_tokens: int, output_tokens: int) -> Cost:
        """Record cost for an LLM call."""
        rates = self._pricing.get(model, self._pricing.get("default", self.DEFAULT_PRICING["default"]))
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        total = input_cost + output_cost
        cost = Cost(
            service=model,
            amount=round(total, 6),
            unit="USD",
            meta={"input_tokens": input_tokens, "output_tokens": output_tokens},
        )
        self._costs.append(cost)
        return cost

    def track_infra(self, service: str, hours: float, instance_type: str) -> Cost:
        """Record infrastructure cost for *hours* on *instance_type*."""
        rates = self.INFRA_RATES.get(service, self.INFRA_RATES["default"])
        hourly = rates.get(instance_type, rates.get("default", 0.05))
        total = hourly * hours
        cost = Cost(
            service=f"{service}:{instance_type}",
            amount=round(total, 6),
            unit="USD",
            meta={"hours": hours},
        )
        self._costs.append(cost)
        return cost

    def get_total(self) -> float:
        """Sum of all tracked costs."""
        return round(sum(c.amount for c in self._costs), 6)

    def get_breakdown(self) -> dict[str, Any]:
        """Return costs grouped by service."""
        breakdown: dict[str, list[float]] = {}
        for c in self._costs:
            breakdown.setdefault(c.service, []).append(c.amount)
        return {
            service: {"count": len(amounts), "total": round(sum(amounts), 6)}
            for service, amounts in breakdown.items()
        }

    def save_baseline(self, path: Path) -> None:
        """Serialize current state to YAML."""
        payload = {
            "total": self.get_total(),
            "breakdown": self.get_breakdown(),
            "costs": [
                {
                    "service": c.service,
                    "amount": c.amount,
                    "unit": c.unit,
                    "meta": c.meta,
                }
                for c in self._costs
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(payload, f, default_flow_style=False)

    def load_baseline(self, path: Path) -> dict[str, Any]:
        """Load a previously saved baseline."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
