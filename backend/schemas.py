from pydantic import BaseModel, Field
from typing import Optional, Any, Union, List, Dict
from datetime import datetime

class APICallCreate(BaseModel):
    task_name: str = Field(..., description="Name of the task that triggered this API call")
    session_id: Optional[str] = Field(None, description="Optional UUID linking multiple calls")
    agent_id: Optional[str] = Field(None, description="ID of the autonomous agent making the call")
    model: str = Field(..., description="Model identifier used (e.g., gpt-4)")
    provider: Optional[str] = Field(None, description="Provider of the model (e.g., openai)")
    prompt: Union[str, List[Dict[str, Any]], Dict[str, Any]] = Field(..., description="The prompt sent to the model")
    response: str = Field(..., description="The text response from the model")
    prompt_tokens: int = Field(0, description="Tokens used in the prompt")
    completion_tokens: int = Field(0, description="Tokens used in the completion")
    total_tokens: int = Field(0, description="Total tokens used")
    cost: float = Field(0.0, description="Calculated cost of the call in USD")
    latency_ms: float = Field(0.0, description="Latency of the API call in milliseconds")

from pydantic import ConfigDict

class APICallResponse(APICallCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AnalyticsSummary(BaseModel):
    total_calls: int
    total_cost: float
    avg_latency_ms: float
    total_tokens: int
    by_model: Dict[str, float] = Field(..., description="Cost broken down by model")
    by_task: Dict[str, float] = Field(..., description="Cost broken down by task name")
    by_agent: Dict[str, float] = Field(default_factory=dict, description="Cost broken down by agent ID")
