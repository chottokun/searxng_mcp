import pytest
import httpx
from fastapi.testclient import TestClient
from src.main import app
from src.schemas import ResultSet

@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    # The TestClient will trigger the lifespan events
    with TestClient(app) as c:
        yield c

def test_searxng_unavailable(client, mocker):
    """
    Test the behavior when the SearXNG service is unavailable by mocking an httpx error.
    """
    # Arrange
    # Mocking the client attached to app.state
    mocker.patch.object(
        app.state.client,
        "get",
        side_effect=httpx.RequestError("Mocked request error")
    )

    # Act
    response = client.get("/search?q=test")

    # Assert
    assert response.status_code == 503
    json_response = response.json()
    assert "detail" in json_response
    assert "SearXNG service is temporarily unavailable" in json_response["detail"]

def test_no_results_found(client, mocker):
    """
    Test the behavior when a search yields no results.
    """
    # Arrange
    query = "aquerythatshouldneverreturnanyresultsatallxyz123"
    empty_response = {"query": query, "results": []}

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = empty_response
    mock_response.raise_for_status.return_value = None

    mocker.patch.object(
        app.state.client,
        "get",
        return_value=mock_response
    )

    # Act
    response = client.get(f"/search?q={query}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert data["number_of_results"] == 0

def test_pii_redaction_integration(client, mocker):
    """
    Test that PII in the search query is redacted before being sent to SearXNG.
    """
    # Arrange
    query = "Find info about test@example.com"
    expected_sanitized_query = "Find info about [REDACTED_EMAIL]"

    # Mock response from SearXNG
    mock_response_data = {
        "query": expected_sanitized_query,
        "results": [
            {"title": "Result", "url": "http://example.com", "content": "Some content", "engine": "google"}
        ]
    }

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Patch the client.get to capture the parameters sent to SearXNG
    mock_get = mocker.patch.object(
        app.state.client,
        "get",
        return_value=mock_response
    )

    # Act
    response = client.get(f"/search?q={query}")

    # Assert
    assert response.status_code == 200

    # Verify that the query sent to SearXNG was sanitized
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["q"] == expected_sanitized_query

    # Verify the response contains the sanitized query
    data = response.json()
    assert data["query"] == expected_sanitized_query
