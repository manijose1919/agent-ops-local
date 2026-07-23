# agentops-local

Zero-dependency Python SDK for [AgentOpsLocal](https://github.com/manijose1919/agent-ops-local).
Auto-instruments your OpenAI and Anthropic calls and streams LLM telemetry
(tokens, latency, cost) to your local AgentOpsLocal backend — with one `init()`
call and **no changes to your existing call sites**.

## Install

```bash
pip install agentops-local          # core (stdlib-only transport)
pip install agentops-local[openai]  # + OpenAI auto-instrumentation
pip install agentops-local[anthropic]
```

## Usage

```python
import agentops_local as ao

ao.init(
    base_url="http://localhost:8000",
    task="summarize_doc",
    environment="prod",
    prices={  # $ per 1M tokens; unknown models record cost=0
        "gpt-4o":          {"input": 2.50,  "output": 10.00},
        "claude-opus-4-8": {"input": 15.00, "output": 75.00},
    },
)

# Your existing code — captured automatically, unchanged:
client.chat.completions.create(model="gpt-4o", messages=[...])
```

Group calls into tasks and session traces with context managers:

```python
with ao.session("run-abc123"):
    with ao.task("plan_step"):
        client.messages.create(...)
    with ao.task("execute_step"):
        client.chat.completions.create(...)
```

## Guarantees

- **Never blocks your call** — telemetry is queued and sent from a background thread.
- **Never breaks your app** — if the backend is down or capture fails, it warns once and drops the data; your LLM call is unaffected.

## Scope (v1)

- Providers: OpenAI (`chat.completions.create`) and Anthropic (`messages.create`).
- Non-streaming responses (streaming calls are not token-captured yet).
- Success-only logging (failed LLM calls re-raise and are not recorded).

## License

MIT © Joseph Maniate
