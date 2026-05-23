import yaml
import pytest
from fastapi.testclient import TestClient
from openapi_schema_validator import validate
from jsonschema import RefResolver
import httpx

from src.main import app

@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def openapi_spec():
    """Load the OpenAPI specification."""
    with open("specs/001-searxng-mcp/contracts/api.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def spec_resolver(openapi_spec):
    """Create a resolver for the OpenAPI spec."""
    return RefResolver.from_schema(openapi_spec)

def test_search_api_contract(client, openapi_spec, spec_resolver, mocker):
    """
    Validates the /search endpoint response against the OpenAPI contract.
    """
    # Arrange: Mock SearXNG response to avoid 503 since no live SearXNG exists in the test env
    mock_response_data = {
        "query": "test",
        "number_of_results": 1,
        "results": [
            {"title": "Test", "url": "http://test.com", "content": "Test content", "engine": "google"}
        ]
    }

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    mocker.patch.object(
        app.state.client,
        "get",
        return_value=mock_response
    )

    # Act: Make a request to the endpoint
    response = client.get("/search?q=test")
    assert response.status_code == 200
    response_data = response.json()

    # Get the schema for the response from the OpenAPI spec
    response_schema = openapi_spec["paths"]["/search"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    # Assert: Validate the response against the schema.
    validate(instance=response_data, schema=response_schema, resolver=spec_resolver)
