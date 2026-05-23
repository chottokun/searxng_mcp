import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.config import settings
from src.schemas import ResultSet, SearchResult

@pytest.fixture
def client():
    """FastAPIのテストクライアントを提供するフィクスチャ。"""
    with TestClient(app) as c:
        yield c

def test_pii_blocking_email(client, mocker):
    """メールアドレスを含むクエリがblock設定で適切に拒否されることをテストします。"""
    # 設定を上書きして検証
    mocker.patch.object(settings, "PII_DETECTION_ENABLED", True)
    mocker.patch.object(settings, "PII_BLOCK_LEVEL", "block")

    response = client.get("/search?q=my email is john.doe@example.com")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "送信不可能な個人情報または機密ワードがクエリ内に検出されたため" in detail
    assert "EMAIL_ADDRESS" in detail

def test_pii_blocking_jp_phone(client, mocker):
    """日本の電話番号を含むクエリがblock設定で適切に拒否されることをテストします。"""
    mocker.patch.object(settings, "PII_DETECTION_ENABLED", True)
    mocker.patch.object(settings, "PII_BLOCK_LEVEL", "block")

    # 携帯電話のパターン
    response = client.get("/search?q=電話番号は 090-1234-5678 です")
    assert response.status_code == 400
    assert "PHONE_NUMBER" in response.json()["detail"]

    # 固定電話のハイフンなしパターン
    response = client.get("/search?q=番号は 0312345678 です")
    assert response.status_code == 400
    assert "PHONE_NUMBER" in response.json()["detail"]

def test_pii_blocking_my_number(client, mocker):
    """日本のマイナンバーを含むクエリがblock設定で適切に拒否されることをテストします。"""
    mocker.patch.object(settings, "PII_DETECTION_ENABLED", True)
    mocker.patch.object(settings, "PII_BLOCK_LEVEL", "block")

    response = client.get("/search?q=マイナンバーは 123456789012 です")
    assert response.status_code == 400
    assert "MY_NUMBER" in response.json()["detail"]

def test_sensitive_word_blocking(client, mocker):
    """機密ワードが含まれる場合に強制ブロックされることをテストします。"""
    mocker.patch.object(settings, "PII_DETECTION_ENABLED", True)
    mocker.patch.object(settings, "PII_BLOCK_LEVEL", "anonymize")  # 匿名化設定であっても強制ブロックされるべき
    mocker.patch.object(settings, "SENSITIVE_WORDS", ["社外秘", "secret"])

    # 日本語の機密ワード
    response = client.get("/search?q=このデータは社外秘です")
    assert response.status_code == 400
    assert "SENSITIVE_WORD" in response.json()["detail"]

    # 英語の機密ワード
    response = client.get("/search?q=this is a secret project")
    assert response.status_code == 400
    assert "SENSITIVE_WORD" in response.json()["detail"]

def test_pii_anonymize_query(client, mocker):
    """anonymize設定のときに個人情報が匿名化されて検索が実行されることをテストします。"""
    mocker.patch.object(settings, "PII_DETECTION_ENABLED", True)
    mocker.patch.object(settings, "PII_BLOCK_LEVEL", "anonymize")

    # 検索サービス呼び出しをモックし、実際に渡されたクエリを検証
    mock_search = mocker.patch(
        "src.services.searxng_service.SearxngService.search",
        return_value=ResultSet(query="anonymous", number_of_results=0, results=[])
    )

    response = client.get("/search?q=my email is john.doe@example.com")
    assert response.status_code == 200
    
    # 実際に検索サービスに渡されたクエリを取得して検証
    called_kwargs = mock_search.call_args[1]
    query_sent = called_kwargs["q"]
    assert "john.doe@example.com" not in query_sent
    assert "EMAIL_ADDRESS" in query_sent

def test_pii_mask_response(client, mocker):
    """検索結果（レスポンス）に含まれる個人情報がマスキングされることをテストします。"""
    mocker.patch.object(settings, "PII_DETECTION_ENABLED", True)
    mocker.patch.object(settings, "PII_BLOCK_LEVEL", "block")
    mocker.patch.object(settings, "PII_MASK_RESPONSE", True)

    # 検索結果に個人情報（電話番号、マイナンバー、メールアドレス）を紛れ込ませる
    mock_result_set = ResultSet(
        query="python",
        number_of_results=1,
        results=[
            SearchResult(
                title="John Doe - Contact at john.doe@example.com",
                url="https://example.com/john",
                content="His phone number is 090-1234-5678. Also MyNumber is 123456789012.",
                engine="google"
            )
        ]
    )
    mocker.patch(
        "src.services.searxng_service.SearxngService.search",
        return_value=mock_result_set
    )

    response = client.get("/search?q=python")
    assert response.status_code == 200
    
    data = response.json()
    first_result = data["results"][0]
    
    # タイトルとコンテンツの中の個人情報がマスクされていることをアサート
    assert "john.doe@example.com" not in first_result["title"]
    assert "EMAIL_ADDRESS" in first_result["title"]
    assert "090-1234-5678" not in first_result["content"]
    assert "PHONE_NUMBER" in first_result["content"]
    assert "123456789012" not in first_result["content"]
    assert "MY_NUMBER" in first_result["content"]
