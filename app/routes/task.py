from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.cognito import get_current_user_info
from app.schemas.task import TaskCreate
from app.crud.task import create_task, get_user_tasks, delete_task

router = APIRouter()

@router.post("/tasks")
def create_task_route(
    task: TaskCreate,
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)
):
    cognito_id = user_info.get("sub")

    # Use the CRUD function to create a new task
    db_task = create_task(db=db, task=task, user_id=cognito_id)
    return db_task

@router.get("/tasks")
def get_user_tasks_route(
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)
):
    cognito_id = user_info.get("sub")
    if not cognito_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Use the CRUD function to get the user's tasks
    tasks = get_user_tasks(db=db, user_id=cognito_id)
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    return tasks

@router.delete("/tasks/{task_id}")
def delete_task_route(
    task_id: int,
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)
):
    cognito_id = user_info.get("sub")
    if not cognito_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    task = delete_task(db=db, task_id=task_id, user_id=cognito_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
