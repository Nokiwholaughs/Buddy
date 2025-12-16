"""
Buddy robot tool implementations.
Each function corresponds to an MCP tool and takes parameters directly.
"""
import json
import sys
import os
import base64
from mcp.types import TextContent, ImageContent

# Shared state - initialized by api.py
operation_queue = None
latest_image = None
queue_lock = None

# Path to the latest image file
LATEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "latest_image.png")


def log(msg):
    print(msg, file=sys.stderr)


def init_shared_state(queue, image, lock):
    """Initialize shared state from api.py"""
    global operation_queue, latest_image, queue_lock
    operation_queue = queue
    latest_image = image
    queue_lock = lock


def queue_operation(operation: dict, message: str):
    """Queue an operation and return response with JSON debug info."""
    with queue_lock:
        operation_queue.append(operation)
        queue_size = len(operation_queue)
        queue_id = id(operation_queue)
    
    # Log with queue details for debugging
    log(f"Queued: {json.dumps(operation)}")
    log(f"Queue size after append: {queue_size} (Queue ID: {queue_id})")
    
    return [TextContent(type="text", text=f"{message}\n\nOperation JSON:\n```json\n{json.dumps(operation, indent=2)}\n```")]


# --- Tool implementations ---

def move_buddy(speed: float, distance: float):
    """Move Buddy forward or backward."""
    operation = {
        "type": "MoveOperation",
        "speed": speed,
        "distance": distance
    }
    direction = "forward" if speed > 0 else "backward"
    return queue_operation(operation, f"Queued move {direction} at speed {speed} for {distance}m")


def rotate_buddy(speed: float, angle: float):
    """Rotate Buddy left or right by the specified angle."""
    operation = {
        "type": "RotateOperation",
        "speed": speed,
        "angle": angle
    }
    return queue_operation(operation, f"Queued rotation at speed {speed} for {angle} degrees")


def speak(message: str, volume: int = 300):
    """Make Buddy say something out loud."""
    operation = {
        "type": "TalkOperation",
        "message": message,
        "volume": volume
    }
    return queue_operation(operation, f"Queued speech: '{message}' at volume {volume}")


def move_head(axis: str, speed: float = 40.0, angle: float = 20.0):
    """Nod (axis='yes') or shake (axis='no') Buddy's head."""
    axis_value = "Yes" if axis.lower() == "yes" else "No"
    operation = {
        "type": "HeadOperation",
        "speed": speed,
        "angle": angle,
        "axis": axis_value
    }
    action = "nod" if axis_value == "Yes" else "shake"
    return queue_operation(operation, f"Queued head {action} at speed {speed} with angle {angle}")


def set_mood(mood: str):
    """Set Buddy's facial expression/mood displayed on screen."""
    operation = {
        "type": "MoodOperation",
        "mood": mood.upper()
    }
    return queue_operation(operation, f"Queued mood change to {mood.upper()}")


def take_picture():
    """Get the latest camera image captured by Buddy."""
    if not os.path.exists(LATEST_IMAGE_PATH):
        return [TextContent(type="text", text="No image available. The robot hasn't sent any image yet.")]
    
    try:
        with open(LATEST_IMAGE_PATH, 'rb') as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        with queue_lock:
            timestamp = latest_image.get("timestamp", "unknown")
        
        return [
            TextContent(type="text", text=f"Image captured at {timestamp}"),
            ImageContent(type="image", data=image_base64, mimeType="image/png")
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error reading image: {e}")]


# --- Tool dispatch dictionary ---

TOOL_HANDLERS = {
    "move_buddy": move_buddy,
    "rotate_buddy": rotate_buddy,
    "speak": speak,
    "move_head": move_head,
    "set_mood": set_mood,
    "take_picture": take_picture,
}


# --- CLI support (used by api.py) ---

def build_operation(name: str, **kwargs) -> dict:
    """Build an operation dict for a given tool name and arguments."""
    if name == "move_buddy":
        return {"type": "MoveOperation", "speed": kwargs["speed"], "distance": kwargs["distance"]}
    elif name == "rotate_buddy":
        return {"type": "RotateOperation", "speed": kwargs["speed"], "angle": kwargs["angle"]}
    elif name == "speak":
        return {"type": "TalkOperation", "message": kwargs["message"], "volume": kwargs.get("volume", 300)}
    elif name == "move_head":
        axis_value = "Yes" if kwargs["axis"].lower() == "yes" else "No"
        return {"type": "HeadOperation", "speed": kwargs.get("speed", 40.0), "angle": kwargs.get("angle", 20.0), "axis": axis_value}
    elif name == "set_mood":
        return {"type": "MoodOperation", "mood": kwargs["mood"].upper()}
    else:
        return None

