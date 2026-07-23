"""Global SDK configuration.

A single module-level ``Config`` instance holds the defaults supplied at
``init()`` time. Everything else in the SDK reads from here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

# Price map shape: {model_name: {"input": usd_per_1M_tokens, "output": usd_per_1M_tokens}}
PriceMap = Dict[str, Dict[str, float]]


@dataclass
class Config:
    """Resolved SDK configuration.

    Attributes mirror the keyword arguments accepted by :func:`agentops_local.init`.
    """

    base_url: str = "http://localhost:8000"
    task: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    environment: str = "dev"
    prices: PriceMap = field(default_factory=dict)
    enabled: bool = True
    timeout: float = 5.0

    @property
    def ingest_url(self) -> str:
        return self.base_url.rstrip("/") + "/api/v1/ingest"

    def is_enabled(self) -> bool:
        """Master kill-switch. ``AGENTOPS_ENABLED=0`` overrides ``enabled=True``."""
        env = os.getenv("AGENTOPS_ENABLED")
        if env is not None:
            return env.strip().lower() not in ("0", "false", "no", "off")
        return self.enabled


# The one global config the SDK reads from. Replaced wholesale by init().
_config = Config()


def get_config() -> Config:
    return _config


def set_config(config: Config) -> None:
    global _config
    _config = config
