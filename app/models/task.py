from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)  # Set a length, e.g., 255 characters
    description = Column(String(1024), nullable=False)       # Set a length based on your needs
    category = Column(String(255), nullable=False)           # Set a length, e.g., 255 characters
    deadline = Column(DateTime, nullable=True)               # Optional deadline
    priority = Column(Integer, nullable=True)                # Optional priority (e.g., 1 = High, 2 = Medium, 3 = Low)
    user_id = Column(String(255), ForeignKey("users.cognito_id"), nullable=False)  # Set length for user_id

    # Define relationships if needed
    user = relationship("User", back_populates="tasks")

    # Set a default value for created_at to the current time
    created_at = Column(DateTime, default=datetime.utcnow)
