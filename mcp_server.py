"""
MCP Server for Buddy Robot Control

This server exposes Buddy robot controls to Claude Desktop via the MCP protocol.
It uses stdio mode for communication and delegates actual functionality to buddy_functions.py.

Architecture:
- Claude Desktop sends tool requests via stdio
- MCP Server processes requests using buddy_functions.py
- Operations are queued and executed by the Flask API
"""

import asyncio
import sys
import threading
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import Buddy functions
from buddy_functions import (
    init_shared_state,
    move_buddy,
    rotate_buddy,
    speak,
    move_head,
    set_mood,
    take_picture,
    multi_action,
    track_person,
    TOOL_HANDLERS
)

# Shared state - These will be initialized by api.py via init_shared_state()
# DO NOT create them here - that would create a separate queue!
# The queue created in api.py is the single source of truth.


def log(msg):
    """Log messages to stderr (stdout is reserved for MCP protocol)"""
    print(f"[MCP Server] {msg}", file=sys.stderr)


# Create MCP server instance
app = Server("buddy-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools for controlling Buddy.
    Claude Desktop will call this to discover available capabilities.
    """
    log("Listing available tools")
    return [
        Tool(
            name="move_buddy",
            description="Move Buddy forward or backward. IMPORTANT: Speed must always be positive. Direction is controlled by distance sign (+ forward, - backward). Example: move_buddy(speed=100, distance=-0.5) moves backward.",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "number",
                        "description": "Movement speed - MUST be positive (recommended: 50-200). Direction is NOT determined by speed.",
                        "minimum": 0,
                        "maximum": 500
                    },
                    "distance": {
                        "type": "number",
                        "description": "Distance to move in meters. POSITIVE = forward, NEGATIVE = backward. Example: 0.5 moves forward, -0.5 moves backward.",
                    }
                },
                "required": ["speed", "distance"]
            }
        ),
        Tool(
            name="rotate_buddy",
            description="Rotate Buddy left or right. IMPORTANT: Speed must always be positive. Direction is controlled by angle sign (+ right, - left). Example: rotate_buddy(speed=50, angle=-90) rotates left.",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "number",
                        "description": "Rotation speed - MUST be positive (recommended: 50-200). Direction is NOT determined by speed.",
                        "minimum": 0,
                        "maximum": 500
                    },
                    "angle": {
                        "type": "number",
                        "description": "Angle to rotate in degrees. POSITIVE = turn right, NEGATIVE = turn left. Example: 90 turns right, -90 turns left.",
                    }
                },
                "required": ["speed", "angle"]
            }
        ),
        Tool(
            name="speak",
            description="Make Buddy say something out loud. Use this for standalone speech. If you want Buddy to talk WHILE doing something else (moving, rotating), use multi_action instead. Perfect for greetings, announcements, or any verbal communication.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The text that Buddy should speak"
                    },
                    "volume": {
                        "type": "integer",
                        "description": "Volume level (100-500, default: 300)",
                        "minimum": 100,
                        "maximum": 500,
                        "default": 300
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="move_head",
            description="Make Buddy nod (yes) or shake (no) his head. Use 'yes' for agreement/approval or 'no' for disagreement/disapproval. Can be combined with other actions using multi_action (e.g., nod while saying 'Yes!')",
            inputSchema={
                "type": "object",
                "properties": {
                    "axis": {
                        "type": "string",
                        "description": "Head movement type",
                        "enum": ["yes", "no"]
                    },
                    "speed": {
                        "type": "number",
                        "description": "Movement speed (default: 40.0)",
                        "minimum": 0,
                        "maximum": 100,
                        "default": 40.0
                    },
                    "angle": {
                        "type": "number",
                        "description": "Movement angle (default: 20.0)",
                        "minimum": 0,
                        "maximum": 90,
                        "default": 20.0
                    }
                },
                "required": ["axis"]
            }
        ),
        Tool(
            name="set_mood",
            description="Change Buddy's facial expression/mood displayed on the screen. Use this to convey emotions visually. Can be combined with speech and gestures using multi_action for more expressive interactions (e.g., smile while saying 'Hello!')",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The mood/expression to display",
                        "enum": ["happy", "sad", "angry", "surprised", "neutral", "afraid", "disgusted", "contempt"]
                    }
                },
                "required": ["mood"]
            }
        ),
        Tool(
            name="take_picture",
            description="Capture and return the latest image from Buddy's camera. Returns the image with timestamp. Use this to see what Buddy sees, analyze the environment, or track a person.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="multi_action",
            description="Execute multiple actions SIMULTANEOUSLY. This makes Buddy more fluid and natural by doing several things at once. Examples: move while talking, rotate while speaking, greet someone (talk + nod + smile). Use this instead of calling individual tools sequentially when you want Buddy to multitask.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "description": "List of actions to execute simultaneously. Each action has a 'type' and its specific parameters.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "Type of action: 'move' (move forward/backward), 'rotate' (turn left/right), 'talk' (speak), 'head' (nod/shake), 'mood' (facial expression)",
                                    "enum": ["move", "rotate", "talk", "head", "mood"]
                                },
                                "speed": {
                                    "type": "number",
                                    "description": "Speed parameter (for move/rotate/head actions). Must be positive."
                                },
                                "distance": {
                                    "type": "number",
                                    "description": "Distance in meters (for move action). Positive = forward, negative = backward."
                                },
                                "angle": {
                                    "type": "number",
                                    "description": "Angle in degrees (for rotate/head actions). Positive = right/yes, negative = left/no."
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Text to speak (for talk action)"
                                },
                                "volume": {
                                    "type": "integer",
                                    "description": "Volume level 100-500 (for talk action, default: 300)"
                                },
                                "axis": {
                                    "type": "string",
                                    "description": "Head movement type (for head action): 'yes' = nod, 'no' = shake",
                                    "enum": ["yes", "no"]
                                },
                                "mood": {
                                    "type": "string",
                                    "description": "Facial expression (for mood action)",
                                    "enum": ["happy", "sad", "angry", "surprised", "neutral", "afraid", "disgusted", "contempt"]
                                }
                            },
                            "required": ["type"]
                        },
                        "minItems": 1
                    }
                },
                "required": ["actions"]
            }
        ),
        Tool(
            name="track_person",
            description="Track a person autonomously by taking photos and executing smart tracking actions. This is THE tool for person following! Process: 1) Takes photo automatically, 2) Returns image for your analysis, 3) You decide action based on person position, 4) Executes action safely (rotate OR move, NEVER both). Call repeatedly to track someone. Perfect for autonomous following, person interaction, or surveillance tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Tracking action to execute based on person position in image. Choose: 'rotate_left' if person on left, 'rotate_right' if on right, 'move_forward' if centered and far, 'backup' if too close, 'search' if not visible, 'stop' if perfectly positioned. If omitted, only takes photo for analysis.",
                        "enum": ["rotate_left", "rotate_right", "move_forward", "backup", "search", "stop"]
                    },
                    "talk_message": {
                        "type": "string",
                        "description": "Optional message to say WHILE executing action. Makes tracking interactive and friendly. Examples: 'Je te vois!', 'J'arrive!', 'Où es-tu?'"
                    },
                    "mood": {
                        "type": "string",
                        "description": "Optional mood/facial expression during action. Adds personality to tracking. Examples: 'happy' when approaching, 'surprised' when searching, 'neutral' for normal tracking.",
                        "enum": ["happy", "sad", "angry", "surprised", "neutral", "afraid", "disgusted", "contempt"]
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool execution requests from Claude.
    
    This function routes tool calls to the appropriate handler in buddy_functions.py
    All operations are queued and will be executed by the Flask API.
    """
    log(f"Tool called: {name} with arguments: {arguments}")
    
    # Check if tool exists
    if name not in TOOL_HANDLERS:
        error_msg = f"Unknown tool: {name}"
        log(f"ERROR: {error_msg}")
        return [TextContent(type="text", text=f"Error: {error_msg}")]
    
    try:
        # Call the appropriate handler from buddy_functions.py
        handler = TOOL_HANDLERS[name]
        result = handler(**arguments)
        log(f"Tool '{name}' executed successfully")
        return result
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        log(f"ERROR: {error_msg}")
        return [TextContent(type="text", text=f"Error: {error_msg}")]


async def run_server():
    """
    Main server entry point.
    Runs the MCP server using stdio transport.
    
    Note: Shared state (operation_queue, latest_image, queue_lock) must be
    initialized by api.py BEFORE calling this function via init_shared_state().
    """
    log("Starting Buddy MCP Server...")
    log("Shared state should already be initialized by api.py")
    
    # Run the server using stdio transport (standard for Claude Desktop)
    log("Server ready - waiting for Claude Desktop connection...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Entry point when running the server directly"""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        log("Server stopped by user")
    except Exception as e:
        log(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
