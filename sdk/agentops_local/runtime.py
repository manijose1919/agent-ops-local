"""Runtime glue: turn an extracted call into a backend payload and enqueue it.

Kept separate from ``__init__`` so the instrumentation modules can import the
record path without a circular import back through the public API.
"""
from __future__ import annotations

import logging
from typing import Optional

from .config import get_config
from .context import current_agent, current_session, current_task
from .pricing import compute_cost

logger = logging.getLogger("agentops_local")

# The active transport, set by init(). None means telemetry is inert.
_transport = None


def get_transport():
    return _transport


def set_transport(transport) -> None:
    global _transport
    _transport = transport


def build_payload(extracted: dict, latency_ms: float) -> dict:
    """Map a provider-agnostic ``extracted`` dict to the /ingest request body."""
    cfg = get_config()
    prompt_tokens = extracted.get("prompt_tokens") or 0
    completion_tokens = extracted.get("completion_tokens") or 0
    total_tokens = extracted.get("total_tokens") or (prompt_tokens + completion_tokens)
    model = extracted.get("model") or "unknown"

    return {
        "task_name": current_task() or "unknown",
        "session_id": current_session(),
        "agent_id": current_agent(),
        "environment": cfg.environment,
        "model": model,
        "provider": extracted.get("provider"),
        "prompt": extracted.get("prompt") if extracted.get("prompt") is not None else "",
        "response": extracted.get("response") or "",
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost": compute_cost(model, prompt_tokens, completion_tokens, cfg.prices),
        "latency_ms": latency_ms,
    }


def record(extracted: dict, latency_ms: float) -> None:
    """Build the payload and hand it to the transport. Never raises."""
    if not get_config().is_enabled():
        return
    transport = get_transport()
    if transport is None:
        return
    try:
        transport.enqueue(build_payload(extracted, latency_ms))
    except Exception:  # pragma: no cover - defensive; telemetry must never break the app
        logger.debug("agentops_local: failed to record telemetry", exc_info=True)
