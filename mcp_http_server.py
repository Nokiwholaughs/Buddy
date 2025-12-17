"""
MCP HTTP Server using StreamableHTTPSessionManager

This provides the HTTP/SSE transport for MCP protocol,
separate from the Flask WSGI app.

Uses the proper MCP pattern with StreamableHTTPSessionManager.
"""

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp_server import app as mcp_app
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from buddy_functions import init_shared_state


def log(msg):
    """Log messages to stderr"""
    print(f"[MCP HTTP Server] {msg}", file=sys.stderr)


# Create session manager for the MCP server
session_manager = StreamableHTTPSessionManager(app=mcp_app)


async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "server": "buddy-mcp-server",
        "version": "1.0.0"
    })


@asynccontextmanager
async def app_lifespan(app: Starlette) -> AsyncIterator[None]:
    """Lifespan manager for the Starlette app"""
    log("Starting MCP session manager")
    async with session_manager.run():
        log("MCP session manager running")
        yield
    log("MCP session manager stopped")


# Create Starlette ASGI app with proper MCP routing
mcp_asgi_app = Starlette(
    routes=[
        Route("/", health_check),
        Mount("/mcp", app=session_manager.handle_request),
        Mount("/sse", app=session_manager.handle_request),
    ],
    lifespan=app_lifespan,
)


if __name__ == "__main__":
    import uvicorn
    log("Starting MCP HTTP/SSE server on port 5001")
    uvicorn.run(mcp_asgi_app, host="0.0.0.0", port=5001)

