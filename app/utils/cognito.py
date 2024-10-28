from fastapi import Depends, HTTPException, Header
from jose import jwt
from app.config import COGNITO_REGION, USER_POOL_ID, CLIENT_ID, COGNITO_DOMAIN
import requests

def get_cognito_public_keys():
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
    response = requests.get(url)
    return response.json()["keys"]

public_keys = get_cognito_public_keys()

def validate_jwt_token(token: str):
    headers = jwt.get_unverified_headers(token)
    kid = headers["kid"]
    key = next((key for key in public_keys if key["kid"] == kid), None)
    if key is None:
        raise ValueError("Public key not found")

    decoded_token = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=CLIENT_ID,
        issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}",
        options={"verify_at_hash": False}
    )
    # Debugging: Print the entire decoded token to see its structure
    print("Decoded Token:", decoded_token)

    return decoded_token

def get_user_info(access_token: str):
    url = f"https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com/oauth2/userInfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Unable to fetch user info from Cognito")

# Dependency function for token validation
def get_current_user_info(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization header format")
    token = authorization.split("Bearer ")[1]
    try:
        user_info = validate_jwt_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_info
