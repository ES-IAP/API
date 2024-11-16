from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.cognito import get_current_user
from app.schemas.task import TaskCreate, TaskRead
from app.crud.task import create_task, get_user_tasks, delete_task, get_task, update_task
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
    if task.deadline and task.deadline.date() < datetime.now(timezone.utc).date():
        raise HTTPException(status_code=400, detail="Deadline must be today or a future date")
    
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
    user: str = Depends(get_current_user)
):
    # Use the CRUD function to delete the task for the authenticated user
    task = delete_task(db=db, task_id=task_id, user_id=user.cognito_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=TaskRead)
def update_task_route(
    task_id: int,
    updated_fields: dict,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    print("Received updated_fields:", updated_fields)

        # Validate deadline if present
    if "deadline" in updated_fields:
        new_deadline_str = updated_fields["deadline"]
        try:
            # Parse the ISO 8601 string
            new_deadline = datetime.fromisoformat(new_deadline_str.replace("Z", "+00:00"))
        except ValueError:
            print("Invalid deadline format received:", new_deadline_str)
            raise HTTPException(status_code=400, detail="Invalid deadline format. Must be ISO 8601.")
        
        # Ensure deadline is today or in the future
        current_datetime = datetime.now(timezone.utc)
        if new_deadline.date() < current_datetime.date():
            print(f"Invalid deadline: {new_deadline} is before {current_datetime}")
            raise HTTPException(status_code=400, detail="Deadline must be today or a future date.")
        
        # Update the validated deadline in the fields
        updated_fields["deadline"] = new_deadline
        

    task = update_task(db=db, task_id=task_id, user_id=user.cognito_id, updated_fields=updated_fields)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
