from pydantic import BaseModel, Field
from typing import List, Optional

class SearchQuery(BaseModel):
    """Represents a user's search query, including filters."""
    q: str = Field(..., description="The search query string.")
    categories: Optional[str] = Field(None, description="Comma-separated list of search categories.")
    time_range: Optional[str] = Field(None, description="Time range for the search (e.g., 'day', 'week', 'month').")

class SearchResult(BaseModel):
    """Represents a single search result item from SearXNG."""
    title: str = Field(..., description="The title of the search result.")
    url: str = Field(..., description="The URL of the search result.")
    content: Optional[str] = Field(None, description="A snippet of content from the result.")
    engine: str = Field(..., description="The search engine that provided the result.")

class ResultSet(BaseModel):
    """Represents the complete set of search results for a given query."""
    query: str = Field(..., description="The original query string.")
    results: List[SearchResult] = Field(..., description="A list of search result items.")
    number_of_results: int = Field(..., description="The total number of results returned.")
