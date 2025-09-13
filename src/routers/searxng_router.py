from fastapi import APIRouter, Query, Depends
from typing import Optional
from src.schemas import ResultSet
from src.services.searxng_service import SearxngService, get_searxng_service

router = APIRouter()

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
    searxng_service: SearxngService = Depends(get_searxng_service)
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
    return await searxng_service.search(q=q, categories=categories, time_range=time_range)
