from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.cognito import get_current_user
from app.schemas.task import TaskCreate, TaskRead
from app.crud.task import create_task, get_user_tasks, delete_task, get_task
from datetime import datetime, timezone
from typing import List
from app.utils.status import Status

router = APIRouter()

@router.post("/tasks")
def create_task_route(
    task: TaskCreate,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    print("Received data:", task)

    # Validate if deadline is in the future
    if task.deadline and task.deadline < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Deadline must be a future date")
    
    # Use the CRUD function to create a new task for the authenticated user
    db_task = create_task(db=db, task=task, user_id=user.cognito_id)
    return db_task

@router.get("/tasks", response_model=List[TaskRead])
def get_user_tasks_route(
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    # Use the CRUD function to get the user's tasks
    tasks = get_user_tasks(db=db, user_id=user.cognito_id)
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")
    return tasks

@router.delete("/tasks/{task_id}")
def delete_task_route(
    task_id: int,
    db: Session = Depends(get_db),
    cognito_id: str = Depends(get_current_user)
):
    # Use the CRUD function to delete the task for the authenticated user
    task = delete_task(db=db, task_id=task_id, user_id=cognito_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/task/{task_id}")
async def update_task_status(task_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    task = get_task(db=db, task_id=task_id, user_id=user.cognito_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = Status.DONE
    db.commit()
    db.refresh(task)
    return task

@router.put("/tasks/{task_id}", response_model=TaskRead)
def update_task_route(
    task_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    existing_task = get_task(db=db, task_id=task_id, user_id=user.cognito_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task details
    existing_task.title = task.title
    existing_task.description = task.description
    existing_task.priority = task.priority
    existing_task.deadline = task.deadline
    existing_task.last_updated = datetime.now(timezone.utc)

    db.commit()
    db.refresh(existing_task)
    return existing_task


