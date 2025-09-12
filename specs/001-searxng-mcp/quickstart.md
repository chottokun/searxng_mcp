# Quickstart

This guide provides instructions on how to run the SearXNG MCP server and perform a search.

## Running the Server

1.  **Start the server:**

    ```bash
    # (Instructions to run the server will be added here)
    ```

## Performing a Search

Once the server is running, you can perform a search by sending a GET request to the `/search` endpoint.

### Example using cURL

```bash
# Basic search
curl "http://localhost:8001/search?q=fastapi"

# Search with a category
curl "http://localhost:8001/search?q=python&categories=news"

# Search with a time range
curl "http://localhost:8001/search?q=docker&time_range=week"
```

### Expected Response

A successful search will return a JSON object with a list of results:

```json
{
  "results": [
    {
      "title": "FastAPI",
      "url": "https://fastapi.tiangolo.com/",
      "snippet": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints."
    }
  ]
}
```
