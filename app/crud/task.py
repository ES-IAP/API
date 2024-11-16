from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate
from datetime import datetime

def create_task(db: Session, task: TaskCreate, user_id: str):
    db_task = Task(
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        created_at=datetime.now(),
        status=task.status,
        user_id=user_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_user_tasks(db: Session, user_id: str):
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks

def get_task(db: Session, task_id: int, user_id: str):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    return task

def delete_task(db: Session, task_id: int, user_id: str):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task:
        db.delete(task)
        db.commit()
    return task


