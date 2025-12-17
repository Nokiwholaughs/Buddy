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
    """Move Buddy forward or backward.
    
    Parameter Rules:
    - speed: MUST be positive (will be forced to abs() if negative)
    - distance: Positive = forward, Negative = backward
    
    Examples:
    - move_buddy(100, 0.5)   -> Move forward 0.5m at speed 100
    - move_buddy(100, -0.5)  -> Move backward 0.5m at speed 100
    - move_buddy(-100, 0.5)  -> Move forward 0.5m at speed 100 (speed auto-corrected)
    """
    # Ensure speed is always positive (critical rule!)
    speed = abs(speed)
    
    operation = {
        "type": "MoveOperation",
        "speed": speed,
        "distance": distance
    }
    
    # Direction is determined by distance sign, NOT speed
    direction = "forward" if distance > 0 else "backward"
    return queue_operation(operation, f"Queued move {direction} at speed {speed} for {abs(distance)}m")


def rotate_buddy(speed: float, angle: float):
    """Rotate Buddy left or right by the specified angle.
    
    Parameter Rules:
    - speed: MUST be positive (will be forced to abs() if negative)
    - angle: Positive = turn right, Negative = turn left
    
    Examples:
    - rotate_buddy(50, 90)   -> Turn right 90° at speed 50
    - rotate_buddy(50, -90)  -> Turn left 90° at speed 50
    - rotate_buddy(-50, 90)  -> Turn right 90° at speed 50 (speed auto-corrected)
    """
    # Ensure speed is always positive (critical rule!)
    speed = abs(speed)
    
    operation = {
        "type": "RotateOperation",
        "speed": speed,
        "angle": angle
    }
    
    # Direction is determined by angle sign, NOT speed
    direction = "right" if angle > 0 else "left"
    return queue_operation(operation, f"Queued rotation {direction} at speed {speed} for {abs(angle)} degrees")


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


def multi_action(actions: list):
    """Execute multiple operations simultaneously.
    
    This allows Buddy to do multiple things at once, making interactions more fluid and natural.
    For example: moving while talking, rotating while speaking, etc.
    
    Parameter Rules:
    - actions: List of action dictionaries, each with 'type' and specific parameters
    
    Supported action types:
    - "move": Requires speed (positive) and distance (±)
    - "rotate": Requires speed (positive) and angle (±)
    - "talk": Requires message, optional volume
    - "head": Requires axis ("yes"/"no"), optional speed and angle
    - "mood": Requires mood (happy/sad/angry/etc.)
    
    Examples:
    - Move and talk: [{"type": "move", "speed": 100, "distance": 1.0}, 
                      {"type": "talk", "message": "I'm moving!"}]
    - Rotate and talk: [{"type": "rotate", "speed": 50, "angle": 90}, 
                        {"type": "talk", "message": "Turning right"}]
    - Talk, nod and smile: [{"type": "talk", "message": "Hello!"}, 
                            {"type": "head", "axis": "yes"}, 
                            {"type": "mood", "mood": "happy"}]
    """
    # Build list of operations
    operations = []
    action_descriptions = []
    
    for action in actions:
        action_type = action.get("type")
        
        if action_type == "move":
            speed = abs(action.get("speed", 100))
            distance = action.get("distance", 0)
            operations.append({
                "type": "MoveOperation",
                "speed": speed,
                "distance": distance
            })
            direction = "forward" if distance > 0 else "backward"
            action_descriptions.append(f"move {direction} {abs(distance)}m")
            
        elif action_type == "rotate":
            speed = abs(action.get("speed", 50))
            angle = action.get("angle", 0)
            operations.append({
                "type": "RotateOperation",
                "speed": speed,
                "angle": angle
            })
            direction = "right" if angle > 0 else "left"
            action_descriptions.append(f"rotate {direction} {abs(angle)}°")
            
        elif action_type == "talk":
            message = action.get("message", "")
            volume = action.get("volume", 300)
            operations.append({
                "type": "TalkOperation",
                "message": message,
                "volume": volume
            })
            action_descriptions.append(f"say '{message}'")
            
        elif action_type == "head":
            axis = action.get("axis", "yes")
            axis_value = "Yes" if axis.lower() == "yes" else "No"
            speed = action.get("speed", 40.0)
            angle = action.get("angle", 20.0)
            operations.append({
                "type": "HeadOperation",
                "speed": speed,
                "angle": angle,
                "axis": axis_value
            })
            head_action = "nod" if axis_value == "Yes" else "shake"
            action_descriptions.append(f"{head_action} head")
            
        elif action_type == "mood":
            mood = action.get("mood", "NEUTRAL")
            operations.append({
                "type": "MoodOperation",
                "mood": mood.upper()
            })
            action_descriptions.append(f"set mood to {mood}")
    
    # Create MultiOperation
    multi_operation = {
        "type": "MultiOperation",
        "operations": operations
    }
    
    # Create descriptive message
    description = " + ".join(action_descriptions)
    message = f"Queued multi-action: {description} ({len(operations)} operations)"
    
    return queue_operation(multi_operation, message)


def track_person(action: str = None, talk_message: str = None, mood: str = None):
    """Track a person by taking a photo and optionally executing a tracking action.
    
    This is the core building block for autonomous person tracking. The process:
    1. ALWAYS takes a photo first to see the current state
    2. Returns the image to Claude for visual analysis
    3. Claude decides the action based on person position in the image
    4. Executes the action (rotate OR move, NEVER both) with optional talk/mood
    
    Decision Logic (recommended for Claude):
    - Person on LEFT side → action="rotate_left" (turn to face them)
    - Person on RIGHT side → action="rotate_right" (turn to face them)
    - Person CENTERED + FAR → action="move_forward" (approach them)
    - Person CENTERED + CLOSE → action="stop" or "backup" (maintain distance)
    - Person NOT VISIBLE → action="search" (slow rotation to find them)
    
    IMPORTANT: This guarantees NO conflict between rotate and move since each action
    is executed separately. This respects the physical constraint of the robot.
    
    Parameter Rules:
    - action: Optional action to execute. If None, only returns photo for analysis.
    - talk_message: Optional message to say during action (makes tracking interactive)
    - mood: Optional mood to display during action (adds personality)
    
    Supported Actions:
    - "rotate_left": Turn left 30° at medium speed
    - "rotate_right": Turn right 30° at medium speed
    - "move_forward": Move forward 0.3m at normal speed
    - "backup": Move backward 0.2m at normal speed
    - "search": Slow rotation 45° left to search for person
    - "stop": No movement, only talk/mood (when centered and close)
    
    Examples:
    - track_person() 
      → Just take photo and return for Claude to analyze
    
    - track_person("rotate_left", "Je te vois à gauche!") 
      → Rotate left while announcing the action
    
    - track_person("move_forward", "J'arrive!", "happy") 
      → Move forward happily while talking
    
    - track_person("search", "Où es-tu?", "surprised")
      → Search with slow rotation while asking where they are
    
    Typical Tracking Loop:
    1. track_person() → Photo → Claude analyzes: "Person on left"
    2. track_person("rotate_left", "Je te vois!") → Rotate + talk
    3. track_person() → Photo → Claude analyzes: "Person centered but far"
    4. track_person("move_forward", "J'arrive!", "happy") → Move + talk + smile
    5. track_person() → Photo → Repeat...
    """
    # ALWAYS take a picture first to see current state
    log("Taking photo for person tracking...")
    photo_result = take_picture()
    
    # If no action specified, just return the photo for Claude to analyze
    if action is None:
        log("No action specified - returning photo for analysis")
        return photo_result
    
    # Build list of actions to execute via multi_action
    actions = []
    
    # Add movement/rotation based on action (NEVER both rotate and move!)
    if action == "rotate_left":
        actions.append({"type": "rotate", "speed": 50, "angle": -30})
        log("Action: Rotate left 30°")
        
    elif action == "rotate_right":
        actions.append({"type": "rotate", "speed": 50, "angle": 30})
        log("Action: Rotate right 30°")
        
    elif action == "move_forward":
        actions.append({"type": "move", "speed": 100, "distance": 0.3})
        log("Action: Move forward 0.3m")
        
    elif action == "backup":
        actions.append({"type": "move", "speed": 100, "distance": -0.2})
        log("Action: Backup 0.2m")
        
    elif action == "search":
        # Slow rotation to search for person
        actions.append({"type": "rotate", "speed": 30, "angle": -45})
        log("Action: Search with slow rotation")
        
    elif action == "stop":
        # No movement, just talk/mood if specified
        log("Action: Stop (no movement)")
        pass
    
    else:
        log(f"Unknown action: {action}")
        return photo_result + [TextContent(type="text", text=f"Error: Unknown action '{action}'")]
    
    # Add optional talk message
    if talk_message:
        actions.append({"type": "talk", "message": talk_message})
        log(f"Adding talk: {talk_message}")
    
    # Add optional mood
    if mood:
        actions.append({"type": "mood", "mood": mood})
        log(f"Adding mood: {mood}")
    
    # Execute actions if any
    if actions:
        multi_result = multi_action(actions)
        # Combine photo + separator + action result
        separator = [TextContent(type="text", text="\n--- Tracking Action Executed ---")]
        return photo_result + separator + multi_result
    else:
        # No actions (only "stop" with no talk/mood)
        return photo_result + [TextContent(type="text", text="Tracking: Stopped (no movement)")]


# --- Tool dispatch dictionary ---

TOOL_HANDLERS = {
    "move_buddy": move_buddy,
    "rotate_buddy": rotate_buddy,
    "speak": speak,
    "move_head": move_head,
    "set_mood": set_mood,
    "take_picture": take_picture,
    "multi_action": multi_action,
    "track_person": track_person,
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

