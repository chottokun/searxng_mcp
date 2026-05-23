import pytest
from src.services.pii_service import PiiService
from src.schemas import ResultSet, SearchResult

@pytest.fixture
def pii_service():
    PiiService.reset()
    return PiiService()

def test_redact_api_keys_and_secrets(pii_service):
    # GitHub トークン
    assert pii_service.inspect_query("Fix ghp_abcdefghijklmnopqrstuvwxyz0123456789") == "Fix [REDACTED_TOKEN]"
    
    # OpenAI API キー
    assert pii_service.inspect_query("Use sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM") == "Use [REDACTED_KEY]"

def test_redact_credit_card(pii_service):
    # ハイフン区切り
    assert pii_service.inspect_query("Payment for 1234-5678-9012-3456") == "Payment for [REDACTED_CC]"
    # スペース区切り
    assert pii_service.inspect_query("Payment for 1234 5678 9012 3456") == "Payment for [REDACTED_CC]"
    # 区切りなし
    assert pii_service.inspect_query("Payment for 1234567890123456") == "Payment for [REDACTED_CC]"

def test_do_not_redact_invalid_credit_card(pii_service):
    # 桁数が足りない
    assert pii_service.inspect_query("Payment for 1234-5678-9012") == "Payment for 1234-5678-9012"
    # 数字以外が含まれている
    assert pii_service.inspect_query("Payment for 1234-56ab-9012-3456") == "Payment for 1234-56ab-9012-3456"

def test_redact_ipv4(pii_service):
    # 正常な IPv4 アドレス
    assert pii_service.inspect_query("Check status of 192.168.1.1") == "Check status of [REDACTED_IP]"
    assert pii_service.inspect_query("Connect to 127.0.0.1") == "Connect to [REDACTED_IP]"

def test_do_not_redact_invalid_ipv4(pii_service):
    # 範囲外の数値を含む無効な IPv4 (マスクされてはならない)
    assert pii_service.inspect_query("Check status of 999.999.999.999") == "Check status of 999.999.999.999"
    assert pii_service.inspect_query("Check status of 192.168.1.300") == "Check status of 192.168.1.300"
    assert pii_service.inspect_query("Check status of 256.0.0.1") == "Check status of 256.0.0.1"

def test_redact_ipv6_various_formats(pii_service):
    # フル形式の IPv6
    assert pii_service.inspect_query("Connect to 2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "Connect to [REDACTED_IP]"
    # 圧縮形式
    assert pii_service.inspect_query("Connect to 2001:db8::1") == "Connect to [REDACTED_IP]"
    # ループバック
    assert pii_service.inspect_query("Connect to ::1") == "Connect to [REDACTED_IP]"
    # 省略形式の末尾
    assert pii_service.inspect_query("Connect to 2001:db8::") == "Connect to [REDACTED_IP]"

def test_do_not_redact_invalid_ipv6(pii_service):
    # 5桁以上のヘキサセグメント (無効なIPv6)
    assert pii_service.inspect_query("Connect to 2001:db8888::1") == "Connect to 2001:db8888::1"

def test_mask_results(pii_service, mocker):
    # 検索結果のマスキング検証（明示的にTrueに設定）
    mocker.patch("src.services.pii_service.settings.PII_MASK_RESPONSE", True)
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
    assert masked.results[0].title == "My IP is [REDACTED_IP]"
    assert masked.results[0].content == "API Key [REDACTED_KEY] works"

def test_inspect_query_disabled(pii_service, mocker):
    """PII検出が無効な場合、クエリが変更されないことを検証します。"""
    mocker.patch("src.services.pii_service.settings.PII_DETECTION_ENABLED", False)
    query = "Contact john.doe@example.com"
    assert pii_service.inspect_query(query) == query

def test_inspect_query_off_level(pii_service, mocker):
    """PIIブロックレベルが'off'の場合、クエリが変更されないことを検証します。"""
    mocker.patch("src.services.pii_service.settings.PII_DETECTION_ENABLED", True)
    mocker.patch("src.services.pii_service.settings.PII_BLOCK_LEVEL", "off")
    query = "Contact john.doe@example.com"
    assert pii_service.inspect_query(query) == query

def test_mask_results_disabled(pii_service, mocker):
    """PII検出が無効な場合、検索結果がマスキングされないことを検証します。"""
    mocker.patch("src.services.pii_service.settings.PII_DETECTION_ENABLED", False)
    mock_results = ResultSet(
        query="test",
        number_of_results=1,
        results=[
            SearchResult(
                title="My email is john.doe@example.com",
                url="http://example.com",
                content="Call me at 090-1234-5678",
                engine="google"
            )
        ]
    )

    masked = pii_service.mask_results(mock_results)
    assert masked.results[0].title == "My email is john.doe@example.com"
    assert masked.results[0].content == "Call me at 090-1234-5678"

def test_mask_results_off_masking(pii_service, mocker):
    """レスポンスのマスキングが設定でオフの場合、検索結果がマスキングされないことを検証します。"""
    mocker.patch("src.services.pii_service.settings.PII_DETECTION_ENABLED", True)
    mocker.patch("src.services.pii_service.settings.PII_MASK_RESPONSE", False)
    mock_results = ResultSet(
        query="test",
        number_of_results=1,
        results=[
            SearchResult(
                title="My email is john.doe@example.com",
                url="http://example.com",
                content="Call me at 090-1234-5678",
                engine="google"
            )
        ]
    )

    masked = pii_service.mask_results(mock_results)
    assert masked.results[0].title == "My email is john.doe@example.com"
    assert masked.results[0].content == "Call me at 090-1234-5678"

