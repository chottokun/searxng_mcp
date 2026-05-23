import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def client():
    """FastAPIテストクライアントを提供するモジュールスコープのフィクスチャ。"""
    with TestClient(app) as c:
        yield c

def test_read_root(client):
    """
    ヘルスチェックエンドポイント（/）が正しく動作することをテストします。
    200 OKと{"status": "ok"}が返ることを確認します。
    """
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
