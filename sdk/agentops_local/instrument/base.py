"""Provider-agnostic monkeypatch machinery.

``wrap_method`` replaces a bound provider method (e.g. ``Completions.create``)
with a wrapper that:

1. Calls the original **untouched** and captures its return value.
2. On success, extracts a payload and records it — inside a ``try/except`` so a
   capture bug can never break the caller.
3. Returns the original response unchanged.

If the original call raises, the wrapper re-raises it and records nothing
(success-only logging, per design).
"""
from __future__ import annotations

import functools
import logging
import time
from typing import Callable

from ..runtime import record

logger = logging.getLogger("agentops_local")


def wrap_method(cls, method_name: str, extractor: Callable[[dict, object], dict]) -> None:
    """Monkeypatch ``cls.method_name`` to capture telemetry after each call."""
    original = getattr(cls, method_name)
    if getattr(original, "_agentops_patched", False):
        return  # already patched — idempotent

    @functools.wraps(original)
    def wrapper(self, *args, **kwargs):
        start = time.perf_counter()
        response = original(self, *args, **kwargs)  # real call — never wrapped
        try:
            # Streaming responses don't expose usage reliably; skip capture (v1).
            if not kwargs.get("stream"):
                latency_ms = (time.perf_counter() - start) * 1000.0
                record(extractor(kwargs, response), latency_ms)
        except Exception:
            logger.debug("agentops_local: telemetry capture failed", exc_info=True)
        return response

    wrapper._agentops_patched = True  # type: ignore[attr-defined]
    wrapper._agentops_original = original  # type: ignore[attr-defined]
    setattr(cls, method_name, wrapper)


def unwrap_method(cls, method_name: str) -> None:
    """Restore the original method if we patched it."""
    fn = getattr(cls, method_name, None)
    if fn is not None and getattr(fn, "_agentops_patched", False):
        setattr(cls, method_name, fn._agentops_original)
