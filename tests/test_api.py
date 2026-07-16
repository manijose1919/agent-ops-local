import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db, Base
from backend import models

from sqlalchemy.pool import StaticPool

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_ingest_telemetry():
    payload = {
        "task_name": "test_ingestion",
        "model": "gpt-4",
        "provider": "openai",
        "prompt": "Say hello",
        "response": "Hello!",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "cost": 0.0015,
        "latency_ms": 200.5
    }
    
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["task_name"] == "test_ingestion"
    assert data["cost"] == 0.0015
    assert "id" in data

def test_get_calls():
    response = client.get("/api/v1/calls") 
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_analytics_summary():
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_calls"] >= 1
    assert data["total_cost"] >= 0.0015
    assert "by_model" in data
    assert "by_task" in data

def test_get_anomalies():
    # Insert 5 normal calls
    for _ in range(5):
        client.post(
            "/api/v1/ingest",
            json={
                "task_name": "anomaly_task",
                "model": "gpt-3.5-turbo",
                "prompt": "Hello",
                "response": "World",
                "latency_ms": 100,
                "prompt_tokens": 1000,
                "completion_tokens": 10,
                "cost": 0.0015,
                "total_tokens": 1010
            }
        )
    
    # Insert a massive call
    r2 = client.post(
        "/api/v1/ingest",
        json={
            "task_name": "anomaly_task",
            "model": "gpt-4-turbo",
            "prompt": "Huge Hello",
            "response": "Huge World",
            "latency_ms": 1000,
            "prompt_tokens": 100000,
            "completion_tokens": 10000,
            "cost": 2.00
        }
    )
    assert r2.status_code == 201, r2.text
    
    response = client.get("/api/v1/analytics/anomalies")
    assert response.status_code == 200
    anomalies = response.json()
    print("ALL CALLS:", client.get("/api/v1/calls").json())
    print("ANOMALIES:", anomalies)
    assert len(anomalies) >= 1
    # Find our specific anomaly
    anomaly = next((a for a in anomalies if a["task_name"] == "anomaly_task"), None)
    assert anomaly is not None
    assert anomaly["severity"] in ["HIGH", "MEDIUM"]
