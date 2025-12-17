# Docker Quick Start Guide

## 🚀 Fast Track: Get Buddy Running in 5 Minutes

### Step 1: Start the Docker Container

```bash
docker-compose up -d
```

That's it! The server is now running on port 5000.

### Step 2: Expose with ngrok

```bash
# Expose the MCP server port (5001)
ngrok http 5001
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

**Note**: We use port 5001 for MCP/AI integrations. Port 5000 is for the Buddy robot's API.

### Step 3: Choose Your AI Platform

#### Option A: ChatGPT Connector

1. Open ChatGPT → Settings → Connectors → Create
2. Fill in:
   - **Name**: Buddy Robot
   - **Description**: Control Buddy robot
   - **URL**: `https://abc123.ngrok-free.app/mcp`
3. Click Create
4. In ChatGPT, add your Buddy connector and try commands

#### Option B: Claude API

```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_KEY")
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Move Buddy forward 1 meter"}],
    mcp_servers=[{
        "type": "url",
        "url": "https://abc123.ngrok-free.app/sse",
        "name": "buddy-robot"
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "buddy-robot"}],
    betas=["mcp-client-2025-11-20"]
)
```

### Step 4: Test It

Try these commands:
- "Move Buddy forward 1 meter at speed 100"
- "Make Buddy say 'Hello World'"
- "Change Buddy's mood to happy"
- "Take a picture with Buddy"

## 🛠️ Common Commands

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Check status
docker-compose ps
```

## 🔌 Integration Endpoints

| Platform | Endpoint | Setup |
|----------|----------|-------|
| **Claude API** | `/sse` | Programmatic via API |
| **ChatGPT** | `/mcp` | Web UI in Settings |
| **Claude Desktop** | stdio | Config file (local) |

## 📝 Operation Types

The Buddy robot polls `/operation` and receives JSON like:

```json
{
  "type": "MoveOperation",
  "speed": 100,
  "distance": 1.5
}
```

```json
{
  "type": "TalkOperation",
  "message": "Hello!",
  "volume": 300
}
```

```json
{
  "type": "MoodOperation",
  "mood": "HAPPY"
}
```

## 🔍 Troubleshooting

**Container won't start?**
```bash
docker-compose logs -f
```

**ngrok not working?**
- Make sure port 5000 is accessible
- Check firewall settings
- Try: `curl http://localhost:5000/`

**ChatGPT can't connect?**
- URL must end with `/mcp` for ChatGPT
- URL must end with `/sse` for Claude API
- Use HTTPS from ngrok, not HTTP
- Verify ngrok is still running

## 🧪 Testing Your Setup

Before testing with Buddy, verify your client works with the official example server:

**Official "Everything" Server**: [https://example-server.modelcontextprotocol.io/mcp](https://example-server.modelcontextprotocol.io/mcp)

**Test with Claude API**:
```python
mcp_servers=[{
    "type": "url",
    "url": "https://example-server.modelcontextprotocol.io/sse",
    "name": "test"
}]
```

**Test with ChatGPT**: Use URL `https://example-server.modelcontextprotocol.io/mcp`

If the example server works but Buddy doesn't, check your Buddy server logs.

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

**Reference Implementation**: [github.com/modelcontextprotocol/servers/tree/main/src/everything](https://github.com/modelcontextprotocol/servers/tree/main/src/everything)

