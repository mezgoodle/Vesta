"""
Tests for users endpoints.
"""

from fastapi.testclient import TestClient


class TestUsersEndpoints:
    """Test class for users endpoints."""

    def test_get_users_endpoint(self, client: TestClient):
        """Test get all users endpoint."""
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)

    def test_get_user_by_id_endpoint(self, client: TestClient):
        """Test get user by ID endpoint."""
        user_id = 123
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert data["user_id"] == user_id
        assert data["username"] == f"user_{user_id}"

    def test_get_user_by_id_with_string_fails(self, client: TestClient):
        """Test get user by ID endpoint with string ID fails."""
        response = client.get("/api/v1/users/invalid_id")
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_user_endpoint(self, client: TestClient, sample_user_data):
        """Test create user endpoint."""
        response = client.post("/api/v1/users/", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data
        assert data["message"] == "User created"
        assert data["data"] == sample_user_data

    def test_create_user_endpoint_empty_data(self, client: TestClient):
        """Test create user endpoint with empty data."""
        response = client.post("/api/v1/users/", json={})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data

    def test_update_user_endpoint(self, client: TestClient, sample_user_data):
        """Test update user endpoint."""
        user_id = 123
        response = client.put(f"/api/v1/users/{user_id}", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data
        assert data["message"] == f"User {user_id} updated"
        assert data["data"] == sample_user_data

    def test_update_user_with_string_id_fails(
        self, client: TestClient, sample_user_data
    ):
        """Test update user endpoint with string ID fails."""
        response = client.put("/api/v1/users/invalid_id", json=sample_user_data)
        assert response.status_code == 422  # Unprocessable Entity

    def test_delete_user_endpoint(self, client: TestClient):
        """Test delete user endpoint."""
        user_id = 123
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == f"User {user_id} deleted"

    def test_delete_user_with_string_id_fails(self, client: TestClient):
        """Test delete user endpoint with string ID fails."""
        response = client.delete("/api/v1/users/invalid_id")
        assert response.status_code == 422  # Unprocessable Entity
