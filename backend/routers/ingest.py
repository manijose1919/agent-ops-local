from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
from datetime import datetime, time
from backend.database import get_db
from backend.models import APICall, AgentSession
from backend.schemas import APICallCreate, APICallResponse

router = APIRouter()

@router.post("/ingest", response_model=APICallResponse, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(call_data: APICallCreate, db: Session = Depends(get_db)):
    """Ingest a single API call telemetry log."""
    
    # Optional: Handle session linking if session_id is provided
    if call_data.session_id:
        session = db.query(AgentSession).filter(AgentSession.id == call_data.session_id).first()
        if not session:
            # Auto-create session if it doesn't exist
            session = AgentSession(id=call_data.session_id, name=f"Session {call_data.session_id}")
            db.add(session)
            db.commit()
            
    # Budget check
    daily_budget_str = os.getenv("DAILY_BUDGET", "0")
    daily_budget = float(daily_budget_str)
    if daily_budget > 0:
        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        today_cost = db.query(func.sum(APICall.cost)).filter(APICall.created_at >= today_start).scalar() or 0.0
        if today_cost + (call_data.cost or 0.0) > daily_budget:
            raise HTTPException(status_code=429, detail=f"Daily budget of ${daily_budget} exceeded. Today's cost: ${today_cost:.4f}")

    db_call = APICall(
        session_id=call_data.session_id,
        agent_id=call_data.agent_id,
        environment=call_data.environment,
        task_name=call_data.task_name,
        model=call_data.model,
        provider=call_data.provider,
        prompt=call_data.prompt,
        response=call_data.response,
        prompt_tokens=call_data.prompt_tokens,
        completion_tokens=call_data.completion_tokens,
        total_tokens=call_data.total_tokens,
        cost=call_data.cost,
        latency_ms=call_data.latency_ms
    )
    
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    
    return db_call

@router.get("/calls", response_model=list[APICallResponse])
def get_all_calls(skip: int = 0, limit: int = 100, env: str = None, db: Session = Depends(get_db)):
    """Retrieve all ingested API calls."""
    query = db.query(APICall)
    if env:
        query = query.filter(APICall.environment == env)
    calls = query.order_by(APICall.created_at.desc()).offset(skip).limit(limit).all()
    return calls
