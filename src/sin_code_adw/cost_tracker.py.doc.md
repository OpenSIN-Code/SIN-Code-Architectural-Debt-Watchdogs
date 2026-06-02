# cost_tracker.py

What: Tracks LLM API costs and infrastructure costs, supports YAML baselines.

Dependencies: `pyyaml` (for save/load baselines), no internal code deps.

Config: `pricing_file` YAML with model rates per 1k tokens. Defaults are baked in.

Usage:
```python
ct = CostTracker()
ct.track_llm_call("gpt-4", 2000, 500)
ct.track_infra("ec2", 10, "t3.medium")
print(ct.get_total())
ct.save_baseline(Path("costs.yaml"))
```

Caveats:
- Infrastructure rates are US-East approximate; update YAML for your region.
- Default pricing assumes USD.
