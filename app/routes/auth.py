from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from app.utils.cognito import get_current_user_info, get_user_info
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.schemas.user import NewUser 
from app.config import COGNITO_REGION, USER_POOL_ID, CLIENT_ID, COGNITO_DOMAIN
from app.crud.user import create_user, get_user_by_cognito_id

router = APIRouter()

@router.post("/login")
def login(
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)  # Inject the user_info dependency
):
    print("User Info received in /login:", user_info)  # Debug

    # Extract fields from the token
    username = user_info.get("cognito:username")
    email = user_info.get("email")
    cognito_id = user_info.get("sub")

    if not username or not email:
        user_info_fetched = get_user_info(user_info["token"])
        username = username or user_info_fetched.get("username")
        email = email or user_info_fetched.get("email")

    if not username or not email or not cognito_id:
        raise HTTPException(status_code=500, detail="Required user fields are missing")

    # Check if user exists in the database
    db_user = get_user_by_cognito_id(cognito_id, db)
    print("DB User in /login:", db_user)  # Debug

    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")

    if not db_user:
        user = NewUser(cognito_id=cognito_id,username=username, email=email)
        db_new_user = create_user(user, db)
        print("New user created:", db_new_user)  # Debug

    return {"message": "Login successful", "user": {"username": db_new_user.username, "email": db_new_user.email}}

@router.get("/me")
async def get_current_user(
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)  # Inject the user_info dependency
):
    cognito_id = user_info.get("sub")
    if not cognito_id:
        raise HTTPException(status_code=500, detail="Cognito ID is missing in token")

    db_user = get_user_by_cognito_id(cognito_id, db)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": db_user.username,
        "email": db_user.email,
        "cognito_id": db_user.cognito_id
    }

# @router.get("/logout")
# async def logout():
#     logout_url = f"https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/logout?client_id={CLIENT_ID}&logout_uri=https://yourapp.com/login"
#     return RedirectResponse(url=logout_url)
