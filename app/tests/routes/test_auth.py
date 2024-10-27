from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user import NewUser
from app.db.database import get_db
from app.crud.user import get_user_by_cognito_id, create_user

client = TestClient(app)

# Mock function to simulate user token info
def mock_get_current_user_info():
    return {
        "cognito:username": "testuser",
        "email": "testuser@example.com",
        "sub": "f02c79fc-f021-706f-aee1-709122218560"
    }

# Test for successful login without an existing user
@patch("app.utils.cognito.validate_jwt_token", return_value=mock_get_current_user_info())
def test_login_success(mock_validate_token):
    print("Starting test_login_success")

    # Mocking the DB session
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None  # Simulate no user exists
    app.dependency_overrides[get_db] = lambda: mock_db
    
    app.dependency_overrides[create_user] = NewUser(username="testuser", email="testuser@example.com", cognito_id="cognito_id_123")

    # Send the test request to `/login`
    response = client.post(
        "/login",
        headers={"Authorization": "Bearer header.payload.signature"}
    )

    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "message": "Login successful",
        "user": {
            "username": "testuser",
            "email": "testuser@example.com"
        }
    }

    # Clear dependency overrides after the test
    app.dependency_overrides.clear()

# `/login` endpoint test for existing user
@patch("app.utils.cognito.validate_jwt_token", return_value=mock_get_current_user_info())
def test_login_user_already_exists(mock_validate_token):
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    
    app.dependency_overrides[get_user_by_cognito_id] = NewUser(
            cognito_id="cognito_id_123",
            username="existinguser",
            email="existinguser@example.com"
        ).model_dump()

    # Send request to `/login` with mock JWT
    response = client.post(
        "/login",
        headers={"Authorization": "Bearer header.payload.signature"}
    )

    # Assertions
    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}

    # Clear dependency overrides after the test
    app.dependency_overrides.clear()


# Test for the `/me` endpoint to successfully retrieve current user data
@patch("app.utils.cognito.validate_jwt_token", return_value=mock_get_current_user_info())
@patch("app.crud.user.get_user_by_cognito_id")
def test_get_current_user_success(mock_get_user_by_cognito_id, mock_validate_token):
    # Mock the database function to return the expected user
    mock_get_user_by_cognito_id.return_value = MagicMock(
        username="test_user",
        email="sct.saraalmeida@gmail.com",
        cognito_id="f02c79fc-f021-706f-aee1-709122218560"
    )

    # Send the test request to `/me`
    response = client.get("/me", headers={"Authorization": "Bearer header.payload.signature"})

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check the response JSON matches the expected user data
    assert response.json() == {# Patching at the module level
        "username": "test_user",
        "email": "sct.saraalmeida@gmail.com",
        "cognito_id": "f02c79fc-f021-706f-aee1-709122218560"
    }

# `/me` test for user not found scenario
@patch("app.utils.cognito.validate_jwt_token", return_value=mock_get_current_user_info())
@patch("app.crud.user.get_user_by_cognito_id", return_value=None) 
def test_get_current_user_not_found(mock_get_user_by_cognito_id, mock_validate_token):

    app.dependency_overrides[get_user_by_cognito_id] = lambda cognito_id, db: None
    # Make the request
    response = client.get("/me", headers={"Authorization": "Bearer header.payload.signature"})

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

    # Clear dependency overrides after the test
    del app.dependency_overrides[get_user_by_cognito_id]
    
# def test_logout():
#     response = client.get("/logout", follow_redirects=False)
#     assert response.status_code == 307
#     assert "https://yourcognito.auth.region.amazoncognito.com/logout" in response.headers["Location"]

