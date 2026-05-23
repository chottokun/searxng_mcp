import pytest
from src.services.pii_service import PiiService
from src.schemas import ResultSet, SearchResult

@pytest.fixture
def pii_service():
    return PiiService()

def test_mask_results_disabled_pii_detection(pii_service, mocker):
    mocker.patch("src.services.pii_service.settings.PII_DETECTION_ENABLED", False)

    mock_results = ResultSet(
        query="test",
        number_of_results=1,
        results=[
            SearchResult(
                title="My IP is 192.168.1.1",
                url="http://example.com",
                content="API Key sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM works",
                engine="google"
            )
        ]
    )

    masked = pii_service.mask_results(mock_results)
    assert masked.results[0].title == "My IP is 192.168.1.1"
    assert masked.results[0].content == "API Key sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM works"

def test_mask_results_disabled_mask_response(pii_service, mocker):
    mocker.patch("src.services.pii_service.settings.PII_MASK_RESPONSE", False)

    mock_results = ResultSet(
        query="test",
        number_of_results=1,
        results=[
            SearchResult(
                title="My IP is 192.168.1.1",
                url="http://example.com",
                content="API Key sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM works",
                engine="google"
            )
        ]
    )

    masked = pii_service.mask_results(mock_results)
    assert masked.results[0].title == "My IP is 192.168.1.1"
    assert masked.results[0].content == "API Key sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM works"

def test_inspect_query_disabled_pii_detection(pii_service, mocker):
    mocker.patch("src.services.pii_service.settings.PII_DETECTION_ENABLED", False)
    query = "Check sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM"
    assert pii_service.inspect_query(query) == query

def test_inspect_query_block_level_off(pii_service, mocker):
    mocker.patch("src.services.pii_service.settings.PII_BLOCK_LEVEL", "off")
    query = "Check sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM"
    assert pii_service.inspect_query(query) == query
