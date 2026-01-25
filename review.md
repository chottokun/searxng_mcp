# Code Review: SearXNG MCP Server

## 1. Bug & Logic
- **`httpx.AsyncClient` Resource Leak**: In `src/services/searxng_service.py`, a new `httpx.AsyncClient` is created in every `SearxngService.__init__`. Since `get_searxng_service` creates a new `SearxngService` instance for every request, this leads to a resource leak as clients are never closed.
- **Deprecated MCP Mount**: `src/main.py` uses `mcp.mount()`, which is deprecated in `fastapi-mcp` 0.4.0. It should use `mount_http()` or `mount_sse()`.
- **Inconsistent Settings Usage**: `src/services/searxng_service.py` uses `os.getenv` instead of the `settings` object defined in `src/config.py`.
- **Fragile Error Handling**: The `search` method in `SearxngService` assumes the response will always be JSON and doesn't handle potential `JSONDecodeError`.

## 2. Performance
- **Client Per Request**: Creating a new `httpx.AsyncClient` for every search request is highly inefficient. Reusing a single client instance would allow for connection pooling and reduced latency.

## 3. Readability & Maintainability
- **Contract Mismatch**: There is a significant mismatch between the OpenAPI spec (`specs/001-searxng-mcp/contracts/api.yaml`) and the implementation (`src/schemas.py`).
    - `api.yaml` uses `snippet`, while `src/schemas.py` uses `content`.
    - `api.yaml` is missing `engine` in `SearchResult`.
    - `api.yaml` is missing `query` and `number_of_results` in `ResultSet`.
- **Documentation**: While docstrings are present, some could be more descriptive about the expected format of categories and time ranges.

## 4. Design & Architecture
- **Dependency Management**: `SearxngService` should be managed as a singleton or have its lifecycle tied to the FastAPI application lifespan to ensure proper resource management (closing the HTTP client).

## 5. Security
- **Missing Timeouts**: No timeout is configured for the `httpx.AsyncClient`. This could lead to the FastAPI application hanging if the SearXNG instance is slow or unresponsive.
- **Input Validation**: `q` is required but not validated for non-empty or whitespace-only strings beyond FastAPI's default.

## 6. Testing
- **Test Fragility**: `tests/contract/test_search_api.py` and `tests/integration/test_search.py` (specifically `test_successful_search`) depend on a live SearXNG service, making them unsuitable for isolated environments or CI/CD without extra setup.
- **Lack of Unit Tests**: There are no unit tests specifically for the `SearxngService` logic (e.g., parsing logic, error handling) in isolation from the FastAPI router.

## 7. README.md
- **Completeness**: The `README.md` is well-written and provides clear instructions for both Docker and local setup. It correctly identifies the project structure and key features.
- **Improvements**: Could benefit from adding a section on how to run tests in a mocked environment.
