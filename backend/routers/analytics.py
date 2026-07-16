from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict

from backend.database import get_db
from backend.models import APICall
from backend.schemas import AnalyticsSummary
from backend import schemas

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
    
    # Cost by agent
    agent_stats = db.query(
        APICall.agent_id,
        func.sum(APICall.cost)
    ).filter(APICall.agent_id != None).group_by(APICall.agent_id).all()
    
    by_agent: Dict[str, float] = {agent: cost for agent, cost in agent_stats if agent}
    
    return AnalyticsSummary(
        total_calls=total_calls,
        total_cost=total_cost,
        avg_latency_ms=avg_latency,
        total_tokens=total_tokens,
        by_model=by_model,
        by_task=by_task,
        by_agent=by_agent
    )

from typing import List

@router.get("/anomalies", response_model=List[schemas.AnomalyReport])
def get_anomalies(db: Session = Depends(get_db)):
    """Detect calls that cost 2x more than the average for their task."""
    calls = db.query(APICall).all()
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
