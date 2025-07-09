# Glean MCP Server - Requirements & Setup

## Overview
This repository contains a Docker-based Model Context Protocol (MCP) server that provides search functionality for Glean knowledge bases. The server is designed to be hosted on GitHub Container Registry for easy deployment.

## Core Requirements

### 1. MCP Server Functionality
- ✅ Implements MCP protocol for AI assistant integration
- ✅ Provides `glean_search` tool for querying Glean API
- ✅ Supports configurable search parameters (query, page_size, max_snippet_size)
- ✅ Returns structured JSON responses with search results

### 2. Glean API Integration
- ✅ Authenticates using browser cookies
- ✅ Supports any Glean instance via configurable base URL
- ✅ Handles search requests with proper headers and payload structure
- ✅ Error handling for API failures

### 3. Docker & Container Registry
- ✅ Multi-architecture Docker image (amd64, arm64)
- ✅ Non-root user execution for security
- ✅ Health checks and proper signal handling
- 🔄 GitHub Actions workflow for automated builds
- 🔄 Publishing to GitHub Container Registry (ghcr.io)

### 4. Configuration
- ✅ Environment-based configuration
- ✅ Required: `GLEAN_BASE_URL` and `GLEAN_COOKIES`
- ✅ Optional: `LOG_LEVEL`
- ✅ Example configuration file (.env.example)

## User Requirements
Users need to provide:
1. **Base URL**: Their Glean instance URL (e.g., `https://company.glean.com`)
2. **Cookies**: Authentication cookies from browser developer tools

All other parameters use sensible defaults but can be customized.

## Next Steps
- [ ] Add GitHub Actions workflow for automated Docker builds
- [ ] Verify GitHub Container Registry publishing
- [ ] Update documentation for container registry usage
- [ ] Test end-to-end deployment workflow