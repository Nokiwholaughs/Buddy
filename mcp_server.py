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
            description="Move Buddy forward or backward. Use positive distance for forward, negative for backward.",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "number",
                        "description": "Movement speed (recommended: 50-200)",
                        "minimum": 0,
                        "maximum": 500
                    },
                    "distance": {
                        "type": "number",
                        "description": "Distance to move in meters. Positive = forward, negative = backward",
                    }
                },
                "required": ["speed", "distance"]
            }
        ),
        Tool(
            name="rotate_buddy",
            description="Rotate Buddy left or right. Use positive angle for right, negative for left.",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "number",
                        "description": "Rotation speed (recommended: 50-200)",
                        "minimum": 0,
                        "maximum": 500
                    },
                    "angle": {
                        "type": "number",
                        "description": "Angle to rotate in degrees. Positive = right, negative = left",
                    }
                },
                "required": ["speed", "angle"]
            }
        ),
        Tool(
            name="speak",
            description="Make Buddy say something out loud. Perfect for monologues, greetings, or any speech!",
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
            description="Make Buddy nod (yes) or shake (no) his head.",
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
            description="Change Buddy's facial expression/mood displayed on the screen.",
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
            description="Capture and return the latest image from Buddy's camera. Returns the image with timestamp.",
            inputSchema={
                "type": "object",
                "properties": {},
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
