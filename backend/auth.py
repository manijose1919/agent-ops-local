"""Optional API-key auth for ingest and analytics.

When ``API_SECRET_KEY`` is empty the API is open (zero-config local use).
When it is set, every ``/api/v1`` route requires ``X-API-Key`` or
``Authorization: Bearer <key>``.
"""
from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status


def api_secret() -> str:
    return os.getenv("API_SECRET_KEY", "").strip()


def require_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    expected = api_secret()
    if not expected:
        return

    candidate = (x_api_key or "").strip()
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()
        if bearer:
            candidate = bearer

    if not candidate or len(candidate) != len(expected) or not secrets.compare_digest(
        candidate, expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
