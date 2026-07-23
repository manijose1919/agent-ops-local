"""Cost computation from token counts and a user-supplied price map.

The SDK ships no pricing data of its own (prices go stale fast). The caller
provides ``prices`` at ``init()``; unknown models resolve to cost ``0.0`` and
warn exactly once so logs don't flood.
"""
from __future__ import annotations

import logging
from typing import Optional

from .config import PriceMap

logger = logging.getLogger("agentops_local")

# Models we've already warned about, so the warning fires at most once each.
_warned_models: set = set()


def reset_warnings() -> None:
    """Clear the warn-once memory. Primarily for tests."""
    _warned_models.clear()


def compute_cost(
    model: Optional[str],
    prompt_tokens: int,
    completion_tokens: int,
    prices: PriceMap,
) -> float:
    """Return the USD cost for a call, or ``0.0`` if the model isn't priced.

    ``prices`` maps model name -> ``{"input": usd_per_1M, "output": usd_per_1M}``.
    """
    entry = prices.get(model) if model else None
    if not entry:
        if model and model not in _warned_models:
            _warned_models.add(model)
            logger.warning(
                "agentops_local: no price configured for model %r; recording cost=0. "
                "Add it to the `prices` map passed to init().",
                model,
            )
        return 0.0

    input_rate = entry.get("input", 0.0) / 1_000_000
    output_rate = entry.get("output", 0.0) / 1_000_000
    cost = prompt_tokens * input_rate + completion_tokens * output_rate
    return round(cost, 8)
