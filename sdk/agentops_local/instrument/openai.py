"""OpenAI auto-instrumentation.

Patches ``openai.resources.chat.completions.Completions.create``. The
``extract`` function is pure and provider-shape-specific, so it can be unit
tested against a hand-built fake response with no ``openai`` install.
"""
from __future__ import annotations

from .base import unwrap_method, wrap_method


def _text(response) -> str:
    """Pull assistant text out of a chat.completions response."""
    try:
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        if message is not None:
            return getattr(message, "content", None) or ""
        return getattr(choice, "text", "") or ""  # legacy completions shape
    except Exception:
        return ""


def extract(kwargs: dict, response) -> dict:
    """Map (call kwargs, response) -> provider-agnostic extracted dict."""
    usage = getattr(response, "usage", None)
    return {
        "provider": "openai",
        "model": getattr(response, "model", None) or kwargs.get("model"),
        "prompt": kwargs.get("messages") or kwargs.get("input") or kwargs.get("prompt"),
        "response": _text(response),
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
        "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
    }


def patch() -> bool:
    """Instrument the OpenAI SDK if it's importable. Returns whether it patched."""
    try:
        from openai.resources.chat.completions import Completions
    except Exception:
        return False
    wrap_method(Completions, "create", extract)
    return True


def unpatch() -> None:
    try:
        from openai.resources.chat.completions import Completions
    except Exception:
        return
    unwrap_method(Completions, "create")
