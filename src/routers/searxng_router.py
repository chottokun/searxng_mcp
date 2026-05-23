from fastapi import APIRouter, Query, Depends, Request
from typing import Optional
import httpx
from src.schemas import ResultSet
from src.services.searxng_service import SearxngService, get_searxng_service
from src.services.privacy_service import PrivacyService, get_privacy_service

router = APIRouter()

def get_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.client

@router.get(
    "/search",
    operation_id="search_searxng",
    response_model=ResultSet,
    summary="Perform a search using SearXNG",
    tags=["Search"]
)
async def search(
    q: str = Query(..., description="The search query string."),
    categories: Optional[str] = Query(None, description="Comma-separated list of search categories (e.g., 'news,files')."),
    time_range: Optional[str] = Query(None, description="Time range for the search (e.g., 'day', 'week', 'month')."),
    client: httpx.AsyncClient = Depends(get_client),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Performs a search using the configured SearXNG instance.

    This endpoint forwards the query to SearXNG and returns the results
    in a structured format.

    Args:
        q: The main search query.
        categories: Optional filter for search categories.
        time_range: Optional filter for the time range of the results.

    Returns:
        A `ResultSet` object containing the search results.
    """
    searxng_service = get_searxng_service(client=client, privacy_service=privacy_service)
    return await searxng_service.search(q=q, categories=categories, time_range=time_range)
