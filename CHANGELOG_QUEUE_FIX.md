# Queue Sharing Fix - Changelog

**Date**: 2025-12-16  
**Issue**: Operations sent from Claude Desktop via MCP were not being received by Buddy robot  
**Status**: ✅ FIXED

## Problem Description

When sending commands through Claude Desktop (e.g., "Salut la team"), the operation was successfully queued by the MCP server but never retrieved by the Flask API's `/operation` endpoint.

**Root Cause**: `mcp_server.py` and `api.py` were creating **two separate queues**:
- Queue A: Created in `mcp_server.py` (line 34) - MCP wrote here
- Queue B: Created in `api.py` (line 26) - Flask read here
- Result: Operations went into Queue A, Flask checked Queue B → nothing found!

## Solution Implemented (Option 1 - KISS Principle)

### Files Modified

#### 1. `mcp_server.py`
**Changes:**
- ❌ Removed local queue creation (lines 34-36):
  ```python
  # REMOVED:
  operation_queue = deque()
  latest_image = {"base64": None, "timestamp": None}
  queue_lock = threading.Lock()
  ```
- ❌ Removed unused `deque` import
- ✏️ Modified `run_server()` to remove redundant `init_shared_state()` call
- ✅ Added clarifying comments about shared state initialization

**Rationale**: The queue should only be created once in `api.py`. The MCP server will use the queue passed via `init_shared_state()`.

#### 2. `buddy_functions.py`
**Changes:**
- ✅ Added detailed logging in `queue_operation()`:
  - Queue size after append
  - Queue ID (memory address) for debugging
  
**Rationale**: These logs help verify that both MCP and Flask are using the same queue object.

#### 3. `api.py`
**Changes:**
- ✅ Enhanced `/operation` endpoint with detailed logging:
  - Queue size when polled
  - Queue ID for debugging
  - Whether an operation was returned or queue was empty
- ✅ Added thread-safe lock usage with `with queue_lock:`
- ✅ Fixed HTTP status code (200 instead of 400 when queue is empty)

**Rationale**: Better observability to confirm operations flow correctly.

## Architecture After Fix

```
┌─────────────────┐
│  Claude Desktop │
└────────┬────────┘
         │ MCP Protocol (stdio)
         ▼
┌─────────────────┐
│  mcp_server.py  │ ← Uses shared queue via init_shared_state()
└────────┬────────┘
         │
         │ Writes to
         ▼
    ┌────────────┐
    │   QUEUE    │ ← Single queue created in api.py
    │  (shared)  │
    └────────────┘
         ▲
         │ Reads from
         │
┌────────┴────────┐
│     api.py      │
│  /operation     │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Buddy Robot   │ (polls /operation endpoint)
└─────────────────┘
```

## How to Test

1. **Restart the server** (important!):
   ```bash
   # Stop any running instance (Ctrl+C)
   # Restart Claude Desktop to reload MCP server
   ```

2. **Send a command** via Claude Desktop:
   ```
   "Dis bonjour Buddy"
   ```

3. **Check the logs** - You should see:
   ```
   [MCP Server] Queued: {"type": "TalkOperation", ...}
   [MCP Server] Queue size after append: 1 (Queue ID: 123456789)
   [/operation] Polled - Queue size: 1 (Queue ID: 123456789)  ← Same ID!
   [/operation] Returning operation: {...}
   ```

4. **⚠️ Critical**: The Queue IDs must be **identical**. If they're different, the queues are still separate.

## Expected Behavior

- ✅ Operations sent from Claude appear in `/operation` endpoint
- ✅ Buddy robot receives and executes commands
- ✅ Queue IDs in logs are identical
- ✅ Queue size decrements after `/operation` poll

## Debugging Tips

If it still doesn't work:

1. **Check Queue IDs**: They MUST be identical in both logs
2. **Check initialization order**: `api.py` creates queue → calls `init_shared_state()` → starts MCP server
3. **Restart Claude Desktop**: MCP server needs to reload after code changes
4. **Check for import errors**: Make sure all imports are working

## Why Can't We Remove mcp_server.py?

`mcp_server.py` is **essential** because:
1. It's the MCP protocol interface that Claude Desktop connects to
2. It defines the tools (speak, move, rotate, etc.) available to Claude
3. It handles stdio communication with Claude Desktop
4. Without it, Claude cannot communicate with Buddy at all

The fix was NOT to remove `mcp_server.py`, but to ensure it uses the **same queue** as `api.py`.

## Notes

- All logging goes to `stderr` (stdout is reserved for MCP JSON protocol)
- The queue is thread-safe thanks to `queue_lock`
- This fix follows KISS (Keep It Simple Stupid) and YAGNI principles
