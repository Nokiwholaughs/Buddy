from flask import Flask, jsonify, request
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
    if operation_queue:
        op = operation_queue.popleft()
        return jsonify({"status": "success", "operation": op}), 200
    return jsonify({"status": "success", "operation": None}), 400

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
    else:
        # Normal mode: Flask + MCP server
        import asyncio
        from buddy_functions import init_shared_state
        from mcp_server import run_server
        
        # Initialize shared state for buddy functions (used by MCP tools)
        init_shared_state(operation_queue, latest_image)
        
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
        
        # Run MCP server in main thread (stdio mode)
        asyncio.run(run_server())
