import types

import pytest

from agentops_local import runtime
from agentops_local.config import Config, set_config
from agentops_local.instrument import anthropic as ant
from agentops_local.instrument import openai as oai
from agentops_local.instrument.base import unwrap_method, wrap_method


class FakeTransport:
    def __init__(self):
        self.items = []

    def enqueue(self, payload):
        self.items.append(payload)

    def shutdown(self, *a, **k):
        pass


def setup_function():
    set_config(Config(task="unit", prices={"gpt-4o": {"input": 2.5, "output": 10.0}}))
    runtime.set_transport(FakeTransport())


def _fake_openai_response():
    usage = types.SimpleNamespace(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    choice = types.SimpleNamespace(message=types.SimpleNamespace(content="hello world"))
    return types.SimpleNamespace(model="gpt-4o", usage=usage, choices=[choice])


# --- pure extractors ---------------------------------------------------------

def test_openai_extract_shape():
    extracted = oai.extract({"messages": [{"role": "user", "content": "hi"}]},
                            _fake_openai_response())
    assert extracted["provider"] == "openai"
    assert extracted["model"] == "gpt-4o"
    assert extracted["response"] == "hello world"
    assert extracted["prompt_tokens"] == 100
    assert extracted["total_tokens"] == 150


def test_anthropic_extract_shape():
    usage = types.SimpleNamespace(input_tokens=200, output_tokens=80)
    resp = types.SimpleNamespace(
        model="claude-opus-4-8", usage=usage,
        content=[types.SimpleNamespace(text="claude "), types.SimpleNamespace(text="reply")],
    )
    extracted = ant.extract({"messages": [{"role": "user", "content": "hi"}]}, resp)
    assert extracted["provider"] == "anthropic"
    assert extracted["prompt_tokens"] == 200
    assert extracted["completion_tokens"] == 80
    assert extracted["total_tokens"] == 280
    assert extracted["response"] == "claude reply"


# --- wrap_method behavior ----------------------------------------------------

class FakeCompletions:
    def create(self, **kwargs):
        return _fake_openai_response()


class RaisingCompletions:
    def create(self, **kwargs):
        raise ValueError("api error")


def test_wrap_records_on_success_and_returns_real_response():
    ft = FakeTransport()
    runtime.set_transport(ft)
    wrap_method(FakeCompletions, "create", oai.extract)
    try:
        resp = FakeCompletions().create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
        assert resp.model == "gpt-4o"                      # real response, untouched
        assert len(ft.items) == 1
        payload = ft.items[0]
        assert payload["task_name"] == "unit"
        assert payload["cost"] == pytest.approx(100 * 2.5 / 1e6 + 50 * 10.0 / 1e6)
    finally:
        unwrap_method(FakeCompletions, "create")


def test_wrap_reraises_and_records_nothing_on_error():
    ft = FakeTransport()
    runtime.set_transport(ft)
    wrap_method(RaisingCompletions, "create", oai.extract)
    try:
        with pytest.raises(ValueError):
            RaisingCompletions().create(model="gpt-4o", messages=[])
        assert ft.items == []                              # success-only logging
    finally:
        unwrap_method(RaisingCompletions, "create")


def test_capture_bug_never_breaks_the_call():
    ft = FakeTransport()
    runtime.set_transport(ft)

    def broken_extract(kwargs, response):
        raise RuntimeError("boom")

    wrap_method(FakeCompletions, "create", broken_extract)
    try:
        resp = FakeCompletions().create(model="gpt-4o", messages=[])
        assert resp.model == "gpt-4o"                      # real response despite bug
        assert ft.items == []
    finally:
        unwrap_method(FakeCompletions, "create")


def test_streaming_calls_are_skipped():
    ft = FakeTransport()
    runtime.set_transport(ft)
    wrap_method(FakeCompletions, "create", oai.extract)
    try:
        FakeCompletions().create(model="gpt-4o", messages=[], stream=True)
        assert ft.items == []
    finally:
        unwrap_method(FakeCompletions, "create")
