import httpx
import logging
from src.config import settings
from src.schemas import ResultSet, SearchResult

logger = logging.getLogger("searxng_mcp.searxng_service")

class SearxngUnavailableError(Exception):
    """SearXNGサービスが利用不可能な場合のカスタム例外。"""
    pass

class SearxngService:
    """
    SearXNG APIと連携するためのサービスレイヤー。
    """

    def __init__(self):
        # settings.SEARXNG_URLを一元的に使用
        self.base_url = settings.SEARXNG_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=settings.SEARXNG_TIMEOUT
        )

    async def search(self, q: str, categories: str | None, time_range: str | None) -> ResultSet:
        """
        Performs a search using the SearXNG API.
        """
        params = {
            "q": q,
            "format": "json",
        }
        if categories:
            params["categories"] = categories
        if time_range:
            params["time_range"] = time_range

        try:
            response = await self.client.get("/search", params=params)
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.exception("Failed to connect to SearXNG")
            raise SearxngUnavailableError("SearXNG service is temporarily unavailable")

        data = response.json()
        results = [
            SearchResult(
                title=r.get("title"),
                url=r.get("url"),
                content=r.get("content") or r.get("snippet"),
                engine=r.get("engine"),
            )
            for r in data.get("results", [])
        ]

        return ResultSet(
            query=data.get("query"),
            number_of_results=len(results),
            results=results,
        )

def get_searxng_service() -> SearxngService:
    return SearxngService()
