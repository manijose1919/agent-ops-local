"""Anthropic auto-instrumentation.

Patches ``anthropic.resources.messages.Messages.create``. Anthropic reports
usage as ``input_tokens`` / ``output_tokens`` and returns content as a list of
blocks, which ``extract`` normalizes to the same shape the OpenAI extractor
produces.
"""
from __future__ import annotations

from .base import unwrap_method, wrap_method


def _text(response) -> str:
    """Concatenate text blocks from a messages response."""
    try:
        parts = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)
    except Exception:
        return ""


def extract(kwargs: dict, response) -> dict:
    """Map (call kwargs, response) -> provider-agnostic extracted dict."""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
    return {
        "provider": "anthropic",
        "model": getattr(response, "model", None) or kwargs.get("model"),
        "prompt": kwargs.get("messages"),
        "response": _text(response),
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def patch() -> bool:
    """Instrument the Anthropic SDK if it's importable. Returns whether it patched."""
    try:
        from anthropic.resources.messages import Messages
    except Exception:
        try:
            from anthropic.resources import Messages  # older layouts
        except Exception:
            return False
    wrap_method(Messages, "create", extract)
    return True


def unpatch() -> None:
    try:
        from anthropic.resources.messages import Messages
    except Exception:
        try:
            from anthropic.resources import Messages
        except Exception:
            return
    unwrap_method(Messages, "create")
