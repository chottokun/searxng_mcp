import pytest
from src.services.privacy_service import PrivacyService

@pytest.fixture
def privacy_service():
    return PrivacyService()

def test_redact_email(privacy_service):
    query = "Search for user@example.com"
    expected = "Search for [REDACTED_EMAIL]"
    assert privacy_service.redact_query(query) == expected

def test_redact_ipv4(privacy_service):
    query = "Check status of 192.168.1.1"
    expected = "Check status of [REDACTED_IP]"
    assert privacy_service.redact_query(query) == expected

def test_redact_ipv6_full(privacy_service):
    query = "Connect to 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    expected = "Connect to [REDACTED_IP]"
    assert privacy_service.redact_query(query) == expected

def test_redact_ipv6_compressed(privacy_service):
    query = "Connect to 2001:db8::1"
    expected = "Connect to [REDACTED_IP]"
    assert privacy_service.redact_query(query) == expected

def test_redact_credit_card(privacy_service):
    query = "Payment for 1234-5678-9012-3456"
    expected = "Payment for [REDACTED_CC]"
    assert privacy_service.redact_query(query) == expected

def test_redact_github_token(privacy_service):
    query = "Fix ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    expected = "Fix [REDACTED_TOKEN]"
    assert privacy_service.redact_query(query) == expected

def test_redact_openai_key(privacy_service):
    query = "Use sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM"
    expected = "Use [REDACTED_KEY]"
    assert privacy_service.redact_query(query) == expected

def test_multiple_pii(privacy_service):
    query = "Email test@test.com and IP 127.0.0.1"
    expected = "Email [REDACTED_EMAIL] and IP [REDACTED_IP]"
    assert privacy_service.redact_query(query) == expected

def test_no_pii(privacy_service):
    query = "What is the capital of France?"
    assert privacy_service.redact_query(query) == query

def test_empty_query(privacy_service):
    assert privacy_service.redact_query("") == ""
    assert privacy_service.redact_query(None) is None
