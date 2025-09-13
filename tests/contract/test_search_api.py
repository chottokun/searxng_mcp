import yaml
import pytest
from fastapi.testclient import TestClient
from openapi_schema_validator import validate
from jsonschema import RefResolver

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

def test_search_api_contract(client, openapi_spec, spec_resolver):
    """
    Validates the /search endpoint response against the OpenAPI contract.
    """
    # Arrange: Make a request to the endpoint
    response = client.get("/search?q=test")
    assert response.status_code == 200
    response_data = response.json()

    # Act: Get the schema for the response from the OpenAPI spec
    response_schema = openapi_spec["paths"]["/search"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    # Assert: Validate the response against the schema.
    # The resolver will correctly handle the $ref to #/components/schemas/ResultSet
    validate(instance=response_data, schema=response_schema, resolver=spec_resolver)

    # The previous validation already checks the nested SearchResult objects,
    # so we don't need to loop and validate them individually anymore.
    # The resolver handles the entire object graph.
