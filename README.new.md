# Glean MCP Library & Utilities

Lightweight Python package providing:

- Async `GleanClient` for search, chat, document retrieval
- Synchronous helper functions returning JSON strings
- CLI (`glean-mcp`) for quick terminal usage

Links: [Releases](https://github.com/alankyshum/glean-mcp-server/releases) · [Filtering Details](FILTERING.md) · [Cookie Guide](docs/COOKIES.md) · [Publishing](PUBLISHING.md)

## Installation
```bash
pip install glean-mcp
# or with performance extra
pip install 'glean-mcp[perf]'
```

## Quick Start (Library)
```python
import os
from glean_mcp import glean_search
os.environ['GLEAN_BASE_URL'] = 'https://your-company-be.glean.com'
os.environ['GLEAN_COOKIES'] = '<cookie string>'
print(glean_search('onboarding docs'))
```

## Quick Start (CLI)
```bash
export GLEAN_BASE_URL=https://your-company-be.glean.com
export GLEAN_COOKIES='<cookie string>'

glean-mcp search "onboarding"
glean-mcp chat "How do I rotate credentials?"
glean-mcp read-docs id=12345 url=https://docs.google.com/document/d/... 
```

## Functions
| Function | Description |
|----------|-------------|
| glean_search(query, page_size=10) | Search documents (JSON string) |
| glean_chat(message) | Chat answer (JSON string) |
| glean_read_documents(specs) | Retrieve documents (JSON string) |

Underlying async usage: create `GleanClient(base_url, cookies)` and await its methods.

## Environment Variables
| Var | Required | Purpose |
|-----|----------|---------|
| GLEAN_BASE_URL | Yes | Backend instance URL |
| GLEAN_COOKIES  | Yes | Auth cookies (see docs/COOKIES.md) |

## Development
```bash
git clone https://github.com/alankyshum/glean-mcp-server.git
cd glean-mcp-server
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Versioning & Publishing
Tag `vX.Y.Z` after updating version strings; GitHub Action publishes if versions match. See PUBLISHING.md.

## License
MIT
