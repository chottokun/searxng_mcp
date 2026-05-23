import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c

def test_read_root(client):
    """
    Test the health check endpoint.
    """
    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
