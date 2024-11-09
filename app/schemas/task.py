from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.utils.priority import Priority
from app.utils.status import Status
from app.schemas.user import NewUser

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Priority  # Use the Priority enum here
    created_at: Optional[datetime] = datetime.now()
    status: Status  # Use the Status enum here

    class Config:
        use_enum_values = True  # This will store the enum as its value (e.g., "low", "medium", "high")

class TaskRead(TaskCreate):
    id: int
    created_at: datetime
    user: NewUser

    class Config:
        orm_mode = True  