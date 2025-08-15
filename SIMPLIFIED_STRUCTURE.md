# Simplified File Structure

This document explains the new, simplified file structure that eliminates confusion and provides clear separation of concerns.

## 📁 File Structure

```
src/
├── cookie_client.py      # Cookie-based authentication client
├── token_client.py       # Token-based authentication client  
├── glean_mcp_server.py   # MCP server with auto-detection
└── glean_filter.py       # Response filtering utilities
```

## 🎯 Design Goals

1. **Simplicity**: Only 4 essential files in `src/`
2. **Clarity**: Each file has a single, clear purpose
3. **No Confusion**: No duplicate or overlapping functionality
4. **Docker Ready**: MCP server auto-detects authentication method

## 📋 File Descriptions

### `cookie_client.py`
- **Purpose**: Cookie-based authentication using browser session cookies
- **Class**: `GleanClient`
- **Endpoints**: Uses `/api/v1/` endpoints
- **Use Case**: Interactive development, browser-based workflows

### `token_client.py`  
- **Purpose**: Token-based authentication using API tokens
- **Class**: `TokenBasedGleanClient` (extends `GleanClient`)
- **Endpoints**: Uses `/rest/api/v1/` endpoints  
- **Use Case**: Server-to-server, production deployments, CI/CD

### `glean_mcp_server.py`
- **Purpose**: MCP server for Docker usage with auto-detection
- **Function**: `create_glean_client()` - automatically chooses auth method
- **Logic**: Prefers token auth if both are available
- **Use Case**: Docker containers, MCP protocol integration

### `glean_filter.py`
- **Purpose**: Response filtering and formatting utilities
- **Use Case**: Shared by both client types

## 🔧 Usage Patterns

### Direct Client Usage

```python
# Cookie-based
from src.cookie_client import GleanClient
client = GleanClient(base_url, cookies)

# Token-based  
from src.token_client import TokenBasedGleanClient
client = TokenBasedGleanClient(base_url, api_token)
```

### Auto-Detection (MCP Server)

```python
from src.glean_mcp_server import create_glean_client
client = create_glean_client()  # Uses env vars to choose
```

### Environment Variables

```bash
# Authentication (choose one)
export GLEAN_API_TOKEN="your-token"     # Preferred
export GLEAN_COOKIES="your-cookies"     # Alternative

# Instance configuration
export GLEAN_BASE_URL="https://company-be.glean.com"
export GLEAN_INSTANCE="company"         # Alternative to base URL
```

## 🔄 Auto-Detection Logic

The MCP server's `create_glean_client()` function uses this logic:

1. **Check for token**: If `GLEAN_API_TOKEN` is set → `TokenBasedGleanClient`
2. **Check for cookies**: If `GLEAN_COOKIES` is set → `GleanClient`  
3. **Both available**: Prefers token-based authentication
4. **Neither available**: Raises clear error message

## 🐳 Docker Integration

The MCP server is designed for Docker usage:

```dockerfile
# Set authentication in your Docker environment
ENV GLEAN_API_TOKEN=your-token
ENV GLEAN_BASE_URL=https://company-be.glean.com

# Run the MCP server
CMD ["python", "src/glean_mcp_server.py"]
```

## 🧪 Testing

Run the simple example to test the structure:

```bash
python examples/simple_usage.py
```

## ✅ Benefits of This Structure

1. **No Package Complexity**: No confusing package hierarchy
2. **Clear Naming**: `cookie_client.py` vs `token_client.py` is obvious
3. **Single Responsibility**: Each file does one thing well
4. **Easy Maintenance**: Simple to understand and modify
5. **Docker Ready**: MCP server handles auth detection automatically
6. **Backward Compatible**: Existing code can still import directly

## 🚀 Migration from Old Structure

If you were using the old package structure:

**Old:**
```python
from glean_mcp import TokenBasedGleanClient, create_client
```

**New:**
```python
from src.token_client import TokenBasedGleanClient
from src.glean_mcp_server import create_glean_client as create_client
```

## 📖 Examples

See `examples/simple_usage.py` for complete working examples of:
- Direct cookie client usage
- Direct token client usage  
- Auto-detection via MCP server
- Error handling and configuration checking

This simplified structure eliminates confusion while maintaining all functionality and providing clear separation between authentication methods.
