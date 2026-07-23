"""Non-blocking, fail-silent telemetry transport.

``enqueue`` never blocks the caller: it drops a payload on an in-memory queue and
returns. A single daemon thread drains the queue and POSTs each payload to the
AgentOpsLocal ``/api/v1/ingest`` endpoint using only the standard library, so the
SDK has zero required third-party dependencies.

Design guarantees:
- **Never blocks the caller** — enqueue is O(1) and returns immediately.
- **Never raises into the caller** — network/serialization errors are swallowed
  and warned about at most once.
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import urllib.error
import urllib.request
from typing import Optional

logger = logging.getLogger("agentops_local")

# Sentinel enqueued by shutdown() to tell the worker thread to exit.
_STOP = object()


class Transport:
    """A background worker that POSTs telemetry payloads to the backend."""

    def __init__(self, ingest_url: str, timeout: float = 5.0, max_queue: int = 10_000):
        self._ingest_url = ingest_url
        self._timeout = timeout
        self._queue: "queue.Queue" = queue.Queue(maxsize=max_queue)
        self._warned = False
        self._dropped = 0
        self._thread = threading.Thread(
            target=self._run, name="agentops-telemetry", daemon=True
        )
        self._thread.start()

    def enqueue(self, payload: dict) -> None:
        """Queue a payload for sending. Non-blocking; drops if the queue is full."""
        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            self._dropped += 1  # backend can't keep up; never block the agent

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is _STOP:
                    return
                self._send(item)
            except Exception:  # pragma: no cover - defensive; _send already guards
                self._warn_once()
            finally:
                self._queue.task_done()

    def _send(self, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._ingest_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                resp.read()  # drain so the connection can be reused/closed cleanly
        except (urllib.error.URLError, OSError, ValueError):
            # Backend down, refused, timed out, or bad URL: drop, warn once.
            self._warn_once()

    def _warn_once(self) -> None:
        if not self._warned:
            self._warned = True
            logger.warning(
                "agentops_local: could not reach the telemetry backend at %s; "
                "dropping telemetry. Is AgentOpsLocal running?",
                self._ingest_url,
            )

    def flush(self, timeout: Optional[float] = None) -> None:
        """Block until all currently-queued payloads have been processed."""
        self._queue.join()

    def shutdown(self, timeout: float = 5.0) -> None:
        """Flush pending payloads and stop the worker thread."""
        self.flush()
        self._queue.put(_STOP)
        self._thread.join(timeout=timeout)
