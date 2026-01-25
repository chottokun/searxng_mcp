import pytest
import httpx
from fastapi.testclient import TestClient
from src.main import app
from src.schemas import ResultSet, SearchResult

@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    # Using the context manager ensures lifespan events are triggered
    with TestClient(app) as c:
        yield c

def test_searxng_unavailable(client, mocker):
    """
    Test the behavior when the SearXNG service is unavailable by mocking an httpx error.
    """
    # Arrange: Patch the AsyncClient.get method
    # Note: We need to patch where it's used or the class itself.
    # Since we use a single client in app.state, we can patch that instance's get.
    mock_get = mocker.patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("Mocked request error"))

    # Act
    response = client.get("/search?q=test")

    # Assert
    assert response.status_code == 503
    json_response = response.json()
    assert "detail" in json_response
    assert "SearXNG service request failed" in json_response["detail"]

def test_no_results_found(client, mocker):
    """
    Test the behavior when a search yields no results.
    """
    # Arrange
    query = "noresults"
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": query, "results": []}
    mock_response.raise_for_status.return_value = None

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act
    response = client.get(f"/search?q={query}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert data["number_of_results"] == 0
    assert data["results"] == []

def test_successful_search(client, mocker):
    """
    Test a successful search query.
    """
    # Arrange
    query = "python"
    mock_data = {
        "query": query,
        "results": [
            {
                "title": "Python.org",
                "url": "https://www.python.org/",
                "content": "The official home of the Python Programming Language",
                "engine": "google"
            }
        ]
    }
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mock_response.raise_for_status.return_value = None

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act
    response = client.get(f"/search?q={query}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    validated_data = ResultSet.model_validate(data)
    assert validated_data.query == query
    assert validated_data.number_of_results == 1
    assert validated_data.results[0].title == "Python.org"
