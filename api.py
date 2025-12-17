from flask import Flask, jsonify, request, Response
from collections import deque
from datetime import datetime
import threading
import sys
import logging
import base64
import os
import tempfile
from io import BytesIO
from PIL import Image
import asyncio
import json as json_module

app = Flask(__name__)

# Path to save the latest image
LATEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "latest_image.png")

# Target image size
IMAGE_SIZE = (800, 600)

# Redirect Flask logs to stderr (stdout is reserved for MCP JSON communication)
app.logger.addHandler(logging.StreamHandler(sys.stderr))
log = lambda msg: print(msg, file=sys.stderr)

# Shared state between Flask and MCP server
operation_queue = deque()
latest_image = {"base64": None, "timestamp": None}
queue_lock = threading.Lock()  # Lock to prevent race conditions between Flask and MCP threads


@app.route("/")
def home():
    return "Bienvenue sur l'api Buddy!"

@app.route("/upload_image", methods=['POST'])
def upload_image():
    # Get JSON payload from request
    data = request.get_json()
    
    if not data or 'image_base64' not in data:
        return jsonify({
            "error": "MissingParameter",
            "message": "Le paramètre 'image' (base64) est requis."
        }), 400
    
    image_base64 = data['image_base64']
    
    # Save image to file (overwrite latest), resized to 800x600
    try:
        image_bytes = base64.b64decode(image_base64)
        img = Image.open(BytesIO(image_bytes))
        img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
        img.save(LATEST_IMAGE_PATH, 'PNG')
    except Exception as e:
        log(f"Error saving image: {e}")
    
    # Store timestamp for MCP take_picture tool
    latest_image["timestamp"] = datetime.now().isoformat()
    
    return jsonify({
        "status": "success",
        "message": "Image reçue avec succès"
    }), 200

@app.route("/operation", methods=['GET'])
def operation():
    """
    Get the next operation from the queue.
    This endpoint is polled by Buddy to get commands to execute.
    """
    # Log queue state for debugging
    queue_id = id(operation_queue)
    queue_size = len(operation_queue)
    log(f"[/operation] Polled - Queue size: {queue_size} (Queue ID: {queue_id})")
    
    if operation_queue:
        with queue_lock:
            op = operation_queue.popleft()
        log(f"[/operation] Returning operation: {op}")
        return jsonify({"status": "success", "operation": op}), 200
    
    log(f"[/operation] No operations in queue")
    return jsonify({"status": "success", "operation": None}), 200

@app.route("/mcp", methods=['GET', 'POST'])
def mcp_endpoint():
    """
    MCP endpoint for ChatGPT connector integration via SSE.
    This endpoint handles the Model Context Protocol over HTTP/SSE transport.
    """
    log(f"[/mcp] MCP endpoint accessed - Method: {request.method}")
    
    # Import MCP components
    try:
        from mcp.server.sse import SseServerTransport
        from mcp_server import app as mcp_app
    except ImportError as e:
        log(f"[/mcp] Error importing MCP SSE: {e}")
        return jsonify({"error": "MCP SSE transport not available", "details": str(e)}), 500
    
    try:
        # Create SSE transport with message endpoint
        sse_transport = SseServerTransport("/mcp/messages")
        
        # Handle SSE requests
        async def handle_sse():
            async with sse_transport.connect_sse(
                request.environ,
                lambda: Response(status=200)
            ) as streams:
                await mcp_app.run(
                    streams[0],
                    streams[1],
                    mcp_app.create_initialization_options()
                )
        
        # Run async handler in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(handle_sse())
        finally:
            loop.close()
        
        return Response(status=200)
        
    except Exception as e:
        log(f"[/mcp] Error handling MCP request: {e}")
        import traceback
        log(f"[/mcp] Traceback: {traceback.format_exc()}")
        return jsonify({"error": "MCP request failed", "details": str(e)}), 500

@app.route("/mcp/messages", methods=['POST'])
def mcp_messages():
    """
    Message endpoint for MCP SSE transport.
    Receives messages from the client (ChatGPT).
    """
    log(f"[/mcp/messages] POST received")
    try:
        data = request.get_json()
        log(f"[/mcp/messages] Data: {data}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        log(f"[/mcp/messages] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/sse", methods=['GET', 'POST'])
def sse_endpoint():
    """
    SSE endpoint for Claude API MCP connector integration.
    This is the endpoint used by Claude's Messages API with MCP connector.
    See: https://platform.claude.com/docs/en/agents-and-tools/mcp-connector
    """
    log(f"[/sse] SSE endpoint accessed - Method: {request.method}")
    
    # Import MCP components
    try:
        from mcp.server.sse import SseServerTransport
        from mcp_server import app as mcp_app
    except ImportError as e:
        log(f"[/sse] Error importing MCP SSE: {e}")
        return jsonify({"error": "MCP SSE transport not available", "details": str(e)}), 500
    
    try:
        # Create SSE transport with message endpoint
        sse_transport = SseServerTransport("/sse/messages")
        
        # Handle SSE requests
        async def handle_sse():
            async with sse_transport.connect_sse(
                request.environ,
                lambda: Response(status=200)
            ) as streams:
                await mcp_app.run(
                    streams[0],
                    streams[1],
                    mcp_app.create_initialization_options()
                )
        
        # Run async handler in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(handle_sse())
        finally:
            loop.close()
        
        return Response(status=200)
        
    except Exception as e:
        log(f"[/sse] Error handling SSE request: {e}")
        import traceback
        log(f"[/sse] Traceback: {traceback.format_exc()}")
        return jsonify({"error": "SSE request failed", "details": str(e)}), 500

@app.route("/sse/messages", methods=['POST'])
def sse_messages():
    """
    Message endpoint for Claude API SSE transport.
    Receives messages from Claude's MCP connector.
    """
    log(f"[/sse/messages] POST received")
    try:
        data = request.get_json()
        log(f"[/sse/messages] Data: {data}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        log(f"[/sse/messages] Error: {e}")
        return jsonify({"error": str(e)}), 500

def run_cli():
    """Run interactive CLI for controlling Buddy."""
    import json
    from buddy_functions import build_operation, LATEST_IMAGE_PATH
    
    print("Buddy CLI - Type 'help' for commands, 'quit' to exit")
    
    while True:
        try:
            user_input = input("\nbuddy> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        
        elif cmd == "help":
            print("""
Commands:
  move <speed> <distance>     Move forward/backward (distance: + forward, - backward)
  rotate <speed> <angle>      Rotate (angle: + right, - left)
  speak <message>             Make Buddy speak (use quotes for multi-word)
  speak <message> <volume>    Speak with specific volume (100-500)
  head <yes|no>               Nod (yes) or shake (no) head
  mood <mood>                 Set mood (happy, sad, angry, surprised, neutral, afraid, disgusted, contempt)
  picture                     Show latest picture info
  queue                       Show current operation queue
  help                        Show this help
  quit                        Exit CLI
""")
        
        elif cmd == "move":
            if len(args) < 2:
                print("Usage: move <speed> <distance>")
                continue
            try:
                operation = build_operation("move_buddy", speed=float(args[0]), distance=float(args[1]))
                operation_queue.append(operation)
                print(f"Queued: {json.dumps(operation)}")
            except ValueError:
                print("Error: speed and distance must be numbers")
        
        elif cmd == "rotate":
            if len(args) < 2:
                print("Usage: rotate <speed> <angle>")
                continue
            try:
                operation = build_operation("rotate_buddy", speed=float(args[0]), angle=float(args[1]))
                operation_queue.append(operation)
                print(f"Queued: {json.dumps(operation)}")
            except ValueError:
                print("Error: speed and angle must be numbers")
        
        elif cmd == "speak":
            if len(args) < 1:
                print("Usage: speak <message> [volume]")
                continue
            # Check if last arg is a number (volume)
            volume = 300
            message_parts = args
            if len(args) > 1 and args[-1].isdigit():
                volume = int(args[-1])
                message_parts = args[:-1]
            message = " ".join(message_parts)
            operation = build_operation("speak", message=message, volume=volume)
            operation_queue.append(operation)
            print(f"Queued: {json.dumps(operation)}")
        
        elif cmd == "head":
            if len(args) < 1 or args[0].lower() not in ("yes", "no"):
                print("Usage: head <yes|no>")
                continue
            operation = build_operation("move_head", axis=args[0].lower())
            operation_queue.append(operation)
            print(f"Queued: {json.dumps(operation)}")
        
        elif cmd == "mood":
            valid_moods = ["happy", "sad", "angry", "surprised", "neutral", "afraid", "disgusted", "contempt"]
            if len(args) < 1 or args[0].lower() not in valid_moods:
                print(f"Usage: mood <{' | '.join(valid_moods)}>")
                continue
            operation = build_operation("set_mood", mood=args[0].lower())
            operation_queue.append(operation)
            print(f"Queued: {json.dumps(operation)}")
        
        elif cmd == "picture":
            if os.path.exists(LATEST_IMAGE_PATH):
                size = os.path.getsize(LATEST_IMAGE_PATH)
                print(f"Latest image: {LATEST_IMAGE_PATH} ({size} bytes)")
            else:
                print("No image available.")
        
        elif cmd == "queue":
            if operation_queue:
                print(f"Queue ({len(operation_queue)} operations):")
                for i, op in enumerate(operation_queue):
                    print(f"  {i+1}. {json.dumps(op)}")
            else:
                print("Queue is empty.")
        
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Buddy Flask Server")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI (Flask only, no MCP)")
    parser.add_argument("--http", action="store_true", help="Run Flask + MCP in HTTP/SSE mode (for Docker/ChatGPT)")
    args = parser.parse_args()
    
    if args.cli:
        # CLI mode: Flask server + interactive CLI (no MCP)
        # Suppress Flask/Werkzeug request logging to keep CLI clean
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.ERROR)
        
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, threaded=True),
            daemon=True
        )
        flask_thread.start()
        print("Flask server started on http://0.0.0.0:5000")
        run_cli()
    elif args.http:
        # HTTP mode: Flask + MCP server via HTTP/SSE (for Docker and ChatGPT connectors)
        from buddy_functions import init_shared_state
        
        # Initialize shared state for buddy functions (used by MCP tools)
        init_shared_state(operation_queue, latest_image, queue_lock)
        
        # Configure logging
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.INFO)
        
        log("=" * 60)
        log("Starting Buddy MCP Server in HTTP/SSE mode")
        log("Flask API + MCP endpoint running on http://0.0.0.0:5000")
        log("MCP endpoint: http://0.0.0.0:5000/mcp")
        log("For ChatGPT connectors, expose via ngrok or Cloudflare Tunnel")
        log("=" * 60)
        
        # Run Flask server (includes /mcp endpoint)
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    else:
        # Normal mode: Flask + MCP server in stdio mode (for Claude Desktop)
        import asyncio
        from buddy_functions import init_shared_state
        from mcp_server import run_server
        
        # Initialize shared state for buddy functions (used by MCP tools)
        init_shared_state(operation_queue, latest_image, queue_lock)
        
        # Suppress Flask/Werkzeug request logging (it goes to stdout and breaks MCP)
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.ERROR)
        
        # Run Flask in a background thread
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, threaded=True),
            daemon=True
        )
        flask_thread.start()
        log("Flask server started on http://0.0.0.0:5000")
        
        # Run MCP server in main thread (stdio mode for Claude Desktop)
        asyncio.run(run_server())
