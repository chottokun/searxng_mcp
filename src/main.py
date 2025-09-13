from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.routers import searxng_router
from src.services.searxng_service import SearxngUnavailableError
from fastapi_mcp import FastApiMCP

app = FastAPI(
    title="SearXNG MCP Server",
    description="A FastAPI server providing a tool for searching with SearXNG, compatible with fastapi-mcp.",
    version="0.1.0",
)

# Include the API router
app.include_router(searxng_router.router)

# Create and mount the MCP server, which will automatically discover the included router.
mcp = FastApiMCP(app)
mcp.mount()

@app.exception_handler(SearxngUnavailableError)
async def searxng_unavailable_exception_handler(request: Request, exc: SearxngUnavailableError):
    """
    Handles the custom SearxngUnavailableError and returns a 503 Service Unavail
able response.
    """
    return JSONResponse(
        status_code=503,
        content={"detail": "SearXNG service is unavailable."},
    )

@app.get("/", tags=["Health"])
async def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}
