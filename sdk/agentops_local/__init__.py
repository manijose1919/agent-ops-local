"""AgentOpsLocal SDK — one-line LLM telemetry for AI agents.

    import agentops_local as ao
    ao.init(task="summarize", prices={"gpt-4o": {"input": 2.5, "output": 10.0}})

    client.chat.completions.create(...)   # captured automatically

See https://github.com/manijose1919/agent-ops-local for the backend + dashboard.
"""
from __future__ import annotations

import atexit
import logging
from typing import Optional

from . import instrument
from .config import Config, PriceMap, set_config
from .context import agent, session, task
from .runtime import get_transport, set_transport
from .transport import Transport

__all__ = ["init", "task", "session", "agent", "shutdown", "Config"]
__version__ = "0.1.0"

logger = logging.getLogger("agentops_local")

_atexit_registered = False


def init(
    base_url: str = "http://localhost:8000",
    task: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    environment: str = "dev",
    prices: Optional[PriceMap] = None,
    enabled: bool = True,
    timeout: float = 5.0,
) -> None:
    """Configure the SDK and auto-instrument installed LLM providers.

    Args:
        base_url: AgentOpsLocal backend URL.
        task: Default task name for captured calls (override with ``ao.task``).
        session_id: Default session id (override with ``ao.session``).
        agent_id: Default agent id (override with ``ao.agent``).
        environment: ``dev`` | ``staging`` | ``prod``.
        prices: ``{model: {"input": usd_per_1M, "output": usd_per_1M}}``. Models
            not listed record ``cost=0`` (with a one-time warning).
        enabled: Master switch. ``AGENTOPS_ENABLED=0`` forces it off.
        timeout: Per-request HTTP timeout for telemetry POSTs, in seconds.
    """
    global _atexit_registered

    config = Config(
        base_url=base_url,
        task=task,
        session_id=session_id,
        agent_id=agent_id,
        environment=environment,
        prices=prices or {},
        enabled=enabled,
        timeout=timeout,
    )
    set_config(config)

    if not config.is_enabled():
        logger.debug("agentops_local: disabled; not instrumenting.")
        return

    # (Re)create the transport pointed at the configured backend.
    existing = get_transport()
    if existing is not None:
        existing.shutdown()
    set_transport(Transport(config.ingest_url, timeout=config.timeout))

    patched = instrument.patch_all()
    logger.debug("agentops_local: instrumented providers: %s", patched or "none")

    if not _atexit_registered:
        atexit.register(shutdown)
        _atexit_registered = True


def shutdown() -> None:
    """Flush pending telemetry, stop the worker thread, and remove patches."""
    transport = get_transport()
    if transport is not None:
        transport.shutdown()
        set_transport(None)
    instrument.unpatch_all()
