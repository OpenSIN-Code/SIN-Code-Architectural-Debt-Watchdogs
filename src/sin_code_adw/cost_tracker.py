"""Track LLM token costs and infrastructure costs.

Docs: cost_tracker.py.doc.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Cost rounding precision. 6 decimal places = millionths of a cent;
# enough to avoid floating-point drift on tiny costs without
# inflating file size in saved baselines.
_COST_ROUND_DIGITS = 6

# Default hourly rate when the user passes an unknown service +
# instance type. Matches the `default` entry in `INFRA_RATES` so
# the value is consistent regardless of which dict it falls out of.
_INFRA_FALLBACK_RATE = 0.05


@dataclass
class Cost:
    """One cost record.

    Attributes:
        service: The model name (for LLM) or `service:instance` (for infra).
        amount: Cost in `unit` (USD by default).
        unit: Currency or measurement unit.
        meta: Free-form metadata (token counts, hours, etc.).
    """

    service: str
    amount: float
    unit: str
    meta: dict = field(default_factory=dict)


class CostTracker:
    """Track costs for LLM calls and infrastructure usage.

    `pricing_file` is a YAML file with model prices per 1k tokens.
    """

    # Default model pricing. Override via `pricing_file` (YAML) for live rates.
    # Prices are in USD per 1k tokens; the `default` entry is the fallback
    # for any model the user passes that we don't have a specific rate for.
    DEFAULT_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "default": {"input": 0.001, "output": 0.002},
    }

    # Default infra pricing. USD per hour per instance type. The
    # `default` service provides a single catch-all rate; the
    # `default` instance type is used when the service has no
    # specific rate for the requested instance.
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
            "default": _INFRA_FALLBACK_RATE,
        },
    }

    def __init__(self, pricing_file: str | None = None):
        """Initialize the tracker.

        Args:
            pricing_file: Optional path to a YAML file with model
                prices. Missing keys fall back to `DEFAULT_PRICING`.
        """
        self._pricing: dict[str, Any] = {}
        if pricing_file:
            path = Path(pricing_file)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._pricing = yaml.safe_load(f) or {}
        # `setdefault` means: for any key the user didn't override, use
        # the built-in default rate. This is non-destructive — the
        # user's overrides always win.
        for k, v in self.DEFAULT_PRICING.items():
            self._pricing.setdefault(k, v)
        self._costs: list[Cost] = []

    # ── Public API ──────────────────────────────────────────────────────

    def track_llm_call(self, model: str, input_tokens: int, output_tokens: int) -> Cost:
        """Record cost for an LLM call.

        Args:
            model: Model name. Falls back to `pricing["default"]` if unknown.
            input_tokens: Prompt token count.
            output_tokens: Completion token count.

        Returns:
            The `Cost` record that was appended to the tracker's history.
        """
        rates = self._pricing.get(model, self._pricing.get("default", self.DEFAULT_PRICING["default"]))
        # Pricing is per 1k tokens; divide tokens by 1000 first.
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        total = input_cost + output_cost
        cost = Cost(
            service=model,
            amount=round(total, _COST_ROUND_DIGITS),
            unit="USD",
            meta={"input_tokens": input_tokens, "output_tokens": output_tokens},
        )
        self._costs.append(cost)
        return cost

    def track_infra(self, service: str, hours: float, instance_type: str) -> Cost:
        """Record infrastructure cost for `hours` on `instance_type`.

        Args:
            service: Cloud provider key (`ec2`, `gcp`, ...). Falls
                back to `INFRA_RATES["default"]` if unknown.
            hours: Usage in hours.
            instance_type: Instance type. Falls back to the service's
                `default` rate if unknown.

        Returns:
            The `Cost` record that was appended to the tracker's history.
        """
        rates = self.INFRA_RATES.get(service, self.INFRA_RATES["default"])
        hourly = rates.get(instance_type, rates.get("default", _INFRA_FALLBACK_RATE))
        total = hourly * hours
        cost = Cost(
            # Use `service:instance_type` as the breakdown key so the
            # report can show per-instance totals.
            service=f"{service}:{instance_type}",
            amount=round(total, _COST_ROUND_DIGITS),
            unit="USD",
            meta={"hours": hours},
        )
        self._costs.append(cost)
        return cost

    def get_total(self) -> float:
        """Sum of all tracked costs (in USD)."""
        return round(sum(c.amount for c in self._costs), _COST_ROUND_DIGITS)

    def get_breakdown(self) -> dict[str, Any]:
        """Return costs grouped by service.

        Each value has `count` and `total` keys, both rounded.
        """
        breakdown: dict[str, list[float]] = {}
        for c in self._costs:
            breakdown.setdefault(c.service, []).append(c.amount)
        return {
            service: {"count": len(amounts), "total": round(sum(amounts), _COST_ROUND_DIGITS)}
            for service, amounts in breakdown.items()
        }

    def save_baseline(self, path: Path) -> None:
        """Serialize current state to YAML.

        Includes total, breakdown, and the full per-record list.
        """
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
        """Load a previously saved baseline. Returns `{}` for empty/missing files."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
