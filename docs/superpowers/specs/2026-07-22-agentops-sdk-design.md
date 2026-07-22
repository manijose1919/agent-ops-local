# AgentOpsLocal Python SDK — Design

**Date:** 2026-07-22
**Status:** Approved (pending spec review)
**Component:** `agentops-local` Python SDK

## Goal

Ship a pip-installable Python SDK that lets developers capture LLM telemetry
(model, tokens, latency, cost, prompt/response) into the AgentOpsLocal backend
with **one import and one `init()` call** — no changes to existing call sites.
This makes the README's SDK promise real and is the highest-leverage adoption lever.

## Design Decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Integration style | **Auto-instrument** — monkey-patch provider clients; zero call-site changes |
| Providers (v1) | **OpenAI + Anthropic** |
| Transport | **Background thread queue + fail-silent** — never blocks, never raises into caller |
| Cost | **User-supplied price map** at `init()`; unknown model → cost `0` + warn-once |

## Architecture & Package Layout

A new, dependency-light package living alongside the backend, installable independently.

```
agent_ops_local/
  sdk/
    pyproject.toml          # name: agentops-local; extras: [openai], [anthropic]
    agentops_local/
      __init__.py           # public API: init(), task(), session(), shutdown()
      config.py             # global Config (base_url, defaults, prices, enabled)
      context.py            # contextvars stack for per-block task/session/agent
      pricing.py            # cost = f(model, tokens, price_map); unknown -> 0 + warn-once
      transport.py          # background queue + daemon thread -> POST /api/v1/ingest
      instrument/
        openai.py           # patches OpenAI chat.completions.create
        anthropic.py        # patches Anthropic messages.create
```

**Zero required dependencies:** transport uses the standard library
(`urllib.request`, `queue`, `threading`). Provider SDKs are optional extras —
`openai` is only needed if instrumenting OpenAI. This keeps
`pip install agentops-local` featherweight.

**Isolation boundaries:** `pricing` knows nothing about HTTP; `transport` knows
nothing about providers; `instrument/*` knows nothing about the queue internals.
Each module is independently testable.

## Public API & Usage

```python
import agentops_local as ao

ao.init(
    base_url="http://localhost:8000",   # default
    task="summarize_doc",                # default task for all calls
    environment="prod",                  # default env
    agent_id="researcher-1",             # optional
    prices={                             # user-supplied model -> price map ($/1M tokens)
        "gpt-4o":          {"input": 2.50,  "output": 10.00},
        "claude-opus-4-8": {"input": 15.00, "output": 75.00},
    },
    enabled=True,                        # kill-switch (also AGENTOPS_ENABLED env)
)

# existing code — captured automatically, unchanged:
client.chat.completions.create(model="gpt-4o", messages=[...])
```

**Per-block overrides** via context managers:

```python
with ao.session("run-abc123"):          # groups calls into a session trace
    with ao.task("plan_step"):
        client.messages.create(...)     # task="plan_step", session="run-abc123"
    with ao.task("execute_step"):
        client.chat.completions.create(...)
```

`ao.shutdown()` flushes the queue and joins the background thread; also registered
via `atexit` so short scripts flush automatically on exit.

**Notes:**
- `prices` is `{input, output}` in **$ per 1M tokens**. Unknown model → cost `0`
  + one-time warning. Migrates cleanly to the future server-side pricing engine
  (SDK simply stops sending `prices`/`cost`).
- `enabled=False` (or `AGENTOPS_ENABLED=0`) makes every hook a no-op — safe to
  leave `init()` in production code.

## Data Flow, Capture & Failure Isolation

**Happy path (per instrumented call):**
```
client.create(...)  →  patched wrapper:
   t0 = perf_counter()
   resp = original_create(...)          # real call, untouched
   t1 = perf_counter()
   ── extract (in try/except) ──────────
   model, provider                       from kwargs / resp
   prompt (messages)                     from kwargs
   response text                         from resp choices/content
   prompt/completion/total_tokens        from resp.usage
   cost = pricing.compute(model, usage)  via user price map
   payload = {…} + current context (task/session/agent/env)
   transport.enqueue(payload)            # non-blocking
   return resp                           # caller gets the real response
```

**Two hard guarantees:**

1. **Never break the caller.** The entire capture block is wrapped in
   `try/except Exception`. Any failure (extraction, pricing, enqueue) is swallowed
   (warn-once) and the real response returned. A telemetry bug can never take down
   the user's agent.
2. **Never block the caller.** `enqueue` puts the payload on an in-memory
   `queue.Queue` and returns. A single daemon thread drains it and POSTs to
   `/api/v1/ingest`. Backend down / timeout → warn once, drop item, keep running.

**v1 scope boundaries (YAGNI):**
- **Non-streaming responses only.** Streaming calls don't expose `usage` reliably;
  v1 captures latency + response but records `tokens=0` for streamed calls
  (documented limitation, clean to extend later).
- **Success-only logging.** If the underlying LLM call raises, we re-raise
  unchanged and log nothing — the backend has no error/status field yet. No silent
  swallowing of the user's real errors.

Both providers map onto the same payload shape, keeping `transport` and `pricing`
provider-agnostic.

## Testing Strategy

Every unit tested in isolation, plus one end-to-end test through the real backend.

| Unit | Test approach |
|---|---|
| `pricing.py` | Known model → correct cost math; unknown model → `0` + warning emitted **once** (not per-call). |
| `context.py` | Nested `task`/`session` overrides resolve to innermost value; state restores on exit; isolated across threads. |
| `transport.py` | `enqueue` → background thread POSTs expected JSON (fake HTTP handler). Backend-down (connection refused/timeout) → **no exception propagates**, item dropped, warn-once. `shutdown()` flushes pending items. |
| `instrument/openai.py`, `instrument/anthropic.py` | Feed a **fake client** whose `create` returns a canned response; assert extracted payload (model, tokens, response text, provider). Assert a raising `create` re-raises and logs nothing. Assert an extraction bug still returns the real response. |
| **End-to-end** | Patch a fake client pointed at the real FastAPI app via `TestClient` as the ingest target; run an instrumented call; assert a row lands in the DB with correct task/session/cost. |

**Test infrastructure:** pytest (already in `requirements.txt`). Provider SDKs are
**not** required to run tests — hand-rolled fake client objects exercise extraction,
so CI needs neither `openai`/`anthropic` nor API keys. Extend
`.github/workflows/main.yml` to run SDK tests.

## Out of Scope (future work)

- Streaming token capture
- Error/status/retry tracking (needs a backend schema change)
- Server-side pricing engine (roadmap item #2 — SDK is designed to migrate to it)
- Batch ingestion endpoint
- Additional providers (Cohere, Gemini, Bedrock, LangChain callbacks)
```
