from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.routers import searxng_router
from src.services.searxng_service import SearxngUnavailableError
from src.config import settings
from fastapi_mcp import FastApiMCP

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of the FastAPI application.
    Initializes a shared httpx.AsyncClient for connection pooling.
    """
    async with httpx.AsyncClient(
        base_url=settings.SEARXNG_URL,
        timeout=settings.SEARXNG_TIMEOUT
    ) as client:
        app.state.httpx_client = client
        yield

app = FastAPI(
    title="SearXNG MCP Server",
    description="A FastAPI server providing a tool for searching with SearXNG, compatible with fastapi-mcp.",
    version="0.1.0",
    lifespan=lifespan,
)

# Include the API router
app.include_router(searxng_router.router)

# Create and mount the MCP server, which will automatically discover the included router.
mcp = FastApiMCP(app)
mcp.mount_http()

@app.exception_handler(SearxngUnavailableError)
async def searxng_unavailable_exception_handler(request: Request, exc: SearxngUnavailableError):
    """
    Handles the custom SearxngUnavailableError and returns a 503 Service Unavailable response.
    """
    return JSONResponse(
        status_code=503,
        content={"detail": "SearXNG service is unavailable."},
    )

@app.get("/", tags=["Health"])
async def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}
