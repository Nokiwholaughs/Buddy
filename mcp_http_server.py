"""
MCP HTTP/SSE Server using ASGI

This provides the HTTP/SSE transport for MCP protocol,
separate from the Flask WSGI app.
"""

import asyncio
import logging
import sys
from mcp.server.sse import SseServerTransport
from mcp_server import app as mcp_app
from buddy_functions import init_shared_state


def log(msg):
    """Log messages to stderr"""
    print(f"[MCP HTTP Server] {msg}", file=sys.stderr)


# Create SSE transports
sse_transport_mcp = SseServerTransport("/mcp/messages")
sse_transport_sse = SseServerTransport("/sse/messages")


class MCPServerApp:
    """
    ASGI application for MCP/SSE endpoints.
    Handles both /mcp and /sse endpoints with proper SSE transport.
    """
    
    def __init__(self):
        self.initialized = False
    
    async def __call__(self, scope, receive, send):
        """ASGI interface"""
        
        if scope['type'] != 'http':
            # Not an HTTP request
            await send({
                'type': 'http.response.start',
                'status': 400,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Bad Request',
            })
            return
        
        path = scope['path']
        method = scope['method']
        
        log(f"Request: {method} {path}")
        
        # Route to appropriate handler
        if path == '/':
            # Health check
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', b'application/json']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'{"status":"ok","server":"mcp-sse","version":"1.0.0"}',
            })
        elif path == '/mcp' or path.startswith('/mcp/'):
            await self.handle_mcp(scope, receive, send)
        elif path == '/sse' or path.startswith('/sse/'):
            await self.handle_sse(scope, receive, send)
        else:
            # 404 for other paths
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Not Found',
            })
    
    async def handle_mcp(self, scope, receive, send):
        """Handle /mcp endpoint"""
        log("Handling /mcp endpoint")
        try:
            async with sse_transport_mcp.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await mcp_app.run(
                    read_stream,
                    write_stream,
                    mcp_app.create_initialization_options()
                )
        except Exception as e:
            log(f"Error in /mcp handler: {e}")
            import traceback
            log(traceback.format_exc())
    
    async def handle_sse(self, scope, receive, send):
        """Handle /sse endpoint"""
        log("Handling /sse endpoint")
        try:
            async with sse_transport_sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await mcp_app.run(
                    read_stream,
                    write_stream,
                    mcp_app.create_initialization_options()
                )
        except Exception as e:
            log(f"Error in /sse handler: {e}")
            import traceback
            log(traceback.format_exc())


# Create the ASGI app
mcp_asgi_app = MCPServerApp()


if __name__ == "__main__":
    import uvicorn
    log("Starting MCP HTTP/SSE server on port 5001")
    uvicorn.run(mcp_asgi_app, host="0.0.0.0", port=5001)

