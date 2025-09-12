# Tasks: SearXNG MCP Server (v2 - Audited)

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
- [ ] T010: Create `src/routers/searxng_router.py`. Implement the `/search` endpoint, ensuring it accepts `q`, `categories`, and `time_range` as query parameters and passes them to the service layer.
- [ ] T011: Create `src/main.py` to configure the FastAPI app and include the `searxng_router`.

*Verification: T008 (Contract Test) should now pass. T007 (Integration Test) must still fail.*

## Phase 4: Implement Business Logic (GREEN for Integration Test)
- [ ] T012: In `src/services/searxng_service.py`, implement the logic to build the correct request URL and parameters for the SearXNG API call, using the values passed from the router.
- [ ] T013: In `src/services/searxng_service.py`, implement the `httpx` call to the SearXNG API and parse the JSON response into the `ResultSet` model.

*Verification: T007 (Integration Test) should now pass.*

## Phase 5: Add Edge Case Tests (RED -> GREEN Cycle)
- [ ] T014 [P]: In `tests/integration/test_search.py`, add a new test case `test_searxng_unavailable` that mocks the HTTP request to raise a connection error.
- [ ] T015: Implement a FastAPI exception handler or middleware to catch the connection error and return a 503 Service Unavailable response. T014 should now pass.
- [ ] T016 [P]: In `tests/integration/test_search.py`, add a new test case `test_no_results_found` that mocks the SearXNG response to be an empty list.
- [ ] T017: Ensure the service and router correctly handle the empty list and return a 200 OK with an empty `results` array. T016 should now pass.

## Phase 6: Refactor
- [ ] T018: Review the entire codebase for clarity, efficiency, and adherence to best practices. Ensure all environment variables, URLs, and magic strings are handled via the `config.py` settings. Ensure all tests pass.

## Dependencies
- T001-T006 are foundational setup tasks.
- T007 & T008 (failing tests) must precede T009.
- T009-T011 (API structure) must precede T012.
- T012 & T013 (business logic) make the main integration test pass.
- Edge case tests (T014, T016) must be written before their corresponding implementation (T015, T017).