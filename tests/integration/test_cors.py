import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.anyio
async def test_cors_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test preflight request
        response = await ac.options(
            "/",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "*"
        assert "access-control-allow-methods" in response.headers

@pytest.mark.anyio
async def test_cors_get_request():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/", headers={"Origin": "http://example.com"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "*"
