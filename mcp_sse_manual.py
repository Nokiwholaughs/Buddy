"""
Manual MCP SSE implementation as a backup.
This bypasses the MCP library's SSE transport and implements it directly.
"""

import json
import asyncio
import sys
from mcp_server import app as mcp_app


def log(msg):
    print(f"[Manual SSE] {msg}", file=sys.stderr)


class ManualMCPSSE:
    """Manually implement MCP over SSE"""
    
    async def handle_mcp_sse(self, scope, receive, send):
        """Handle MCP SSE connection manually"""
        log("Starting manual MCP SSE handler")
        
        # Send SSE headers
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/event-stream'],
                [b'cache-control', b'no-cache'],
                [b'connection', b'keep-alive'],
                [b'access-control-allow-origin', b'*'],
            ],
        })
        
        log("SSE headers sent")
        
        # Send initial endpoint event
        endpoint_url = f"{scope['scheme']}://{dict(scope['headers']).get(b'host', b'localhost').decode()}/mcp/messages"
        endpoint_event = f'event: endpoint\ndata: {json.dumps({"endpoint": endpoint_url})}\n\n'
        
        await send({
            'type': 'http.response.body',
            'body': endpoint_event.encode(),
            'more_body': True,
        })
        
        log(f"Sent endpoint event: {endpoint_url}")
        
        # Create message queue for bidirectional communication
        from asyncio import Queue
        read_queue = Queue()
        write_queue = Queue()
        
        # Start background task to handle MCP protocol
        async def mcp_handler():
            """Run MCP server"""
            try:
                # Create simple stream interfaces
                class QueueReader:
                    async def receive(self):
                        return await read_queue.get()
                
                class QueueWriter:
                    async def send(self, msg):
                        await write_queue.put(msg)
                
                reader = QueueReader()
                writer = QueueWriter()
                
                log("Running MCP app")
                await mcp_app.run(reader, writer, mcp_app.create_initialization_options())
                log("MCP app finished")
                
            except Exception as e:
                log(f"Error in MCP handler: {e}")
                import traceback
                log(traceback.format_exc())
        
        # Start MCP handler
        mcp_task = asyncio.create_task(mcp_handler())
        
        # Keep connection alive and forward messages
        try:
            while not mcp_task.done():
                # Send messages from MCP to client
                try:
                    msg = await asyncio.wait_for(write_queue.get(), timeout=1.0)
                    event_data = f'event: message\ndata: {json.dumps(msg)}\n\n'
                    await send({
                        'type': 'http.response.body',
                        'body': event_data.encode(),
                        'more_body': True,
                    })
                    log(f"Sent message: {msg}")
                except asyncio.TimeoutError:
                    # Send keepalive
                    await send({
                        'type': 'http.response.body',
                        'body': b': keepalive\n\n',
                        'more_body': True,
                    })
                
        except Exception as e:
            log(f"Error in SSE loop: {e}")
            import traceback
            log(traceback.format_exc())
        finally:
            # Close the response
            await send({
                'type': 'http.response.body',
                'body': b'',
                'more_body': False,
            })
            log("SSE connection closed")


manual_sse = ManualMCPSSE()


