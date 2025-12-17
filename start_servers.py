"""
Start both Flask (for robot API) and Starlette (for MCP/SSE) servers.
"""

import threading
import sys
import logging

def log(msg):
    print(msg, file=sys.stderr)


def start_flask():
    """Start Flask server in a thread"""
    from api import app, operation_queue, latest_image, queue_lock
    from buddy_functions import init_shared_state
    
    # Initialize shared state
    init_shared_state(operation_queue, latest_image, queue_lock)
    
    # Configure logging
    werkzeug_log = logging.getLogger('werkzeug')
    werkzeug_log.setLevel(logging.INFO)
    
    log("Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


def start_mcp_server(operation_queue, latest_image, queue_lock):
    """Start MCP HTTP/SSE server"""
    import uvicorn
    from mcp_http_server import mcp_asgi_app
    from buddy_functions import init_shared_state
    
    # Initialize shared state for MCP tools
    init_shared_state(operation_queue, latest_image, queue_lock)
    
    log("Starting MCP HTTP/SSE server on port 5001")
    uvicorn.run(mcp_asgi_app, host="0.0.0.0", port=5001, log_level="info")


if __name__ == "__main__":
    from api import operation_queue, latest_image, queue_lock
    
    log("=" * 60)
    log("Starting Buddy MCP Server System")
    log("Flask API (robot control): http://0.0.0.0:5000")
    log("MCP/SSE endpoints: http://0.0.0.0:5001/mcp and /sse")
    log("=" * 60)
    
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Wait a moment for Flask to initialize
    import time
    time.sleep(2)
    
    # Start MCP server in main thread
    start_mcp_server(operation_queue, latest_image, queue_lock)

