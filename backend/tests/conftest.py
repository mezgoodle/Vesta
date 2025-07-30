"""
Test configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {"name": "Test Item", "description": "This is a test item", "price": 29.99}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def sample_credentials():
    """Sample login credentials for testing."""
    return {"username": "testuser", "password": "testpassword123"}
