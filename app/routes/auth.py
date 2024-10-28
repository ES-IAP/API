# app/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from app.utils.cognito import validate_jwt_token, get_user_info
from app.models.user import User
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import boto3
from app.schemas.user import RegistrationData 
from app.config import COGNITO_REGION, USER_POOL_ID, CLIENT_ID, COGNITO_DOMAIN

router = APIRouter()

# Initialize the Cognito client
cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

@router.post("/register")
def register_user(data: RegistrationData):
    try:
        # Call Cognito to sign up the user
        response = cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username=data.username,
            Password=data.password,
            UserAttributes=[
                {
                    "Name": "email",
                    "Value": data.email
                },
            ],
        )
        return {"message": "User registered successfully", "user": response}
    except cognito_client.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to register user")


@router.post("/login")
def login(authorization: str = Header(...), db: Session = Depends(get_db)):
    # Extract token from the "Authorization" header
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization header format")
    token = authorization.split("Bearer ")[1]

    try:
        # Validate JWT Token
        user_info = validate_jwt_token(token)
        print("Decoded Token:", user_info)  # Debugging: prints token info
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Attempt to get `username`, `email`, and `cognito_id`
    username = user_info.get("cognito:username")
    email = user_info.get("email")
    cognito_id = user_info.get("sub")

    # Log the extracted fields
    print(f"Extracted username: {username}, email: {email}, cognito_id: {cognito_id}")

    # If username or email is missing, retrieve it from the UserInfo endpoint
    if not username or not email:
        print("Fetching additional info from /userInfo endpoint")
        user_info_fetched = get_user_info(token)  # Use the correct token type for userInfo
        username = username or user_info_fetched.get("username")
        email = email or user_info_fetched.get("email")
        print("Fetched UserInfo:", user_info_fetched)  # Debugging line

    # Check if required fields are available
    if not username or not email or not cognito_id:
        print("Missing required user fields. Username:", username, "Email:", email, "Cognito ID:", cognito_id)
        raise HTTPException(status_code=500, detail="Required user fields are missing")

    # Check if user exists in the database
    stmt = select(User).where(User.cognito_id == cognito_id)
    result = db.execute(stmt)
    db_user = result.scalar_one_or_none()

    # If the user doesn't exist, add them to the database
    if not db_user:
        print("Creating new user with:", username, email, cognito_id)  # Debug line
        new_user = User(username=username, email=email, cognito_id=cognito_id)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = new_user

    return {"message": "Login successful", "user": {"username": db_user.username, "email": db_user.email}}


@router.get("/logout")
async def logout():
    # Construct the logout URL
    logout_url = f"https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/logout?client_id={CLIENT_ID}&logout_uri=https://yourapp.com/login"
    
    # Redirect to the Cognito logout URL
    return RedirectResponse(url=logout_url)
