"""Auto-instrumentation for supported LLM providers."""
from __future__ import annotations

from . import anthropic, openai


def patch_all() -> list:
    """Patch every provider whose SDK is importable. Returns the ones patched."""
    patched = []
    if openai.patch():
        patched.append("openai")
    if anthropic.patch():
        patched.append("anthropic")
    return patched


def unpatch_all() -> None:
    openai.unpatch()
    anthropic.unpatch()
