import pytest
import httpx
from fastapi.testclient import TestClient
from src.main import app
from src.schemas import ResultSet

@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c

def test_searxng_unavailable(client, mocker):
    """
    Test the behavior when the SearXNG service is unavailable by mocking an httpx error.
    """
    # Arrange
    mocker.patch(
        "httpx.AsyncClient.get",
        side_effect=httpx.RequestError("Mocked request error")
    )

    # Act
    response = client.get("/search?q=test")

    # Assert
    assert response.status_code == 503
    json_response = response.json()
    assert "detail" in json_response
    assert "SearXNG service is unavailable" in json_response["detail"]

def test_no_results_found(client, mocker):
    """
    Test the behavior when a search yields no results.
    This test mocks the service to ensure a predictable empty result.
    """
    # Arrange
    query = "aquerythatshouldneverreturnanyresultsatallxyz123"
    empty_result_set = ResultSet(query=query, number_of_results=0, results=[])
    mocker.patch(
        "src.services.searxng_service.SearxngService.search",
        return_value=empty_result_set
    )

    # Act
    response = client.get(f"/search?q={query}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data == empty_result_set.model_dump()

def test_successful_search(client):
    """
    Test a successful search query against the live service.
    This test checks for a valid response structure, not specific content.
    """
    # Arrange
    query = "python"

    # Act
    response = client.get(f"/search?q={query}")

    # Assert
    assert response.status_code == 200

    # Validate the response against the Pydantic model
    data = response.json()
    validated_data = ResultSet.model_validate(data)

    assert validated_data.query == query
    # We can't guarantee results, but it's highly likely for a common query
    if validated_data.number_of_results > 0:
        assert len(validated_data.results) == validated_data.number_of_results

        # Check the structure of the first result
        first_result = validated_data.results[0]
        assert isinstance(first_result.title, str)
        assert first_result.title is not None and first_result.title != ""
        assert isinstance(first_result.url, str)
        assert first_result.url.startswith("http")
        # Content can sometimes be None, so we don't assert its type strictly
        assert isinstance(first_result.engine, str)
