"""
Integration tests for the API.
"""

from fastapi.testclient import TestClient


class TestAPIIntegration:
    """Integration tests for the entire API."""

    def test_full_user_workflow(self, client: TestClient):
        """Test a complete user workflow: register -> login -> get profile."""
        # Register a new user
        user_data = {
            "username": "integration_user",
            "email": "integration@example.com",
            "password": "integration123",
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200

        # Login with the user
        credentials = {"username": "integration_user", "password": "integration123"}

        login_response = client.post("/api/v1/auth/login", json=credentials)
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "token" in login_data

        # Get current user profile
        profile_response = client.get("/api/v1/auth/me")
        assert profile_response.status_code == 200

    def test_full_item_crud_workflow(self, client: TestClient):
        """Test a complete CRUD workflow for items."""
        # Create an item
        item_data = {
            "name": "Integration Item",
            "description": "Item for integration testing",
            "price": 99.99,
        }

        create_response = client.post("/api/v1/items/", json=item_data)
        assert create_response.status_code == 200

        # Get all items
        list_response = client.get("/api/v1/items/")
        assert list_response.status_code == 200

        # Get specific item
        item_id = 1
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 200

        # Update the item
        updated_data = {
            "name": "Updated Integration Item",
            "description": "Updated description",
            "price": 149.99,
        }

        update_response = client.put(f"/api/v1/items/{item_id}", json=updated_data)
        assert update_response.status_code == 200

        # Delete the item
        delete_response = client.delete(f"/api/v1/items/{item_id}")
        assert delete_response.status_code == 200

    def test_api_endpoints_accessibility(self, client: TestClient):
        """Test that all main API endpoints are accessible."""
        # Root endpoints
        assert client.get("/").status_code == 200
        assert client.get("/health").status_code == 200

        # API v1 endpoints
        assert client.get("/api/v1/").status_code == 200
        assert client.get("/api/v1/status").status_code == 200

        # Auth endpoints
        assert client.post("/api/v1/auth/login", json={}).status_code == 200
        assert client.post("/api/v1/auth/logout").status_code == 200
        assert client.post("/api/v1/auth/register", json={}).status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 200

        # Items endpoints
        assert client.get("/api/v1/items/").status_code == 200
        assert client.get("/api/v1/items/1").status_code == 200
        assert client.post("/api/v1/items/", json={}).status_code == 200
        assert client.put("/api/v1/items/1", json={}).status_code == 200
        assert client.delete("/api/v1/items/1").status_code == 200

        # Users endpoints
        assert client.get("/api/v1/users/").status_code == 200
        assert client.get("/api/v1/users/1").status_code == 200
        assert client.post("/api/v1/users/", json={}).status_code == 200
        assert client.put("/api/v1/users/1", json={}).status_code == 200
        assert client.delete("/api/v1/users/1").status_code == 200

    def test_invalid_endpoints_return_404(self, client: TestClient):
        """Test that invalid endpoints return 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        response = client.get("/api/v2/items/")
        assert response.status_code == 404

        response = client.post("/api/v1/invalid/endpoint")
        assert response.status_code == 404
