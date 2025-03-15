"""Test cases for the API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_start_analysis() -> None:
    """Test the start analysis endpoint."""
    response = client.post(
        "/analyze/start", json={"repo_url": "https://github.com/example/repo"}
    )
    assert response.status_code == 200
    assert "job_id" in response.json()


def test_get_job_status_not_found() -> None:
    """Test getting status of non-existent job."""
    response = client.get("/analyze/status/nonexistent")
    assert response.status_code == 404


def test_analyze_function_not_found() -> None:
    """Test analyzing non-existent function."""
    response = client.post(
        "/analyze/function", json={"job_id": "nonexistent", "function_name": "test"}
    )
    assert response.status_code == 404
