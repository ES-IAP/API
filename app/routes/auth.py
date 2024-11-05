from fastapi import APIRouter, Depends, HTTPException, Response, Request, Cookie
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.cognito import get_current_user_info, validate_jwt_token
from app.schemas.user import NewUser
from app.config import COGNITO_REGION, CLIENT_ID, CLIENT_SECRET, COGNITO_DOMAIN
from app.crud.user import create_user, get_user_by_cognito_id
import requests
import json
from jose import jwt

router = APIRouter()

# Redirect to Cognito Hosted UI for login
@router.get("/login")
def login():
    cognito_login_url = (
        f"https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/login?"
        f"client_id={CLIENT_ID}&response_type=code&scope=email+openid+profile&"
        f"redirect_uri=http://localhost:8000/auth/callback" 
    )
    return RedirectResponse(url=cognito_login_url)


@router.get("/auth/callback")
def auth_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    # Retrieve the authorization code from query parameters
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    # Exchange the authorization code for an access token
    token_url = f"https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/oauth2/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": "http://localhost:8000/auth/callback"  # Match with Cognito's configuration
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    if token_response.status_code != 200:
        raise HTTPException(status_code=token_response.status_code, detail="Failed to fetch access token")

    tokens = token_response.json()
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")
    
    if not id_token or not access_token:
        raise HTTPException(status_code=400, detail="ID or access token not found in response")

    # Print the decoded token to inspect the fields
    decoded_token = jwt.get_unverified_claims(id_token)
    print("Decoded token:", json.dumps(decoded_token, indent=4))

    # Extract user information
    cognito_id = decoded_token.get("sub")
    username = decoded_token.get("cognito:username")
    email = decoded_token.get("email")

    if not cognito_id or not username or not email:
        raise HTTPException(status_code=500, detail="Required user fields are missing")

    # Check if user exists in the database; create if not
    db_user = get_user_by_cognito_id(cognito_id, db)
    if not db_user:
        user = NewUser(cognito_id=cognito_id, username=username, email=email)
        db_user = create_user(user, db)

    # Set the access token in a secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600, 
        secure=False,
        samesite="lax"  # "lax" is usually compatible with cross-site redirects
    )

    # Return a RedirectResponse after setting the cookie
    return RedirectResponse(url="http://localhost:3000")


@router.get("/me")
def get_current_user(
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info)
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

@router.post("/logout")
def logout(response: Response):
    cognito_logout_url = (
        f"https://{COGNITO_DOMAIN}/logout?"
        f"client_id={CLIENT_ID}&logout_uri=http://localhost:3000/"  # REDIRECT_URI deve estar registrado no Cognito
    )
    response = RedirectResponse(url=cognito_logout_url)
    response.delete_cookie(key="access_token")
    return response
