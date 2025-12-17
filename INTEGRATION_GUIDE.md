# Buddy Robot MCP Integration Guide

This guide covers all the ways to integrate Buddy Robot with AI platforms via the Model Context Protocol (MCP).

## 🌐 Supported Platforms

| Platform | Transport | Endpoint | Setup Type |
|----------|-----------|----------|------------|
| **Claude API** | HTTP/SSE | `/sse` | Programmatic |
| **ChatGPT** | HTTP/SSE | `/mcp` | Web UI |
| **Claude Desktop** | stdio | N/A | Config File |

## 🔧 Prerequisites

1. Docker and Docker Compose installed
2. ngrok or Cloudflare Tunnel account (for public HTTPS)
3. API keys for your chosen platform

## 📋 Setup Steps

### 1. Start the Server

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using Docker
docker build -t buddy-mcp-server .
docker run -d -p 5000:5000 --name buddy-server buddy-mcp-server
```

### 2. Expose Publicly

```bash
# Using ngrok
ngrok http 5000

# Using Cloudflare Tunnel
cloudflared tunnel --url http://localhost:5000
```

You'll get a public HTTPS URL like `https://abc123.ngrok-free.app`

## 🤖 Platform-Specific Integration

### Claude API (Messages API with MCP Connector)

**Endpoint**: `https://your-url.ngrok-free.app/sse`

**Documentation**: [Claude MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)

**Python Example**:

```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")

response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": "Move Buddy forward 1 meter at speed 100, then make him say hello"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://your-url.ngrok-free.app/sse",
        "name": "buddy-robot",
        # Optional: "authorization_token": "YOUR_TOKEN"
    }],
    tools=[{
        "type": "mcp_toolset",
        "mcp_server_name": "buddy-robot"
    }],
    betas=["mcp-client-2025-11-20"]
)

print(response.content)
```

**Features**:
- ✅ Programmatic control
- ✅ Tool filtering (allowlist/denylist)
- ✅ Multiple MCP servers per request
- ✅ Bearer token authentication support
- ✅ Per-tool configuration

**Advanced: Tool Filtering**:

```python
# Only enable specific tools
tools=[{
    "type": "mcp_toolset",
    "mcp_server_name": "buddy-robot",
    "default_config": {
        "enabled": False  # Disable all by default
    },
    "configs": {
        "move_buddy": {"enabled": True},
        "speak": {"enabled": True}
    }
}]
```

### ChatGPT (Custom Connectors)

**Endpoint**: `https://your-url.ngrok-free.app/mcp`

**Setup Steps**:

1. Open ChatGPT
2. Navigate to **Settings** → **Connectors** → **Create**
3. Fill in:
   - **Connector name**: Buddy Robot Controller
   - **Description**: Control and interact with Buddy robot - move, speak, change moods, take pictures
   - **Connector URL**: `https://your-url.ngrok-free.app/mcp`
4. Click **Create**
5. Verify tools appear in the connector details

**Usage**:

1. Start a new chat
2. Click the **+** button
3. Select "Buddy Robot Controller"
4. Send commands like:
   - "Move Buddy forward 2 meters"
   - "Make Buddy happy and say 'I love working!'"
   - "Take a picture with Buddy's camera"

**Features**:
- ✅ Easy web UI setup
- ✅ No coding required
- ✅ Visual tool discovery
- ✅ Integrated in ChatGPT interface

### Claude Desktop (Local stdio)

**Transport**: stdio (standard input/output)

**Setup Steps**:

1. Locate your Claude Desktop config file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the Buddy server:

```json
{
    "mcpServers": {
        "buddy-robot": {
            "command": "python",
            "args": ["C:\\path\\to\\api.py"],
            "description": "Control Buddy robot - move, speak, change mood, take pictures"
        }
    }
}
```

3. Restart Claude Desktop

**Features**:
- ✅ Local execution (no public exposure needed)
- ✅ Automatic startup with Claude Desktop
- ✅ Integrated in chat interface

**Note**: This mode runs the server in stdio mode (not HTTP). The Flask API still runs in the background for the Buddy robot to poll operations.

## 🛠️ Available MCP Tools

All platforms have access to these tools:

### `move_buddy`

Move Buddy forward or backward.

**Parameters**:
- `speed` (number, 0-500): Movement speed
- `distance` (number): Distance in meters (+ forward, - backward)

**Example**: "Move Buddy forward 1.5 meters at speed 100"

### `rotate_buddy`

Rotate Buddy left or right.

**Parameters**:
- `speed` (number, 0-500): Rotation speed
- `angle` (number): Angle in degrees (+ right, - left)

**Example**: "Rotate Buddy 90 degrees to the right at speed 75"

### `speak`

Make Buddy say something.

**Parameters**:
- `message` (string): Text to speak
- `volume` (integer, 100-500, default 300): Volume level

**Example**: "Make Buddy say 'Hello, I am Buddy!'"

### `move_head`

Make Buddy nod or shake head.

**Parameters**:
- `axis` (string): "yes" for nod, "no" for shake
- `speed` (number, 0-100, default 40): Movement speed
- `angle` (number, 0-90, default 20): Movement angle

**Example**: "Make Buddy nod his head"

### `set_mood`

Change Buddy's facial expression.

**Parameters**:
- `mood` (string): happy, sad, angry, surprised, neutral, afraid, disgusted, contempt

**Example**: "Change Buddy's mood to happy"

### `take_picture`

Capture and return the latest image from Buddy's camera.

**Parameters**: None

**Example**: "Take a picture with Buddy's camera and show it to me"

## 🔐 Authentication (Optional)

### Adding Bearer Token Authentication

If you want to secure your MCP endpoints:

1. **Modify `api.py`** to check for authorization header:

```python
def check_auth():
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {os.getenv('MCP_TOKEN')}":
        return False
    return True

@app.route("/sse", methods=['GET', 'POST'])
def sse_endpoint():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    # ... rest of the handler
```

2. **Set environment variable** in `docker-compose.yml`:

```yaml
environment:
  - MCP_TOKEN=your_secret_token_here
```

3. **Use in Claude API**:

```python
mcp_servers=[{
    "type": "url",
    "url": "https://your-url.ngrok-free.app/sse",
    "name": "buddy-robot",
    "authorization_token": "your_secret_token_here"
}]
```

## 📊 Architecture Comparison

### Claude API (Programmatic)
```
Your Code → Claude API → ngrok → Docker → /sse → MCP Server → Buddy
```

**Pros**: 
- Full programmatic control
- Tool filtering
- Can integrate into existing apps

**Cons**: 
- Requires coding
- Need API key management

### ChatGPT (Web UI)
```
ChatGPT UI → ChatGPT Backend → ngrok → Docker → /mcp → MCP Server → Buddy
```

**Pros**: 
- No coding required
- Easy setup
- Visual interface

**Cons**: 
- Web UI only
- Less programmatic control

### Claude Desktop (Local)
```
Claude Desktop → stdio → api.py → MCP Server → Buddy
```

**Pros**: 
- No public exposure needed
- Automatic startup
- Integrated experience

**Cons**: 
- Local machine only
- Tied to desktop app

## 🧪 Testing

### Test Endpoints

```bash
# Test Flask API
curl http://localhost:5000/

# Test MCP endpoint (ChatGPT)
curl http://localhost:5000/mcp

# Test SSE endpoint (Claude API)
curl http://localhost:5000/sse

# Test operation polling (Buddy robot)
curl http://localhost:5000/operation
```

### Test with MCP Inspector

```bash
# Install and run MCP Inspector
npx @modelcontextprotocol/inspector

# Configure:
# - Transport: SSE or Streamable HTTP
# - URL: http://localhost:5000/sse (or /mcp)
# - Test tool calls interactively
```

### Compare with Official Example Server

The MCP organization provides a reference "Everything" server that you can use to compare behavior:

**Hosted Example**: [https://example-server.modelcontextprotocol.io/mcp](https://example-server.modelcontextprotocol.io/mcp)

**Source Code**: [github.com/modelcontextprotocol/servers/tree/main/src/everything](https://github.com/modelcontextprotocol/servers/tree/main/src/everything)

This reference server demonstrates all MCP features and can help verify that your client setup is working correctly before testing with the Buddy server.

## 🐛 Troubleshooting

### "MCP SSE transport not available"

```bash
# Ensure mcp package is installed
docker exec buddy-server pip list | grep mcp

# Check Python version (needs 3.11+)
docker exec buddy-server python --version
```

### Connection Refused

```bash
# Check if container is running
docker ps | grep buddy

# Check logs
docker logs buddy-server

# Verify port is exposed
netstat -an | grep 5000
```

### Tools Not Appearing

1. Check server logs for errors
2. Verify MCP endpoint is accessible
3. Test with MCP Inspector
4. Check tool configuration (allowlist/denylist)

### Claude API 400 Error

- Verify beta header: `"anthropic-beta": "mcp-client-2025-11-20"`
- Check URL format (must be HTTPS)
- Ensure `mcp_server_name` matches the name in `mcp_servers`

### ChatGPT Connector Creation Fails

- Verify URL is HTTPS (from ngrok)
- Ensure `/mcp` endpoint is accessible
- Check ngrok is still running
- Try creating connector again (may be temporary issue)

## 📚 Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude MCP Connector Docs](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)
- [OpenAI MCP Documentation](https://platform.openai.com/docs/mcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## 💡 Tips & Best Practices

1. **Use ngrok's static domains** for production to avoid URL changes
2. **Implement authentication** for public deployments
3. **Monitor logs** to debug tool execution
4. **Test locally first** before exposing publicly
5. **Use tool filtering** in Claude API to limit which operations are available
6. **Set up health checks** to monitor server availability
7. **Use volumes** for persistent image storage

## 🎯 Next Steps

1. ✅ Server is running
2. ✅ Endpoints are exposed
3. ✅ Integration is configured
4. 🎨 Customize tool descriptions for better AI understanding
5. 🔐 Add authentication for security
6. 📊 Monitor usage and performance
7. 🚀 Deploy to production environment

Happy automating with Buddy! 🤖

