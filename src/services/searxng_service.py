import httpx
from src.schemas import ResultSet, SearchResult
from src.config import settings
from src.services.privacy_service import PrivacyService, get_privacy_service

class SearxngUnavailableError(Exception):
    """Custom exception for when the SearXNG service is unavailable."""
    pass

class SearxngService:
    """
    Service layer for interacting with the SearXNG API.
    """

    def __init__(self, client: httpx.AsyncClient, privacy_service: PrivacyService):
        self.client = client
        self.privacy_service = privacy_service

    async def search(self, q: str, categories: str | None, time_range: str | None) -> ResultSet:
        """
        Performs a search using the SearXNG API after redacting PII from the query.
        """
        # Redact PII from the query before sending it to SearXNG
        sanitized_q = self.privacy_service.redact_query(q)

        params = {
            "q": sanitized_q,
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
            query=sanitized_q,
            number_of_results=len(results),
            results=results,
        )

def get_searxng_service(
    client: httpx.AsyncClient,
    privacy_service: PrivacyService = get_privacy_service()
) -> SearxngService:
    # In a real FastAPI app, the client would be retrieved from app.state
    # This factory function will be used by the router
    return SearxngService(client=client, privacy_service=privacy_service)
