import pytest
from fastapi import HTTPException, Depends, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.utils.cognito import validate_jwt_token, get_user_info, get_current_user_info
from app.config import CLIENT_ID, COGNITO_REGION, USER_POOL_ID

# Mock FastAPI app and route for testing
app = FastAPI()

# Add a protected route for testing
@app.get("/some-protected-route", dependencies=[Depends(get_current_user_info)])
def protected_route():
    return {"message": "Protected content"}

client = TestClient(app)

# Replace these with actual values from your configuration
ACTUAL_CLIENT_ID = CLIENT_ID
ACTUAL_ISSUER_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"

# Mock data
MOCK_TOKEN = "header.payload.signature"  # Token with three segments to prevent structure errors
MOCK_ACCESS_TOKEN = "mock_access_token"
MOCK_PUBLIC_KEYS = [{"kid": "mock_kid", "kty": "RSA", "alg": "RS256"}]
MOCK_USER_INFO = {"sub": "1234567890", "name": "Test User"}

MOCK_DECODED_TOKEN = {"sub": "1234567890", "name": "Test User"}

@pytest.fixture
def mock_public_keys():
    return MOCK_PUBLIC_KEYS

@pytest.fixture
def mock_user_info():
    return MOCK_USER_INFO

# @patch("app.utils.cognito.requests.get")
# def test_get_cognito_public_keys(mock_get):
#     mock_get.return_value.json.return_value = {"keys": MOCK_PUBLIC_KEYS}
#     from app.utils.cognito import get_cognito_public_keys
#     keys = get_cognito_public_keys()
#     assert keys == MOCK_PUBLIC_KEYS
#     mock_get.assert_called_once()


# Test validate_jwt_token function with mocked dependencies
# Test validate_jwt_token function with mocked dependencies
@patch("app.utils.cognito.public_keys", MOCK_PUBLIC_KEYS)
@patch("app.utils.cognito.jwt.decode")
@patch("app.utils.cognito.jwt.get_unverified_headers")
def test_validate_jwt_token(mock_get_unverified_headers, mock_decode):
    # Mock the unverified headers to return a specific "kid" value
    mock_get_unverified_headers.return_value = {"kid": "mock_kid"}
    
    # Mock the decode function to return a valid decoded token structure
    mock_decode.return_value = MOCK_DECODED_TOKEN

    # Call the function to test with the mocked token
    decoded_token = validate_jwt_token(MOCK_TOKEN)

    # Assertions to verify that the mocked functions were called and returned expected values
    assert decoded_token == MOCK_DECODED_TOKEN
    mock_get_unverified_headers.assert_called_once_with(MOCK_TOKEN)
    mock_decode.assert_called_once_with(
        MOCK_TOKEN,
        MOCK_PUBLIC_KEYS[0],
        algorithms=["RS256"],
        audience=ACTUAL_CLIENT_ID,  # Use actual CLIENT_ID
        issuer=ACTUAL_ISSUER_URL,  # Use actual issuer URL
        options={"verify_at_hash": False}
    )
@patch("app.utils.cognito.requests.get")
def test_get_user_info(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_USER_INFO
    user_info = get_user_info(MOCK_ACCESS_TOKEN)
    assert user_info == MOCK_USER_INFO
    mock_get.assert_called_once()

def test_get_current_user_info_valid():
    with patch("app.utils.cognito.validate_jwt_token", return_value=MOCK_USER_INFO):
        response = client.get("/some-protected-route", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json() == {"message": "Protected content"}

def test_get_current_user_info_invalid_header():
    response = client.get("/some-protected-route", headers={"Authorization": "InvalidToken"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Authorization header format"}

def test_get_current_user_info_invalid_token():
    with patch("app.utils.cognito.validate_jwt_token", side_effect=ValueError("Invalid token")):
        response = client.get("/some-protected-route", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid token"}
