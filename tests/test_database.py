import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import APICall, AgentSession

# Setup an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_api_call(db):
    new_call = APICall(
        task_name="test_task",
        model="gpt-3.5-turbo",
        prompt="Hello",
        response="World",
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
        cost=0.0002,
        latency_ms=150.0
    )
    db.add(new_call)
    db.commit()
    db.refresh(new_call)
    
    assert new_call.id is not None
    assert new_call.task_name == "test_task"
    assert new_call.cost == 0.0002

def test_session_relationship(db):
    session = AgentSession(id="test-session-123", name="test_session")
    db.add(session)
    db.commit()
    
    new_call = APICall(
        session_id=session.id,
        task_name="test_task_2",
        model="gpt-4",
        prompt="Hi",
        response="Hello",
    )
    db.add(new_call)
    db.commit()
    
    # Refresh and check
    db.refresh(session)
    assert len(session.api_calls) == 1
    assert session.api_calls[0].task_name == "test_task_2"
