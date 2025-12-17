"""
MCP HTTP/SSE Server using Starlette (ASGI)

This provides the HTTP/SSE transport for MCP protocol,
separate from the Flask WSGI app.
"""

import asyncio
import logging
import sys
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from mcp.server.sse import SseServerTransport
from mcp_server import app as mcp_app


def log(msg):
    """Log messages to stderr"""
    print(f"[MCP HTTP Server] {msg}", file=sys.stderr)


# Create SSE transports
sse_transport_mcp = SseServerTransport("/mcp/messages")
sse_transport_sse = SseServerTransport("/sse/messages")


async def handle_mcp(request):
    """
    MCP endpoint for ChatGPT connector integration.
    """
    log(f"MCP endpoint accessed - {request.method}")
    
    async with sse_transport_mcp.connect_sse(request) as (read_stream, write_stream):
        await mcp_app.run(
            read_stream,
            write_stream,
            mcp_app.create_initialization_options()
        )
    
    return JSONResponse({"status": "ok"})


async def handle_sse(request):
    """
    SSE endpoint for Claude API MCP connector integration.
    """
    log(f"SSE endpoint accessed - {request.method}")
    
    async with sse_transport_sse.connect_sse(request) as (read_stream, write_stream):
        await mcp_app.run(
            read_stream,
            write_stream,
            mcp_app.create_initialization_options()
        )
    
    return JSONResponse({"status": "ok"})


async def handle_mcp_messages(request):
    """Message endpoint for /mcp transport"""
    log("MCP messages endpoint accessed")
    data = await request.json()
    log(f"MCP message data: {data}")
    return JSONResponse({"status": "received"})


async def handle_sse_messages(request):
    """Message endpoint for /sse transport"""
    log("SSE messages endpoint accessed")
    data = await request.json()
    log(f"SSE message data: {data}")
    return JSONResponse({"status": "received"})


# Create Starlette ASGI app
mcp_asgi_app = Starlette(
    debug=False,
    routes=[
        Route("/mcp", handle_mcp, methods=["GET", "POST"]),
        Route("/mcp/messages", handle_mcp_messages, methods=["POST"]),
        Route("/sse", handle_sse, methods=["GET", "POST"]),
        Route("/sse/messages", handle_sse_messages, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    import uvicorn
    log("Starting MCP HTTP/SSE server on port 5001")
    uvicorn.run(mcp_asgi_app, host="0.0.0.0", port=5001)

