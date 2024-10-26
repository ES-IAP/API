import requests
from fastapi import HTTPException
from jose import jwt
from app.config import COGNITO_REGION, USER_POOL_ID, CLIENT_ID, COGNITO_DOMAIN

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

    # Decode the token without enforcing `at_hash` validation
    decoded_token = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=CLIENT_ID,
        issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}",
        options={"verify_at_hash": False}  # Disables the `at_hash` claim verification
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
