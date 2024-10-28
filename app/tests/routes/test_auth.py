import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app  # Replace with the actual import path for your FastAPI instance

client = TestClient(app)

# Test /login endpoint without following redirects
def test_login_redirect():
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 307
    assert "amazoncognito.com/login?" in response.headers["location"]

# Test /auth/callback with successful token exchange
@patch("app.routes.auth.requests.post")
@patch("app.routes.auth.jwt.get_unverified_claims")
@patch("app.routes.auth.get_user_by_cognito_id")
@patch("app.routes.auth.create_user")
def test_auth_callback_success(
    mock_create_user, mock_get_user_by_cognito_id, mock_get_unverified_claims, mock_requests_post
):
    mock_requests_post.return_value = Mock(status_code=200, json=lambda: {
        "id_token": "mock_id_token",
        "access_token": "mock_access_token"
    })
    mock_get_unverified_claims.return_value = {
        "sub": "test_cognito_id",
        "cognito:username": "testuser",
        "email": "testuser@example.com"
    }
    mock_get_user_by_cognito_id.return_value = None
    mock_create_user.return_value = Mock(
        cognito_id="test_cognito_id", username="testuser", email="testuser@example.com"
    )

    response = client.get("/auth/callback", params={"code": "mock_code"})
    assert response.status_code == 200
    assert response.json() == {"message": "User successfully logged in"}
    assert response.cookies.get("access_token") == "mock_access_token"

# Test /auth/callback with missing authorization code
def test_auth_callback_missing_code():
    response = client.get("/auth/callback")
    assert response.status_code == 400
    assert response.json() == {"detail": "Authorization code not provided"}

# # Test /me endpoint with valid user info
# @patch("app.utils.cognito.get_current_user_info", return_value={"sub": "test_cognito_id"})
# @patch("app.crud.user.get_user_by_cognito_id")
# def test_get_current_user_success(mock_get_user_by_cognito_id, mock_get_current_user_info):
#     mock_get_user_by_cognito_id.return_value = Mock(
#         username="testuser", email="testuser@example.com", cognito_id="test_cognito_id"
#     )

#     client.cookies.set("access_token", "mock_access_token")
#     response = client.get("/me", headers={"Authorization": "Bearer mock_access_token"})
    
#     assert response.status_code == 200
#     assert response.json() == {
#         "username": "testuser",
#         "email": "testuser@example.com",
#         "cognito_id": "test_cognito_id"
#     }

# # Test /me endpoint with missing cognito_id in token
# @patch("app.utils.cognito.get_current_user_info", return_value={})
# def test_get_current_user_missing_cognito_id(mock_get_current_user_info):
#     client.cookies.set("access_token", "mock_access_token")
#     response = client.get("/me", headers={"Authorization": "Bearer mock_access_token"})
    
#     assert response.status_code == 500
#     assert response.json() == {"detail": "Cognito ID is missing in token"}

# # Test /me endpoint when user is not found
# @patch("app.utils.cognito.get_current_user_info", return_value={"sub": "test_cognito_id"})
# @patch("app.crud.user.get_user_by_cognito_id", return_value=None)
# def test_get_current_user_user_not_found(mock_get_user_by_cognito_id, mock_get_current_user_info):
#     client.cookies.set("access_token", "mock_access_token")
#     response = client.get("/me", headers={"Authorization": "Bearer mock_access_token"})
    
#     assert response.status_code == 404
#     assert response.json() == {"detail": "User not found"}