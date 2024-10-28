from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.cognito import get_current_user_info
from app.models.task import Task
from app.schemas.task import TaskCreate  

router = APIRouter()

@router.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)  # Inject the user info dependency
):
    cognito_id = user_info.get("sub")  # Get the user's cognito_id from the token

    # Create a new task
    db_task = Task(
        title=task.title,
        description=task.description,
        category=task.category,
        deadline=task.deadline,
        priority=task.priority,
        user_id=cognito_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task

@router.get("/tasks")
def get_user_tasks(
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)
):
    # Extract the user's unique identifier (Cognito ID)
    cognito_id = user_info.get("sub")
    if not cognito_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Query tasks for the logged-in user only
    tasks = db.query(Task).filter(Task.user_id == cognito_id).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    return tasks
