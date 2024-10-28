import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from jose import JWTError
from app.utils.cognito import validate_jwt_token, get_current_user_info

# Sample public keys and token for testing
SAMPLE_PUBLIC_KEYS = [
    {
        "kid": "sample_kid",
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": "sample_n_value",
        "e": "AQAB"
    }
]

SAMPLE_TOKEN_HEADERS = {
    "kid": "sample_kid"
}

SAMPLE_DECODED_TOKEN = {
    "sub": "sample_user_id",
    "aud": "sample_client_id",
    "iss": "https://cognito-idp.sample-region.amazonaws.com/sample_user_pool_id",
    "username": "sample_user"
}

CLIENT_ID = "sample_client_id"
USER_POOL_ID = "sample_user_pool_id"
COGNITO_REGION = "sample-region"

@patch("app.utils.cognito.public_keys", SAMPLE_PUBLIC_KEYS)
@patch("app.utils.cognito.jwt.get_unverified_headers")
@patch("app.utils.cognito.jwt.decode")
def test_validate_jwt_token(mock_decode, mock_get_unverified_headers):
    # Mocking to return sample token headers and decoded token
    mock_get_unverified_headers.return_value = SAMPLE_TOKEN_HEADERS
    mock_decode.return_value = SAMPLE_DECODED_TOKEN

    sample_token = "sample.jwt.token"
    decoded_token = validate_jwt_token(sample_token)

    assert decoded_token == SAMPLE_DECODED_TOKEN
    
@patch("app.utils.cognito.jwt.decode", side_effect=JWTError("Error decoding token"))
@patch("app.utils.cognito.jwt.get_unverified_headers", return_value={"kid": "sample_kid"})
@patch("app.utils.cognito.public_keys", SAMPLE_PUBLIC_KEYS)
def test_validate_jwt_token_invalid_token(mock_get_unverified_headers, mock_decode):
    with pytest.raises(HTTPException) as exc_info:
        validate_jwt_token("invalid.jwt.token")
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token is invalid"

@patch("app.utils.cognito.validate_jwt_token")
def test_get_current_user_info(mock_validate_jwt_token):
    # Mock the validate_jwt_token to return the sample decoded token
    mock_validate_jwt_token.return_value = SAMPLE_DECODED_TOKEN

    access_token = "sample.jwt.token"
    user_info = get_current_user_info(access_token=access_token)

    assert user_info == SAMPLE_DECODED_TOKEN
    mock_validate_jwt_token.assert_called_once_with(access_token)

def test_get_current_user_info_no_token():
    # Test with no token provided, expecting a 401 Unauthorized error
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_info(access_token=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token not provided"
