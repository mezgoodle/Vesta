"""
Tests for authentication endpoints.
"""

from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test class for authentication endpoints."""

    def test_login_endpoint(self, client: TestClient, sample_credentials):
        """Test user login endpoint."""
        response = client.post("/api/v1/auth/login", json=sample_credentials)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "token" in data
        assert data["message"] == "Login successful"

    def test_login_endpoint_empty_data(self, client: TestClient):
        """Test login endpoint with empty data."""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "token" in data

    def test_logout_endpoint(self, client: TestClient):
        """Test user logout endpoint."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Logout successful"

    def test_register_endpoint(self, client: TestClient, sample_user_data):
        """Test user registration endpoint."""
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data
        assert data["message"] == "User registered successfully"
        assert data["data"] == sample_user_data

    def test_register_endpoint_empty_data(self, client: TestClient):
        """Test registration endpoint with empty data."""
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data

    def test_get_current_user_endpoint(self, client: TestClient):
        """Test get current user endpoint."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"] == "current_user"
