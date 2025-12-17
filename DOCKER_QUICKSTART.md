# Docker Quick Start Guide

## 🚀 Fast Track: Get Buddy Running in 5 Minutes

### Step 1: Start the Docker Container

```bash
docker-compose up -d
```

That's it! The server is now running on port 5000.

### Step 2: Expose with ngrok

```bash
ngrok http 5000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### Step 3: Connect to ChatGPT

1. Open ChatGPT → Settings → Connectors → Create
2. Fill in:
   - **Name**: Buddy Robot
   - **Description**: Control Buddy robot
   - **URL**: `https://abc123.ngrok-free.app/mcp`
3. Click Create

### Step 4: Test It

In ChatGPT, add your Buddy connector and try:
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
- URL must end with `/mcp`
- Use HTTPS from ngrok, not HTTP
- Verify ngrok is still running

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

