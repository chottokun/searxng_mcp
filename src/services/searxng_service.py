import os
import httpx
from src.schemas import ResultSet, SearchResult

class SearxngUnavailableError(Exception):
    """Custom exception for when the SearXNG service is unavailable."""
    pass

class SearxngService:
    """
    Service layer for interacting with the SearXNG API.
    """

    def __init__(self):
        self.base_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
        self.client = httpx.AsyncClient(base_url=self.base_url)

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
            raise SearxngUnavailableError(f"SearXNG service is unavailable: {e}")

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
