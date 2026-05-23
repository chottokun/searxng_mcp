import pytest
import httpx
from src.services.searxng_service import SearxngService, SearxngUnavailableError

@pytest.fixture
def searxng_service():
    return SearxngService()

@pytest.mark.anyio
async def test_search_params_q_only(searxng_service, mocker):
    # Arrange
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act
    await searxng_service.search(q="test", categories=None, time_range=None)

    # Assert
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json"}

@pytest.mark.anyio
async def test_search_params_with_categories(searxng_service, mocker):
    # Arrange
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act
    await searxng_service.search(q="test", categories="news,images", time_range=None)

    # Assert
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json", "categories": "news,images"}

@pytest.mark.anyio
async def test_search_params_with_time_range(searxng_service, mocker):
    # Arrange
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act
    await searxng_service.search(q="test", categories=None, time_range="day")

    # Assert
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json", "time_range": "day"}

@pytest.mark.anyio
async def test_search_params_with_all(searxng_service, mocker):
    # Arrange
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act
    await searxng_service.search(q="test", categories="science", time_range="month")

    # Assert
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {
        "q": "test",
        "format": "json",
        "categories": "science",
        "time_range": "month"
    }

@pytest.mark.anyio
async def test_search_http_status_error(searxng_service, mocker):
    # Arrange
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=mocker.Mock(), response=mocker.Mock()
    )
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act & Assert
    with pytest.raises(SearxngUnavailableError):
        await searxng_service.search(q="test", categories=None, time_range=None)

@pytest.mark.anyio
async def test_search_request_error(searxng_service, mocker):
    # Arrange
    mocker.patch(
        "httpx.AsyncClient.get", side_effect=httpx.RequestError("Error")
    )

    # Act & Assert
    with pytest.raises(SearxngUnavailableError):
        await searxng_service.search(q="test", categories=None, time_range=None)
