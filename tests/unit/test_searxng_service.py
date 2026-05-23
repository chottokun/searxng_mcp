import pytest
import httpx
from src.services.searxng_service import SearxngService, SearxngUnavailableError

@pytest.fixture
def searxng_service():
    """テスト用のSearxngServiceインスタンスを提供するフィクスチャ。"""
    client = httpx.AsyncClient(base_url="http://localhost:8080", timeout=10.0)
    return SearxngService(client=client)

@pytest.mark.anyio
async def test_search_params_q_only(searxng_service, mocker):
    """クエリパラメータqのみを指定した場合の検索パラメータを検証します。"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await searxng_service.search(q="test", categories=None, time_range=None)

    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json"}

@pytest.mark.anyio
async def test_search_params_with_categories(searxng_service, mocker):
    """categoriesパラメータが正しく渡されることを検証します。"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await searxng_service.search(q="test", categories="news,images", time_range=None)

    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json", "categories": "news,images"}

@pytest.mark.anyio
async def test_search_params_with_time_range(searxng_service, mocker):
    """time_rangeパラメータが正しく渡されることを検証します。"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await searxng_service.search(q="test", categories=None, time_range="day")

    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "test", "format": "json", "time_range": "day"}

@pytest.mark.anyio
async def test_search_params_with_all(searxng_service, mocker):
    """すべてのパラメータ（q, categories, time_range）が正しく渡されることを検証します。"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [], "query": "test"}
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await searxng_service.search(q="test", categories="science", time_range="month")

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
    """HTTPステータスエラー時にSearxngUnavailableErrorが発生することを検証します。"""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=mocker.Mock(), response=mocker.Mock()
    )
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    with pytest.raises(SearxngUnavailableError):
        await searxng_service.search(q="test", categories=None, time_range=None)

@pytest.mark.anyio
async def test_search_request_error(searxng_service, mocker):
    """ネットワーク接続エラー時にSearxngUnavailableErrorが発生することを検証します。"""
    mocker.patch(
        "httpx.AsyncClient.get", side_effect=httpx.RequestError("Error")
    )

    with pytest.raises(SearxngUnavailableError):
        await searxng_service.search(q="test", categories=None, time_range=None)
