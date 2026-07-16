# AI Agent Task Telemetry & Cost Analyzer (AgentOpsLocal)

## The Problem
As developers build complex multi-agent workflows, tracing exactly what prompts were sent to LLMs, the latency of each call, and the resulting token usage (and cost) becomes impossible to manage across standard logs. There is a strong need for a standalone, private, zero-config local tool that acts as a telemetry sink for AI Agents.

## The Solution
**AgentOpsLocal** is a lightweight engine combining a high-performance Python FastAPI backend (with SQLite) and a modern React/Vite dashboard. Developers simply route their LLM API calls (or log them async) through the AgentOpsLocal ingestion endpoint, and it provides real-time analytics on token usage, latency, and costs grouped by "Agent Tasks" or "Sessions".

## Quickstart Guide (1-Step Standalone)
1. Clone this repository.
2. Double-click the `run.bat` file on Windows. (Make sure Docker Desktop is installed).
3. The dashboard will be available at `http://localhost:5173`.
4. The API will be available at `http://localhost:8000/docs`.

## Integration Guide (How to plug into your Enterprise systems)
You can easily integrate this tool into any Python or Node.js agent by sending a simple POST request to the `/ingest` endpoint whenever an LLM call completes.

```python
import requests
import time

def log_llm_call(task_name, model, prompt, response, tokens, cost):
    requests.post("http://localhost:8000/ingest", json={
        "task_id": task_name,
        "model": model,
        "prompt": prompt,
        "response": response,
        "tokens_used": tokens,
        "cost": cost,
        "latency_ms": 150
    })
```

## Target Audience & Client Acquisition
- **Target Audience:** Solo developers, AI researchers, and engineering teams building multi-agent systems using frameworks like LangChain, AutoGen, or custom orchestrators.
- **Acquisition Strategy:** Open-source release as a "Must-Have Developer Tool for AI". Providing SDKs for easy integration will drive bottom-up adoption.

## Architecture
- Backend: FastAPI, SQLAlchemy, SQLite (Swappable to Postgres).
- Frontend: React (Vite), TailwindCSS, Recharts.
- Deployment: Docker & Docker Compose.
