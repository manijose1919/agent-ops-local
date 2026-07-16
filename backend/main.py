from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import engine, Base, get_db
from backend import models, schemas

from backend.routers import ingest, analytics

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgentOpsLocal Telemetry API",
    description="Local telemetry and cost analyzer for AI Agents.",
    version="0.1.0",
)

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1/analytics")

@app.get("/")
def read_root():
    return {"message": "AgentOpsLocal API is running. Visit /docs for Swagger UI."}
