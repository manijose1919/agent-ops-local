"""End-to-end: the payload the SDK builds is accepted by the real backend.

Validates the contract between the SDK's extractor/payload pipeline and the
FastAPI ingest schema by POSTing a built payload through a TestClient and
confirming a row lands.
"""
import pathlib
import sys
import types

import pytest

# Make the backend package importable regardless of cwd (repo root == parents[2]).
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def client(tmp_path):
    import os

    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path.as_posix()}/e2e.db"
    # Re-import backend so it binds to the temp database.
    for name in [m for m in sys.modules if m.startswith("backend")]:
        del sys.modules[name]
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


def _fake_openai_response():
    usage = types.SimpleNamespace(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    choice = types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))
    return types.SimpleNamespace(model="gpt-4o", usage=usage, choices=[choice])


def test_sdk_payload_is_accepted_and_stored(client):
    from agentops_local import context, runtime
    from agentops_local.config import Config, set_config
    from agentops_local.instrument import openai as oai

    set_config(Config(task="summarize", environment="prod",
                      prices={"gpt-4o": {"input": 2.5, "output": 10.0}}))

    with context.session("run-e2e"):
        extracted = oai.extract({"messages": [{"role": "user", "content": "hi"}]},
                                _fake_openai_response())
        payload = runtime.build_payload(extracted, latency_ms=123.0)

    resp = client.post("/api/v1/ingest", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["task_name"] == "summarize"
    assert body["session_id"] == "run-e2e"
    assert body["model"] == "gpt-4o"
    assert body["total_tokens"] == 150
    assert body["cost"] == pytest.approx(100 * 2.5 / 1e6 + 50 * 10.0 / 1e6)

    calls = client.get("/api/v1/calls").json()
    assert any(c["task_name"] == "summarize" for c in calls)
