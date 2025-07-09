#!/bin/bash

# Script to run Glean MCP server for VS Code
# This can be called from any VS Code workspace

# Path to your Glean MCP server directory
GLEAN_MCP_DIR="/path/to/your/glean-mcp-server"

# Check if container is already running
if docker ps | grep -q "glean-mcp-server"; then
    echo "Using existing Glean MCP server container..."
    docker exec -i glean-mcp-server python src/glean_mcp_server.py
else
    echo "Starting new Glean MCP server container..."
    docker run --rm -i \
        --env-file "$GLEAN_MCP_DIR/.env" \
        glean-mcp-server-glean-mcp-server:latest
fi
