"""
Tests for items endpoints.
"""

from fastapi.testclient import TestClient


class TestItemsEndpoints:
    """Test class for items endpoints."""

    def test_get_items_endpoint(self, client: TestClient):
        """Test get all items endpoint."""
        response = client.get("/api/v1/items/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_item_by_id_endpoint(self, client: TestClient):
        """Test get item by ID endpoint."""
        item_id = 123
        response = client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert "item_id" in data
        assert "name" in data
        assert data["item_id"] == item_id
        assert data["name"] == f"Item {item_id}"

    def test_get_item_by_id_with_string_fails(self, client: TestClient):
        """Test get item by ID endpoint with string ID fails."""
        response = client.get("/api/v1/items/invalid_id")
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_endpoint(self, client: TestClient, sample_item_data):
        """Test create item endpoint."""
        response = client.post("/api/v1/items/", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data
        assert data["message"] == "Item created"
        assert data["data"] == sample_item_data

    def test_create_item_endpoint_empty_data(self, client: TestClient):
        """Test create item endpoint with empty data."""
        response = client.post("/api/v1/items/", json={})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data

    def test_update_item_endpoint(self, client: TestClient, sample_item_data):
        """Test update item endpoint."""
        item_id = 123
        response = client.put(f"/api/v1/items/{item_id}", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data
        assert data["message"] == f"Item {item_id} updated"
        assert data["data"] == sample_item_data

    def test_update_item_with_string_id_fails(
        self, client: TestClient, sample_item_data
    ):
        """Test update item endpoint with string ID fails."""
        response = client.put("/api/v1/items/invalid_id", json=sample_item_data)
        assert response.status_code == 422  # Unprocessable Entity

    def test_delete_item_endpoint(self, client: TestClient):
        """Test delete item endpoint."""
        item_id = 123
        response = client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == f"Item {item_id} deleted"

    def test_delete_item_with_string_id_fails(self, client: TestClient):
        """Test delete item endpoint with string ID fails."""
        response = client.delete("/api/v1/items/invalid_id")
        assert response.status_code == 422  # Unprocessable Entity
