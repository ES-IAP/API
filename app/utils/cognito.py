from fastapi import HTTPException, Cookie
from jose import jwt, JWTError
from app.config import COGNITO_REGION, USER_POOL_ID, CLIENT_ID
import requests
import os

# Function to retrieve Cognito public keys
def get_cognito_public_keys():
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Cognito public keys")
    return response.json()["keys"]

public_keys = get_cognito_public_keys()

# Validate the JWT token using Cognito public keys
def validate_jwt_token(token: str):
    headers = jwt.get_unverified_headers(token)
    kid = headers["kid"]
    key = next((key for key in public_keys if key["kid"] == kid), None)
    if key is None:
        raise ValueError("Public key not found")

        # Ensure issuer URL matches the Cognito User Pool URL
    issuer = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"

    try:
        decoded_token = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=issuer  # Use the correct issuer
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    return decoded_token

# Dependency function to get user info from the access token in the cookie
def get_current_user_info(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Token not provided")

    try:
        user_info = validate_jwt_token(access_token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_info
