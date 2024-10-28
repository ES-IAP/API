from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str
    category: str
    deadline: Optional[datetime] = None
    priority: Optional[int] = None
