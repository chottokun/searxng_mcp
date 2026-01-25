import httpx
from src.schemas import ResultSet, SearchResult
from src.config import settings

class SearxngUnavailableError(Exception):
    """Custom exception for when the SearXNG service is unavailable."""
    pass

class SearxngService:
    """
    Service layer for interacting with the SearXNG API.
    """

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def search(self, q: str, categories: str | None = None, time_range: str | None = None) -> ResultSet:
        """
        Performs a search using the SearXNG API.
        """
        if not q.strip():
            return ResultSet(query=q, number_of_results=0, results=[])

        params = {
            "q": q,
            "format": "json",
        }
        if categories:
            params["categories"] = categories
        if time_range:
            params["time_range"] = time_range

        try:
            response = await self.client.get("/search", params=params, timeout=settings.SEARXNG_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as e:
            raise SearxngUnavailableError(f"SearXNG service timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise SearxngUnavailableError(f"SearXNG service returned an error status {response.status_code}: {e}")
        except httpx.RequestError as e:
            raise SearxngUnavailableError(f"SearXNG service request failed: {e}")
        except ValueError as e:
            raise SearxngUnavailableError(f"SearXNG service returned an invalid JSON response: {e}")

        results = [
            SearchResult(
                title=r.get("title") or "No Title",
                url=r.get("url") or "",
                content=r.get("content") or r.get("snippet") or "",
                engine=r.get("engine") or "unknown",
            )
            for r in data.get("results", [])
        ]

        return ResultSet(
            query=data.get("query") or q,
            number_of_results=len(results),
            results=results,
        )

def get_searxng_service(client: httpx.AsyncClient) -> SearxngService:
    """
    Factory function to create a SearxngService with a given client.
    This is intended to be used with FastAPI's dependency injection.
    """
    return SearxngService(client)
