import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock
from app.main import app
from app.db.database import Base, get_db

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Set up test client
client = TestClient(app)

# Use SQLite in-memory database for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for testing
def override_get_db():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test registration endpoint
@patch("boto3.client")
def test_register_user(mock_boto_client):
    mocked_client = MagicMock()
    mock_boto_client.return_value = mocked_client
    mocked_client.sign_up.return_value = {"UserSub": "test_user_sub"}
    
    response = client.post("/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password123!"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

# Test login endpoint with JWT validation mock
@patch("app.utils.cognito.validate_jwt_token")
def test_login_user(mock_validate_jwt):
    # Mock token validation to return dummy user info
    mock_validate_jwt.return_value = {
        "cognito:username": "testuser",
        "email": "testuser@example.com",
        "sub": "test_cognito_id"
    }

    response = client.post("/login", headers={"Authorization": "Bearer test_token"})
    
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
    assert response.json()["user"]["username"] == "testuser"
    assert response.json()["user"]["email"] == "testuser@example.com"

# Test logout endpoint to handle redirects
@patch("app.routes.auth.RedirectResponse")
def test_logout(mock_redirect_response):
    # Mock RedirectResponse and URL
    mock_redirect_response.return_value = MagicMock(status_code=200, url="https://yourcognitodomain.com/logout")
    
    response = client.get("/logout")
    
    # Validate that the mock redirect was invoked correctly
    mock_redirect_response.assert_called_once()
    assert response.status_code == 200
    redirect_url = mock_redirect_response.return_value.url
    assert redirect_url.startswith("https://")
