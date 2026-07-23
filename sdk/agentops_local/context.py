"""Per-block overrides for task / session / agent.

``contextvars`` gives us overrides that are correct under threads and asyncio:
each ``with ao.task(...)`` pushes a value that resolves innermost-first and is
restored on exit. When no override is active, we fall back to the ``init()``
defaults held in :mod:`agentops_local.config`.
"""
from __future__ import annotations

import contextlib
from contextvars import ContextVar
from typing import Iterator, Optional

from .config import get_config

_task_var: ContextVar[Optional[str]] = ContextVar("agentops_task", default=None)
_session_var: ContextVar[Optional[str]] = ContextVar("agentops_session", default=None)
_agent_var: ContextVar[Optional[str]] = ContextVar("agentops_agent", default=None)


def current_task() -> Optional[str]:
    return _task_var.get() or get_config().task


def current_session() -> Optional[str]:
    return _session_var.get() or get_config().session_id


def current_agent() -> Optional[str]:
    return _agent_var.get() or get_config().agent_id


@contextlib.contextmanager
def task(name: str) -> Iterator[None]:
    """Override the task name for all instrumented calls inside this block."""
    token = _task_var.set(name)
    try:
        yield
    finally:
        _task_var.reset(token)


@contextlib.contextmanager
def session(session_id: str) -> Iterator[None]:
    """Group all instrumented calls inside this block into one session trace."""
    token = _session_var.set(session_id)
    try:
        yield
    finally:
        _session_var.reset(token)


@contextlib.contextmanager
def agent(agent_id: str) -> Iterator[None]:
    """Override the agent id for all instrumented calls inside this block."""
    token = _agent_var.set(agent_id)
    try:
        yield
    finally:
        _agent_var.reset(token)
