from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class AgentSession(Base):
    """A collection of API calls that make up a single agent run or session."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True) # UUID string
    name = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    api_calls = relationship("APICall", back_populates="session", cascade="all, delete-orphan")

class APICall(Base):
    """An individual LLM API request/response."""
    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), index=True, nullable=True)
    task_name = Column(String, index=True) # e.g., "summarize_doc", "generate_code"
    
    model = Column(String, index=True) # e.g., "gpt-4-turbo"
    provider = Column(String, index=True, nullable=True) # e.g., "openai"
    
    prompt = Column(JSON) # Array of message dicts or string
    response = Column(Text)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    session = relationship("AgentSession", back_populates="api_calls")
