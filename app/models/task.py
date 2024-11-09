from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
from app.utils.priority import Priority
from app.utils.status import Status

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)  
    description = Column(String(1024), nullable=False)     
    deadline = Column(DateTime,nullable=True)              
    priority = Column(Enum(Priority), default=Priority.LOW, nullable=True) 
    created_at = Column(DateTime, default=datetime.now())   
    # updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now()) 
    status = Column(Enum(Status), default=Status.TODO, nullable=False)
    user_id = Column(String(255), ForeignKey("users.cognito_id"), nullable=False) 

    # Define relationships if needed
    user = relationship("User", back_populates="tasks")

    # Set a default value for created_at to the current time
    created_at = Column(DateTime, default=datetime.now())

    # Set a default value for updated_at to the current time and update it on every change
    # updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
