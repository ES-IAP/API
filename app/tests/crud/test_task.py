import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.models.task import Task
from app.schemas.task import TaskCreate
from app.crud.task import create_task, get_user_tasks
from fastapi.testclient import TestClient
from app.main import app  # Assuming app is the FastAPI instance in the main module
from app.utils.cognito import get_current_user_info

# In-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency for the database session in testing
@pytest.fixture(scope="module")
def db():
    # Create the tables in the in-memory database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="module")
def client():
    # Mock the get_current_user_info dependency to simulate an authenticated user
    def mock_get_current_user_info():
        return {"sub": "test_user_id"}  # Mock user_id as "test_user_id"
    
    app.dependency_overrides[get_db] = lambda: TestingSessionLocal()
    app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
    with TestClient(app) as c:
        yield c

# Test for the create_task function
def test_create_task(db):
    task_data = TaskCreate(
        title="Test Task",
        description="This is a test task",
        category="Test Category",
        priority=1
    )
    user_id = "test_user_id"
    created_task = create_task(db, task_data, user_id)
    
    assert created_task.id is not None
    assert created_task.title == "Test Task"
    assert created_task.description == "This is a test task"
    assert created_task.category == "Test Category"
    assert created_task.priority == 1
    assert created_task.user_id == user_id

# Test for the get_user_tasks function
def test_get_user_tasks(db):
    # First, create a task to ensure there is at least one for the user
    task_data = TaskCreate(
        title="Another Test Task",
        description="Testing retrieval of tasks",
        category="Test",
        priority=2
    )
    user_id = "test_user_id"
    create_task(db, task_data, user_id)

    # Now, retrieve tasks for the user
    tasks = get_user_tasks(db, user_id)
    
    assert len(tasks) > 0
    assert all(task.user_id == user_id for task in tasks)

