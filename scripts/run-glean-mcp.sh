#!/bin/bash

# Simple script to run Glean MCP server
# Set your environment variables before running this script

docker run --rm -i \
    -e GLEAN_BASE_URL="${GLEAN_BASE_URL}" \
    -e GLEAN_COOKIES="${GLEAN_COOKIES}" \
    ghcr.io/alankyshum/glean-mcp-server:latest
