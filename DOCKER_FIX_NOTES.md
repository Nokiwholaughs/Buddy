# Docker MCP/SSE Implementation Fix

## Problem
The original implementation tried to mix Flask (WSGI) with MCP SSE transport (ASGI), which caused the error:
```
TypeError: SseServerTransport.connect_sse() missing 1 required positional argument: 'send'
```

## Solution
Created a **dual-server architecture**:

1. **Flask Server (Port 5000)** - WSGI
   - Robot control API (`/upload_image`, `/operation`)
   - Health check (`/`)
   - Used by the Buddy robot

2. **MCP/SSE Server (Port 5001)** - ASGI (Starlette)
   - MCP protocol endpoints (`/mcp`, `/sse`)
   - Proper SSE transport implementation
   - Used by ChatGPT and Claude API

## New Files

- `mcp_http_server.py` - ASGI server for MCP/SSE endpoints
- `start_servers.py` - Unified launcher for both servers
- `DOCKER_FIX_NOTES.md` - This file

## Updated Files

- `Dockerfile` - Now runs `start_servers.py` and exposes both ports
- `docker-compose.yml` - Exposes both 5000 and 5001
- `requirements.txt` - Added `starlette`, `httpx`, `uvicorn`
- `README.md` - Updated port references
- `DOCKER_QUICKSTART.md` - Updated ngrok instructions

## How to Rebuild

```bash
# Clean up old containers
docker-compose down -v
docker rm -f buddy-mcp-server buddy-server 2>/dev/null || true

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Port Usage

| Port | Server | Purpose |
|------|--------|---------|
| 5000 | Flask (WSGI) | Robot control API |
| 5001 | Starlette (ASGI) | MCP/SSE endpoints |

## ngrok Setup

```bash
# For AI integrations (ChatGPT/Claude API)
ngrok http 5001

# For robot API (if needed externally)
ngrok http 5000
```

## Testing

```bash
# Test Flask API
curl http://localhost:5000/

# Test MCP endpoint
curl http://localhost:5001/mcp

# Test SSE endpoint
curl http://localhost:5001/sse
```

## Architecture

```
┌─────────────────────────────────────┐
│         Docker Container            │
│                                     │
│  ┌──────────────┐  ┌──────────────┐│
│  │   Flask      │  │  Starlette   ││
│  │   :5000      │  │  :5001       ││
│  │              │  │              ││
│  │ /operation   │  │ /mcp         ││
│  │ /upload_image│  │ /sse         ││
│  └──────────────┘  └──────────────┘│
│         ▲                 ▲         │
└─────────┼─────────────────┼─────────┘
          │                 │
    Buddy Robot       ChatGPT/Claude
```

## Why Two Servers?

- **Flask (WSGI)**: Mature, synchronous, perfect for simple REST API
- **Starlette (ASGI)**: Modern, async, required for SSE/WebSocket support

MCP SSE transport requires ASGI. Rather than migrate everything to ASGI, we run both servers simultaneously.

## Benefits

- ✅ Proper SSE implementation
- ✅ No WSGI/ASGI mixing
- ✅ Clean separation of concerns
- ✅ Both servers share same codebase
- ✅ Independent scaling possible

