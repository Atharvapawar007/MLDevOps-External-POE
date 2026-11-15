"""
test_api.py - Pytest integration tests for FastAPI addition endpoints.
"""

import unittest

# Check if pytest is available
try:
    import pytest
except ImportError:
    pytest = None

# Check if fastapi and starlette/httpx are available for TestClient
try:
    from fastapi.testclient import TestClient
    from src.app import app
    client = TestClient(app)
    HAS_FASTAPI_TESTCLIENT = True
except (ImportError, Exception):
    HAS_FASTAPI_TESTCLIENT = False
    client = None


@unittest.skipIf(not HAS_FASTAPI_TESTCLIENT, "fastapi / httpx not installed in test environment")
class TestFastAPIEndpoints(unittest.TestCase):
    """Test suite for FastAPI endpoints."""

    def test_root_endpoint(self):
        """Test GET / returns welcoming metadata and status 200."""
        response = client.get("/")
        assert response.status_code == 200
        payload = response.json()
        assert "message" in payload
        assert "documentation" in payload
        assert payload["health"] == "/health"

    def test_health_check_endpoint(self):
        """Test GET /health returns status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["service"] == "Addition MLOps API"
        assert "timestamp" in payload

    def test_post_add_valid_numbers(self):
        """Test POST /api/v1/add with valid float numbers."""
        response = client.post(
            "/api/v1/add",
            json={"num1": 25.5, "num2": 14.5},
            params={"log_data": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["num1"] == 25.5
        assert data["num2"] == 14.5
        assert data["result"] == 40.0
        assert data["operation"] == "addition"
        assert "timestamp" in data

    def test_post_add_negative_and_zero(self):
        """Test POST /api/v1/add with negative numbers and zero."""
        response = client.post(
            "/api/v1/add",
            json={"num1": -15.0, "num2": 15.0},
            params={"log_data": False}
        )
        assert response.status_code == 200
        assert response.json()["result"] == 0.0

    def test_post_add_invalid_input_type(self):
        """Test POST /api/v1/add with invalid string payload triggers 422 validation error."""
        response = client.post(
            "/api/v1/add",
            json={"num1": "not-a-number", "num2": 10},
            params={"log_data": False}
        )
        assert response.status_code == 422

    def test_post_add_missing_field(self):
        """Test POST /api/v1/add with missing required field triggers 422."""
        response = client.post(
            "/api/v1/add",
            json={"num1": 10},
            params={"log_data": False}
        )
        assert response.status_code == 422

    def test_get_add_valid_params(self):
        """Test GET /api/v1/add query parameters."""
        response = client.get("/api/v1/add?num1=33&num2=67&log_data=false")
        assert response.status_code == 200
        data = response.json()
        assert data["num1"] == 33.0
        assert data["num2"] == 67.0
        assert data["result"] == 100.0

    def test_get_add_missing_params(self):
        """Test GET /api/v1/add missing query parameter triggers 422."""
        response = client.get("/api/v1/add?num1=33")
        assert response.status_code == 422

    def test_batch_add(self):
        """Test POST /api/v1/add/batch with multiple items."""
        batch_payload = {
            "items": [
                {"num1": 1.0, "num2": 2.0},
                {"num1": 10.0, "num2": 20.0},
                {"num1": -5.0, "num2": -5.0}
            ]
        }
        response = client.post("/api/v1/add/batch", json=batch_payload, params={"log_data": False})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3
        assert data["results"][0]["result"] == 3.0
        assert data["results"][1]["result"] == 30.0
        assert data["results"][2]["result"] == -10.0
