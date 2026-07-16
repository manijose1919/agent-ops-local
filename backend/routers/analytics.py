from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict

from backend.database import get_db
from backend.models import APICall
from backend.schemas import AnalyticsSummary

router = APIRouter()

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Retrieve aggregated analytics summary."""
    
    total_calls = db.query(func.count(APICall.id)).scalar() or 0
    total_cost = db.query(func.sum(APICall.cost)).scalar() or 0.0
    avg_latency = db.query(func.avg(APICall.latency_ms)).scalar() or 0.0
    total_tokens = db.query(func.sum(APICall.total_tokens)).scalar() or 0
    
    # Cost by model
    model_stats = db.query(
        APICall.model, 
        func.sum(APICall.cost)
    ).group_by(APICall.model).all()
    
    by_model: Dict[str, float] = {model: cost for model, cost in model_stats if model}
    
    # Cost by task
    task_stats = db.query(
        APICall.task_name,
        func.sum(APICall.cost)
    ).group_by(APICall.task_name).all()
    
    by_task: Dict[str, float] = {task: cost for task, cost in task_stats if task}
    
    return AnalyticsSummary(
        total_calls=total_calls,
        total_cost=total_cost,
        avg_latency_ms=avg_latency,
        total_tokens=total_tokens,
        by_model=by_model,
        by_task=by_task
    )
