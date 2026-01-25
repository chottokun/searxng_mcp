import pytest
import httpx
from src.services.searxng_service import SearxngService, SearxngUnavailableError
from src.schemas import ResultSet

@pytest.mark.anyio
async def test_search_success(mocker):
    # Arrange
    mock_client = mocker.Mock(spec=httpx.AsyncClient)
    mock_response = mocker.Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "query": "test",
        "results": [
            {"title": "Title", "url": "http://example.com", "content": "Content", "engine": "google"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    service = SearxngService(mock_client)

    # Act
    result = await service.search("test")

    # Assert
    assert isinstance(result, ResultSet)
    assert result.query == "test"
    assert result.number_of_results == 1
    assert result.results[0].title == "Title"

@pytest.mark.anyio
async def test_search_timeout(mocker):
    # Arrange
    mock_client = mocker.Mock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")

    service = SearxngService(mock_client)

    # Act & Assert
    with pytest.raises(SearxngUnavailableError) as excinfo:
        await service.search("test")
    assert "timed out" in str(excinfo.value)

@pytest.mark.anyio
async def test_search_http_error(mocker):
    # Arrange
    mock_client = mocker.Mock(spec=httpx.AsyncClient)
    mock_response = mocker.Mock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=mocker.Mock(), response=mock_response)
    mock_client.get.return_value = mock_response

    service = SearxngService(mock_client)

    # Act & Assert
    with pytest.raises(SearxngUnavailableError) as excinfo:
        await service.search("test")
    assert "returned an error status" in str(excinfo.value)

@pytest.mark.anyio
async def test_search_invalid_json(mocker):
    # Arrange
    mock_client = mocker.Mock(spec=httpx.AsyncClient)
    mock_response = mocker.Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response

    service = SearxngService(mock_client)

    # Act & Assert
    with pytest.raises(SearxngUnavailableError) as excinfo:
        await service.search("test")
    assert "invalid JSON response" in str(excinfo.value)

@pytest.mark.anyio
async def test_search_empty_query(mocker):
    # Arrange
    service = SearxngService(mocker.Mock())

    # Act
    result = await service.search("  ")

    # Assert
    assert result.number_of_results == 0
    assert result.results == []
