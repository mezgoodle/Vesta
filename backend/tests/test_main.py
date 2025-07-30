"""
Tests for the main application endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    """Test class for main application endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to Vesta API"

    def test_health_check_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data

    def test_api_root_endpoint(self, client: TestClient):
        """Test the API v1 root endpoint."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["version"] == "1.0.0"

    def test_api_status_endpoint(self, client: TestClient):
        """Test the API v1 status endpoint."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "message" in data
