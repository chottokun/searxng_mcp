import pytest
from src.services.privacy_service import PrivacyService

@pytest.fixture
def privacy_service():
    return PrivacyService()

def test_redact_email(privacy_service):
    # 基本パターン
    assert privacy_service.redact_query("Search for user@example.com") == "Search for [REDACTED_EMAIL]"
    # 大文字・記号・サブドメインを含む複雑なパターン
    assert privacy_service.redact_query("Contact TEST.user+label@Sub-Domain.example.co.jp") == "Contact [REDACTED_EMAIL]"

def test_redact_ipv4(privacy_service):
    # 正常な IPv4 アドレス
    assert privacy_service.redact_query("Check status of 192.168.1.1") == "Check status of [REDACTED_IP]"
    assert privacy_service.redact_query("Connect to 127.0.0.1") == "Connect to [REDACTED_IP]"
    assert privacy_service.redact_query("Public IP is 8.8.8.8") == "Public IP is [REDACTED_IP]"

def test_do_not_redact_invalid_ipv4(privacy_service):
    # 範囲外の数値を含む無効な IPv4 (マスクされてはならない)
    assert privacy_service.redact_query("Check status of 999.999.999.999") == "Check status of 999.999.999.999"
    assert privacy_service.redact_query("Check status of 192.168.1.300") == "Check status of 192.168.1.300"
    assert privacy_service.redact_query("Check status of 256.0.0.1") == "Check status of 256.0.0.1"
    # フォーマットが不完全なIP
    assert privacy_service.redact_query("Check status of 192.168.1") == "Check status of 192.168.1"

def test_redact_ipv6_various_formats(privacy_service):
    # フル形式の IPv6
    assert privacy_service.redact_query("Connect to 2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "Connect to [REDACTED_IP]"
    # 圧縮形式
    assert privacy_service.redact_query("Connect to 2001:db8::1") == "Connect to [REDACTED_IP]"
    # ループバック
    assert privacy_service.redact_query("Connect to ::1") == "Connect to [REDACTED_IP]"
    # 省略形式の末尾
    assert privacy_service.redact_query("Connect to 2001:db8::") == "Connect to [REDACTED_IP]"

def test_do_not_redact_invalid_ipv6(privacy_service):
    # 5桁以上のヘキサセグメント (無効なIPv6)
    assert privacy_service.redact_query("Connect to 2001:db8888::1") == "Connect to 2001:db8888::1"
    # コロンが3つ連続する無効な形式
    assert privacy_service.redact_query("Connect to 2001:db8:::1") == "Connect to 2001:db8:::1"

def test_redact_credit_card(privacy_service):
    # ハイフン区切り
    assert privacy_service.redact_query("Payment for 1234-5678-9012-3456") == "Payment for [REDACTED_CC]"
    # スペース区切り
    assert privacy_service.redact_query("Payment for 1234 5678 9012 3456") == "Payment for [REDACTED_CC]"
    # 区切りなし
    assert privacy_service.redact_query("Payment for 1234567890123456") == "Payment for [REDACTED_CC]"

def test_do_not_redact_invalid_credit_card(privacy_service):
    # 桁数が足りない
    assert privacy_service.redact_query("Payment for 1234-5678-9012") == "Payment for 1234-5678-9012"
    # 数字以外が含まれている
    assert privacy_service.redact_query("Payment for 1234-56ab-9012-3456") == "Payment for 1234-56ab-9012-3456"

def test_redact_github_token(privacy_service):
    assert privacy_service.redact_query("Fix ghp_abcdefghijklmnopqrstuvwxyz0123456789") == "Fix [REDACTED_TOKEN]"

def test_redact_openai_key(privacy_service):
    assert privacy_service.redact_query("Use sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM") == "Use [REDACTED_KEY]"

def test_multiple_pii(privacy_service):
    query = "Email test@test.com and IP 127.0.0.1 and CC 1234-5678-9012-3456"
    expected = "Email [REDACTED_EMAIL] and IP [REDACTED_IP] and CC [REDACTED_CC]"
    assert privacy_service.redact_query(query) == expected

def test_no_pii(privacy_service):
    query = "What is the capital of France?"
    assert privacy_service.redact_query(query) == query

def test_empty_query(privacy_service):
    assert privacy_service.redact_query("") == ""
    assert privacy_service.redact_query(None) is None
