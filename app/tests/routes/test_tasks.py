import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal, Base
from app.utils.cognito import get_current_user_info
from sqlalchemy.orm import Session
from app.crud.user import create_user, get_user_by_cognito_id
from app.schemas.user import NewUser

client = TestClient(app)

# Mock function to simulate Cognito user info
def mock_get_current_user_info(user_id: str):
    return {"sub": user_id}

# Fixture for setting up and tearing down the test database
@pytest.fixture
def test_db():
    # Setup test database session
    db = SessionLocal()
    # Ensure a clean slate by deleting all records
    Base.metadata.drop_all(bind=db.get_bind())
    Base.metadata.create_all(bind=db.get_bind())
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# Helper function to create a user in the database
def create_user_in_db(db: Session, user_id: str, email: str, username: str):
    existing_user = get_user_by_cognito_id(user_id, db)
    if not existing_user:
        user_data = NewUser(cognito_id=user_id, email=email, username=username)
        return create_user(db=db, user=user_data)
    return existing_user

# Test to verify that users can only see their own tasks
def test_user_can_only_see_own_tasks(test_db):
    # Simulate User A
    user_a_id = "90cca98c-7041-70f8-3298-479881cae008"
    user_a_email = "user_a@example.com"
    user_a_username = "UserA"

    # Simulate User B
    user_b_id = "004c19cc-e021-70ce-5655-6eb6c36dd08b"
    user_b_email = "user_b@example.com"
    user_b_username = "UserB"

    # Create users in the database
    create_user_in_db(test_db, user_id=user_a_id, email=user_a_email, username=user_a_username)
    create_user_in_db(test_db, user_id=user_b_id, email=user_b_email, username=user_b_username)

    # Override dependency to simulate User A
    app.dependency_overrides[get_current_user_info] = lambda: mock_get_current_user_info(user_a_id)
    
    # Use POST /tasks endpoint to create a task for User A
    task_data_a = {
        "title": "User A's Task",
        "description": "Task for User A",
        "category": "General",
        "deadline": "2024-12-31T00:00:00",
        "priority": 1
    }
    response_a_post = client.post("/tasks", json=task_data_a, cookies={"access_token": "mock_token"})
    assert response_a_post.status_code == 200
    task_a = response_a_post.json()
    assert task_a["title"] == "User A's Task"

    # Fetch tasks for User A using GET /tasks
    response_a_get = client.get("/tasks", cookies={"access_token": "mock_token"})
    assert response_a_get.status_code == 200
    tasks_a = response_a_get.json()
    assert len(tasks_a) == 1
    assert tasks_a[0]["title"] == "User A's Task"

    # Now simulate as User B
    app.dependency_overrides[get_current_user_info] = lambda: mock_get_current_user_info(user_b_id)

    # Use POST /tasks endpoint to create a task for User B
    task_data_b = {
        "title": "User B's Task",
        "description": "Task for User B",
        "category": "General",
        "deadline": "2024-12-31T00:00:00",
        "priority": 2
    }
    response_b_post = client.post("/tasks", json=task_data_b, cookies={"access_token": "mock_token"})
    assert response_b_post.status_code == 200
    task_b = response_b_post.json()
    assert task_b["title"] == "User B's Task"

    # Fetch tasks for User B using GET /tasks
    response_b_get = client.get("/tasks", cookies={"access_token": "mock_token"})
    assert response_b_get.status_code == 200
    tasks_b = response_b_get.json()
    assert len(tasks_b) == 1
    assert tasks_b[0]["title"] == "User B's Task"

    # Ensure User A's task is not visible to User B and vice versa
    assert tasks_a[0]["user_id"] == user_a_id
    assert tasks_b[0]["user_id"] == user_b_id

    # Cleanup: reset dependency override
    app.dependency_overrides = {}
