from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict
import os

from backend.database import get_db
from backend.models import APICall
from backend.schemas import AnalyticsSummary
from backend import schemas

router = APIRouter()

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(env: str = None, db: Session = Depends(get_db)):
    """Retrieve aggregated analytics summary."""
    
    base_query = db.query(APICall)
    if env:
        base_query = base_query.filter(APICall.environment == env)
    
    total_calls = base_query.with_entities(func.count(APICall.id)).scalar() or 0
    total_cost = base_query.with_entities(func.sum(APICall.cost)).scalar() or 0.0
    avg_latency = base_query.with_entities(func.avg(APICall.latency_ms)).scalar() or 0.0
    total_tokens = base_query.with_entities(func.sum(APICall.total_tokens)).scalar() or 0
    
    # Cost by model
    # Cost by model
    model_stats = base_query.with_entities(
        APICall.model, 
        func.sum(APICall.cost)
    ).group_by(APICall.model).all()
    
    by_model: Dict[str, float] = {model: cost for model, cost in model_stats if model}
    
    # Cost by task
    # Cost by task
    task_stats = base_query.with_entities(
        APICall.task_name,
        func.sum(APICall.cost)
    ).group_by(APICall.task_name).all()
    
    by_task: Dict[str, float] = {task: cost for task, cost in task_stats if task}
    
    # Cost by agent
    # Cost by agent
    agent_stats = base_query.filter(APICall.agent_id != None).with_entities(
        APICall.agent_id,
        func.sum(APICall.cost)
    ).group_by(APICall.agent_id).all()
    
    by_agent: Dict[str, float] = {agent: cost for agent, cost in agent_stats if agent}
    
    # Cost over time (daily)
    # Cost over time (daily)
    all_calls = base_query.with_entities(APICall.created_at, APICall.cost).all()
    cost_over_time = {}
    for created_at, c_cost in all_calls:
        if created_at:
            day = created_at.date().isoformat()
            cost_over_time[day] = cost_over_time.get(day, 0.0) + (c_cost or 0.0)
    
    return AnalyticsSummary(
        total_calls=total_calls,
        total_cost=total_cost,
        avg_latency_ms=avg_latency,
        total_tokens=total_tokens,
        by_model=by_model,
        by_task=by_task,
        by_agent=by_agent,
        cost_over_time=cost_over_time,
        daily_budget=float(os.getenv("DAILY_BUDGET", "0"))
    )

from typing import List

@router.get("/anomalies", response_model=List[schemas.AnomalyReport])
def get_anomalies(env: str = None, db: Session = Depends(get_db)):
    """Detect calls that cost 2x more than the average for their task."""
    query = db.query(APICall)
    if env:
        query = query.filter(APICall.environment == env)
    calls = query.all()
    if not calls:
        return []
        
    # Calculate averages per task
    task_stats = {}
    for c in calls:
        if c.task_name not in task_stats:
            task_stats[c.task_name] = {"cost": [], "tokens": []}
        task_stats[c.task_name]["cost"].append(c.cost)
        task_stats[c.task_name]["tokens"].append(c.total_tokens)
        
    averages = {}
    for task, stats in task_stats.items():
        averages[task] = {
            "avg_cost": sum(stats["cost"]) / len(stats["cost"]),
            "avg_tokens": sum(stats["tokens"]) / len(stats["tokens"])
        }
        
    anomalies = []
    for c in calls:
        avg = averages[c.task_name]
        # Flag if cost is > 2x average AND cost > $0.001 (ignore tiny anomalies)
        if c.cost > avg["avg_cost"] * 2 and c.cost > 0.001:
            anomalies.append({
                "call_id": c.id,
                "task_name": c.task_name,
                "cost": c.cost,
                "avg_cost": avg["avg_cost"],
                "total_tokens": c.total_tokens,
                "avg_tokens": avg["avg_tokens"],
                "severity": "HIGH" if c.cost > avg["avg_cost"] * 5 else "MEDIUM"
            })
            
    return anomalies

@router.get("/export")
def export_calls(env: str = None, db: Session = Depends(get_db)):
    """Export all telemetry data as a JSON file for fine-tuning or backup."""
    query = db.query(APICall)
    if env:
        query = query.filter(APICall.environment == env)
    calls = query.all()
    
    # Return as JSON file attachment
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        content=[
            {
                "id": c.id,
                "session_id": c.session_id,
                "agent_id": c.agent_id,
                "task_name": c.task_name,
                "model": c.model,
                "provider": c.provider,
                "prompt": c.prompt,
                "response": c.response,
                "prompt_tokens": c.prompt_tokens,
                "completion_tokens": c.completion_tokens,
                "total_tokens": c.total_tokens,
                "cost": c.cost,
                "latency_ms": c.latency_ms,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in calls
        ],
        headers={
            "Content-Disposition": "attachment; filename=agentops_export.json"
        }
    )

from fastapi import HTTPException

@router.get("/sessions/{session_id}", response_model=List[schemas.APICallResponse])
def get_session_calls(session_id: str, db: Session = Depends(get_db)):
    """Get all calls in a session timeline."""
    calls = db.query(APICall).filter(APICall.session_id == session_id).order_by(APICall.created_at.asc()).all()
    if not calls:
        raise HTTPException(status_code=404, detail="Session not found")
    return calls
