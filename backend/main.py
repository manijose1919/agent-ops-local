from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from backend.database import engine, Base
from backend.routers import ingest, analytics
from backend.auth import api_secret, require_api_key

# Create all database tables
Base.metadata.create_all(bind=engine)

log = logging.getLogger("agentops")

app = FastAPI(
    title="AgentOpsLocal Telemetry API",
    description="Local telemetry and cost analyzer for AI Agents.",
    version="0.1.0",
    dependencies=[Depends(require_api_key)],
)

# Dashboard origin only — never credentials+wildcard (browsers reject that combo
# and it trains a too-open production config).
_cors = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1/analytics")


@app.get("/")
def read_root():
    return {"message": "AgentOpsLocal API is running. Visit /docs for Swagger UI."}


@app.on_event("startup")
def _warn_if_open() -> None:
    if not api_secret():
        log.warning(
            "API_SECRET_KEY is unset — ingest and analytics are open. Fine on "
            "localhost; set a key before publishing port 8000 past this machine."
        )
