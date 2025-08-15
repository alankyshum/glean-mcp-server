# Glean MCP Server & Python Package

Simple, focused implementation providing:

- Cookie-based client (`glean_mcp.cookie_client.GleanClient`) — uses browser session cookies
- Token-based client (`glean_mcp.token_client.TokenBasedGleanClient`) — uses API tokens for server-to-server auth
- MCP server (`python -m glean_mcp.server`) — auto-detects authentication method; ready for Docker

Links: [Releases](https://github.com/alankyshum/glean-mcp-server/releases) · [Cookie Guide](docs/COOKIES.md) · [Token Auth Guide](docs/TOKEN_BASED_AUTH.md)

## Install
```bash
pip install -U glean-mcp
```

## Package Layout
```
src/
└── glean_mcp/
    ├── cookie_client.py      # Cookie-based authentication client
    ├── token_client.py       # Token-based authentication client
    ├── server.py             # MCP server with auto-detection
    └── glean_filter.py       # Response filtering utilities
```

## Quick Start

### MCP Server (local or Docker)
The MCP server automatically detects your authentication method.

```bash
# Choose ONE (token preferred)
export GLEAN_API_TOKEN="your-api-token"   # preferred
# OR
export GLEAN_COOKIES="your-browser-cookies"

# Set your Glean instance
export GLEAN_BASE_URL="https://your-company-be.glean.com"  # or set GLEAN_INSTANCE=your-company

# Run the MCP server locally
python -m glean_mcp.server
```

Docker (example):
```bash
docker run --pull always --rm \
  -e GLEAN_API_TOKEN="$GLEAN_API_TOKEN" \
  -e GLEAN_BASE_URL="$GLEAN_BASE_URL" \
  ghcr.io/alankyshum/glean-mcp-server:latest
```
Upgrade: use `--pull always` (Docker) or `pip install -U glean-mcp` (pip).

### Library Usage (async)

Cookie-based:
```python
from glean_mcp import GleanClient

client = GleanClient(base_url, cookies)
results = await client.search("onboarding docs")
await client.close()
```

Token-based:
```python
from glean_mcp import TokenBasedGleanClient

client = TokenBasedGleanClient(base_url, api_token)
results = await client.search("onboarding docs")
await client.close()
```

Auto-detection (same logic as server):
```python
from glean_mcp import create_glean_client

client = create_glean_client()  # Uses env vars; prefers token
results = await client.search("onboarding docs")
await client.close()
```

## Authentication

Two supported methods:

### 🍪 Cookies (original)
- Use browser cookies from your Glean session
- Requires `GLEAN_COOKIES`
- Uses `/api/v1/` endpoints
- See [Cookie Guide](docs/COOKIES.md)

### 🔑 Token (recommended)
- Use Glean API tokens for server-to-server authentication
- Requires `GLEAN_API_TOKEN`
- Uses `/rest/api/v1/` endpoints
- More secure for automated/production environments
- See [Token Auth Guide](docs/TOKEN_BASED_AUTH.md)

### 🤖 Auto-detection rules
1) If `GLEAN_API_TOKEN` is set → token-based auth
2) Else if `GLEAN_COOKIES` is set → cookie-based auth
3) If both are set → token preferred
4) If neither is set → error with guidance

## Environment Variables

Required for server/library:
- `GLEAN_BASE_URL` (e.g. https://your-company-be.glean.com) or `GLEAN_INSTANCE`
- One of: `GLEAN_API_TOKEN` (preferred) or `GLEAN_COOKIES`

Optional (server behavior):
- `GLEAN_DEFAULT_PAGE_SIZE` (default: 14)
- `GLEAN_DEFAULT_SNIPPET_SIZE` (default: 215)
- `GLEAN_TOOL_DESCRIPTION` (tool description text)
- `GLEAN_AUTO_OPEN_BROWSER` (default: true)

## Development
```bash
git clone https://github.com/alankyshum/glean-mcp-server.git
cd glean-mcp-server
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Versioning & Publishing
- Semantic versioning; breaking changes bump MAJOR
- Tag `vX.Y.Z` after updating version strings; CI publishes to PyPI/GHCR if versions match

## License
MIT
