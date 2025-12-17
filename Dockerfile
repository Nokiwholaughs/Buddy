# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api.py .
COPY mcp_server.py .
COPY buddy_functions.py .
COPY mcp_http_server.py .
COPY start_servers.py .

# Create directory for image storage
RUN mkdir -p /app/data

# Expose ports
# 5000 - Flask API (robot control endpoints)
# 5001 - MCP/SSE endpoints
EXPOSE 5000 5001

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run both servers
CMD ["python", "start_servers.py"]

