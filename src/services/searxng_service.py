from src.schemas import ResultSet, SearchResult

class SearxngUnavailableError(Exception):
    """Custom exception for when the SearXNG service is unavailable."""
    pass

class SearxngService:
    """
    Service layer for interacting with the SearXNG API.

    This service is mocked to return hardcoded data and does not make real HTTP calls.
    """

    async def search(self, q: str, categories: str | None, time_range: str | None) -> ResultSet:
        """
        Performs a mocked search.

        Returns a hardcoded, high-quality ResultSet for testing purposes.
        """

        mock_results = [
            SearchResult(
                title="FastAPI - The Python web framework for building APIs",
                url="https://fastapi.tiangolo.com/",
                content="FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.",
                engine="google"
            ),
            SearchResult(
                title="Tutorial - FastAPI",
                url="https://fastapi.tiangolo.com/tutorial/",
                content="This tutorial shows you how to use FastAPI with most of its features, step by step. Each section gradually builds on the previous ones.",
                engine="google"
            ),
            SearchResult(
                title="FastAPI on GitHub",
                url="https://github.com/tiangolo/fastapi",
                content="FastAPI framework, high performance, easy to learn, fast to code, ready for production.",
                engine="github"
            )
        ]

        # Handle the special case for testing "no results found"
        if q == "aquerythatyieldsnoresults":
            return ResultSet(query=q, number_of_results=0, results=[])

        # Handle the special case for testing "service unavailable"
        if q == "unavailable":
            raise SearxngUnavailableError("Mocked service is unavailable.")

        return ResultSet(
            query=q,
            number_of_results=len(mock_results),
            results=mock_results
        )

searxng_service = SearxngService()
