"""Glean MCP Python package exports.

Public API:
- Cookie-based client: GleanClient, CookieExpiredError
- Token-based client: TokenBasedGleanClient, TokenExpiredError
- Server helpers: create_glean_client (auto-detects auth)

Typing: package includes PEP 561 marker (py.typed)
"""

from .cookie_client import GleanClient, CookieExpiredError
from .token_client import TokenBasedGleanClient, TokenExpiredError
from .server import create_glean_client

# Keep version in sync with pyproject.toml; CI verifies this on tag release
__version__ = "3.1.0"

__all__ = [
    "GleanClient",
    "CookieExpiredError",
    "TokenBasedGleanClient",
    "TokenExpiredError",
    "create_glean_client",
    "__version__",
]
