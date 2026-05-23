import pytest
import httpx
from src.services.searxng_service import SearxngService, SearxngUnavailableError

@pytest.fixture
def searxng_service():
    return SearxngService()

@pytest.mark.anyio
async def test_search_params_only_q(searxng_service, mocker):
    # Mock response
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": "test", "results": []}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch.object(httpx.AsyncClient, "get", return_value=mock_response)

    await searxng_service.search(q="test", categories=None, time_range=None)

    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json"}

@pytest.mark.anyio
async def test_search_params_with_categories(searxng_service, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": "test", "results": []}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch.object(httpx.AsyncClient, "get", return_value=mock_response)

    await searxng_service.search(q="test", categories="news,files", time_range=None)

    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json", "categories": "news,files"}

@pytest.mark.anyio
async def test_search_params_with_time_range(searxng_service, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": "test", "results": []}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch.object(httpx.AsyncClient, "get", return_value=mock_response)

    await searxng_service.search(q="test", categories=None, time_range="day")

    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json", "time_range": "day"}

@pytest.mark.anyio
async def test_search_params_all(searxng_service, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": "test", "results": []}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch.object(httpx.AsyncClient, "get", return_value=mock_response)

    await searxng_service.search(q="test", categories="news", time_range="month")

    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {
        "q": "test",
        "format": "json",
        "categories": "news",
        "time_range": "month"
    }

@pytest.mark.anyio
async def test_search_raises_unavailable_on_request_error(searxng_service, mocker):
    mocker.patch.object(httpx.AsyncClient, "get", side_effect=httpx.RequestError("error"))

    with pytest.raises(SearxngUnavailableError):
        await searxng_service.search(q="test", categories=None, time_range=None)

@pytest.mark.anyio
async def test_search_raises_unavailable_on_http_error(searxng_service, mocker):
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=mocker.Mock(), response=mocker.Mock())
    mocker.patch.object(httpx.AsyncClient, "get", return_value=mock_response)

    with pytest.raises(SearxngUnavailableError):
        await searxng_service.search(q="test", categories=None, time_range=None)
