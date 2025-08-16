# Token-based Authentication Addon

This document describes the token-based authentication addon for the Glean MCP server, which provides an alternative to cookie-based authentication using Glean API tokens.

## Overview

The `glean_token_based_api_calls.py` module provides a polymorphic addon that extends the base `GleanClient` to support Bearer token authentication. This is useful for:

- Server-to-server integrations
- Automated scripts and CI/CD pipelines
- Environments where browser cookies are not available
- More secure authentication workflows

## Key Differences

### API Endpoints

The token-based client uses different API endpoints compared to the cookie-based client:

**Token-based endpoints:**
- Search: `POST {base}/rest/api/v1/search`
- Chat: `POST {base}/rest/api/v1/chat`
- Read documents: `POST {base}/rest/api/v1/getdocuments`

**Cookie-based endpoints:**
- Search: `POST {base}/api/v1/search`
- Chat: `POST {base}/api/v1/chat`
- Read documents: `POST {base}/api/v1/getdocuments`

### Authentication

- **Token-based**: Uses `Authorization: Bearer <token>` header
- **Cookie-based**: Uses `Cookie: <cookie-string>` header with browser-like headers

### Payload Structure

Token-based API calls use simplified payloads compared to cookie-based calls, which require more complex browser-like payloads.

## Setup

### Environment Variables

```bash
# Required: Your Glean API token
export GLEAN_API_TOKEN="your-api-token-here"

# Optional: Base URL (if not provided, derived from instance)
export GLEAN_BASE_URL="https://your-company-be.glean.com"

# Optional: Instance name (default: "linkedin")
export GLEAN_INSTANCE="your-company"
```

### Obtaining API Tokens

1. Log into your Glean instance as an administrator
2. Navigate to Admin Settings → API Tokens
3. Create a new API token with appropriate permissions
4. Copy the token and set it as `GLEAN_API_TOKEN`

## Usage

### Async Client (Recommended)

```python
from glean_mcp import TokenBasedGleanClient, create_client

async def example():
    # Create token-based client from environment variables
    client = create_client("token")
    # Or explicitly create token client
    # client = TokenBasedGleanClient(base_url, api_token)

    try:
        # Search
        results = await client.search("onboarding docs", page_size=10)
        print(f"Found {len(results.get('results', []))} results")

        # Chat
        response = await client.chat(message="What is our vacation policy?")
        print(f"Response: {response}")

        # Read documents
        docs = await client.read_documents([
            {"url": "https://example.com/doc"},
            {"id": "document-id"}
        ])
        print(f"Retrieved {len(docs.get('documents', {}))} documents")

    finally:
        await client.close()
```

### Synchronous API (Auto-detects Authentication)

```python
from glean_mcp import glean_search, glean_chat, glean_read_documents

# These functions automatically detect whether to use token or cookie auth
# based on environment variables (prefers token if both are available)

# Search
search_result = glean_search("team structure", page_size=5)
print(search_result)  # JSON string

# Chat
chat_result = glean_chat("How do I submit expenses?")
print(chat_result)  # Formatted string

# Read documents
docs_result = glean_read_documents([{"url": "https://example.com/doc"}])
print(docs_result)  # JSON string
```

### Auto-detection

```python
from glean_mcp import create_client

# Automatically choose token or cookie auth based on environment
client = create_client("auto")  # or just create_client()

# Or explicitly specify
token_client = create_client("token")
cookie_client = create_client("cookie")
```

## Error Handling

### TokenExpiredError

```python
from glean_mcp import TokenExpiredError, create_client

try:
    client = create_client("token")
    results = await client.search("query")
except TokenExpiredError as e:
    print(f"Token expired: {e}")
    # Handle token renewal
```

### Token Renewal Callback

```python
from glean_mcp import TokenBasedGleanClient

def renew_token():
    # Your token renewal logic here
    new_token = get_new_token_from_somewhere()
    return new_token

client = TokenBasedGleanClient(base_url, api_token, token_renewal_callback=renew_token)
```

## Integration with MCP Server

To use token-based authentication in the MCP server, modify your server configuration:

```python
# In your MCP server code
from glean_mcp import create_client

# Use auto-detection to support both auth types
client = create_client("auto")  # or just create_client()
```

This allows the same MCP server to work with either token-based or cookie-based authentication depending on which environment variables are set.

### Using the Synchronous API in MCP Tools

```python
from glean_mcp import glean_search, glean_chat, glean_read_documents

# These functions automatically handle auth detection
def search_tool(query: str) -> str:
    return glean_search(query, page_size=10)

def chat_tool(message: str) -> str:
    return glean_chat(message)
```

## Security Considerations

1. **Token Storage**: Store API tokens securely, preferably in environment variables or secure key management systems
2. **Token Rotation**: Implement regular token rotation policies
3. **Permissions**: Use tokens with minimal required permissions
4. **HTTPS**: Always use HTTPS endpoints (enforced by the client)
5. **Logging**: Avoid logging tokens in application logs

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Token is invalid or expired
   - Verify token is correct
   - Check if token has expired
   - Ensure token has required permissions

2. **403 Forbidden**: Token lacks required permissions
   - Contact your Glean administrator to grant appropriate permissions

3. **Connection Issues**:
   - Verify `GLEAN_BASE_URL` is correct
   - Check network connectivity
   - Ensure HTTPS is used

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your client code here
```

## Examples

See `examples/token_based_example.py` for complete working examples demonstrating:
- Async client usage
- Synchronous wrapper functions
- Auto-detection
- Error handling
- Token renewal

## API Reference

### Classes

- `TokenBasedGleanClient`: Main client class extending `GleanClient`
- `TokenExpiredError`: Exception raised when token is invalid/expired

### Functions

- `create_token_based_client()`: Factory function to create token-based client
- `get_client_for_auth_type()`: Factory function with auth type selection
- `glean_search_with_token()`: Synchronous search function
- `glean_chat_with_token()`: Synchronous chat function
- `glean_read_documents_with_token()`: Synchronous document reading function
