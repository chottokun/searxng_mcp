# Tasks: SearXNG MCP Server (v4 - Final & Compliant)

**Input**: Design documents from `/specs/001-searxng-mcp/`

## Phase 1: Project Setup
- [ ] T001: Create `requirements.txt` with `fastapi`, `uvicorn`, `httpx`, and `fastapi-mcp`. Create `requirements-dev.txt` with `pytest`.
- [ ] T002: Create and configure a `pyproject.toml` file to set up `ruff` for linting and formatting.
- [ ] T003: Create the `Dockerfile` for the FastAPI application in the repository root.
- [ ] T004: Create the `docker-compose.yml` file in the repository root, defining the `mcp-searxng` and `searxng` services.
- [ ] T005: Create the Pydantic models for `SearchQuery`, `SearchResult`, and `ResultSet` in `src/schemas.py`.
- [ ] T006: Create `src/config.py` and implement a Pydantic `Settings` class to read `SEARXNG_URL` from environment variables.

## Phase 2: Write Failing Tests (RED)
**CRITICAL: These tests MUST be written and MUST FAIL before proceeding.**
- [ ] T007 [P]: Create `tests/integration/test_search.py` and write a test case `test_successful_search`. This test should simulate a GET request to `/search?q=test` and assert a 200 OK status. It must fail.
- [ ] T008 [P]: Create `tests/contract/test_search_api.py` and write a test case that validates the `/search` endpoint against `contracts/api.yaml`. It must fail.

## Phase 3: Implement API Structure (GREEN for Contract Test)
- [ ] T009: Create `src/services/searxng_service.py` and implement a skeleton `SearxngService` class with a method that returns a hardcoded, schema-valid response.
- [ ] T010: Create `src/routers/searxng_router.py`. Implement the `/search` endpoint, ensuring it:
    - Uses a unique `operation_id` (e.g., `search_searxng`), as this is **required by `fastapi-mcp`** to generate the tool name.
    - Accepts `q`, `categories`, and `time_range` as query parameters.
    - Follows the docstring convention from the guide.
- [ ] T011: Create `src/main.py` to configure the FastAPI app and include the `searxng_router`.

*Verification: T008 (Contract Test) should now pass. T007 (Integration Test) must still fail.*

## Phase 4: Implement Business Logic (GREEN for Integration Test)
- [ ] T012: In `src/services/searxng_service.py`, implement the logic to build the correct request URL and parameters for the SearXNG API call.
- [ ] T013: In `src/services/searxng_service.py`, implement the `httpx` call to the SearXNG API and parse the JSON response into the `ResultSet` model.

*Verification: T007 (Integration Test) should now pass.*

## Phase 5: Integrate `fastapi-mcp`
- [ ] T014: In `src/main.py`, import the MCP server from `fastapi_mcp` and mount it to the main FastAPI app. This will expose all defined endpoints as MCP tools for AI agents.

## Phase 6: Add Edge Case Tests (RED -> GREEN Cycle)
- [ ] T015 [P]: In `tests/integration/test_search.py`, add a new test case `test_searxng_unavailable` that mocks the HTTP request to raise a connection error.
- [ ] T016: Implement a FastAPI exception handler or middleware to catch the connection error and return a 503 Service Unavailable response. T015 should now pass.
- [ ] T017 [P]: In `tests/integration/test_search.py`, add a new test case `test_no_results_found` that mocks the SearXNG response to be an empty list.
- [ ] T018: Ensure the service and router correctly handle the empty list and return a 200 OK with an empty `results` array. T017 should now pass.

## Phase 7: Refactor & Polish
- [ ] T019: Review and refactor the entire codebase for clarity, efficiency, and adherence to best practices.
- [ ] T020: **[Docstrings]** Perform a final review of all docstrings for schemas, services, and routers. Ensure they are complete and follow the `FastAPImcp_guide.md` standard. **Note: These docstrings are used by `fastapi-mcp` to generate descriptions for the AI tools.**