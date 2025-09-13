# SearXNG MCP Server

This project provides a FastAPI-based server that exposes a search endpoint as a tool compatible with the Model Context Protocol (MCP). It is designed to act as a bridge between an AI agent (like Claude) and a SearXNG instance, allowing the agent to perform web searches.

## Features

-   **FastAPI Backend**: A modern, fast web framework for building APIs.
-   **MCP Integration**: Exposes the search functionality as an MCP tool using the `fastapi-mcp` library, making it discoverable and usable by AI agents.
-   **Pydantic Schemas**: Clear, validated data models for API requests and responses.
-   **Edge Case Handling**: Includes tests and handlers for common edge cases like "no results found" and "service unavailable".
-   **Contract and Integration Testing**: A suite of tests to validate the API against its OpenAPI contract and to test its functionality.

## Project Structure

```
.
├── requirements-dev.txt
├── requirements.txt
├── searxng_config/
│   └── settings.yml
├── src/
│   ├── __init__.py
│   ├── config.py         # Pydantic settings management
│   ├── main.py           # FastAPI application entrypoint and MCP setup
│   ├── routers/
│   │   └── searxng_router.py # API router for the /search endpoint
│   ├── schemas.py        # Pydantic models for data structures
│   └── services/
│       └── searxng_service.py # Mocked service layer for search logic
└── tests/
    ├── contract/
    │   └── test_search_api.py # OpenAPI contract validation tests
    └── integration/
        └── test_search.py     # Integration tests for API functionality
```

## Getting Started

### Prerequisites

-   Python 3.11+
-   `pip` for installing dependencies
-   Docker and Docker Compose (for the recommended setup)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Server

#### With Docker (Recommended)

The project is configured to run with Docker Compose, which orchestrates both the FastAPI server and a SearXNG instance.

```bash
docker compose up --build
```

The services will be available at:
-   **MCP Server**: `http://127.0.0.1:8000`
-   **SearXNG Instance**: `http://127.0.0.1:8080`

#### Locally with Uvicorn

You can also run the web server locally using `uvicorn`. However, this requires you to have a separate SearXNG instance running and to configure the `SEARXNG_URL` environment variable accordingly.

```bash
# Example:
export SEARXNG_URL=http://localhost:8080
uvicorn src.main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

-   **API Docs**: `http://127.0.0.1:8000/docs`
-   **MCP Endpoint**: `http://127.0.0.1:8000/mcp`

## Running Tests

To run the test suite, you need to install the development dependencies. This will also include the main application dependencies from `requirements.txt`.

```bash
pip install -r requirements-dev.txt
```

Then, run `pytest` from the project root. Make sure the Docker containers are running and set the `SEARXNG_URL` environment variable:

```bash
SEARXNG_URL='http://localhost:8080' pytest
```

## API Endpoint

### `GET /search`

Performs a search query.

-   **Query Parameters**:
    -   `q` (str, required): The search query string.
    -   `categories` (str, optional): A comma-separated list of search categories (e.g., 'news,files').
    -   `time_range` (str, optional): A time range for the search (e.g., 'day', 'week', 'month').
-   **Success Response (200 OK)**:
    ```json
    {
      "query": "fastapi",
      "number_of_results": 26,
      "results": [
        {
          "title": "FastAPI",
          "url": "https://fastapi.tiangolo.com/",
          "content": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints...",
          "engine": "brave"
        }
      ]
    }
    ```
-   **Service Unavailable (503 Service Unavailable)**:
    -   Returned if the connection to the SearXNG service fails.
    ```json
    {
      "detail": "SearXNG service is unavailable: <error details>"
    }
    ```
