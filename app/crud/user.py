##create user and get user by email
from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.schemas.user import NewUser
from app.db.database import get_db
from fastapi import Depends


def create_user(user: NewUser, db: Session = Depends(get_db)):

    user_db = UserModel(**user.model_dump())
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db

def get_user_by_email(email: str, db: Session = Depends(get_db)):
    return db.query(UserModel).filter(UserModel.email == email).first()

def get_user_by_cognito_id(cognito_id: str, db: Session = Depends(get_db)):
    return db.query(UserModel).filter(UserModel.cognito_id == cognito_id).first()

