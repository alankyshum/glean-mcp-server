"""Public Python package interface for the Glean MCP utilities.

This package intentionally exposes a *minimal*, implementation‑agnostic API so
it can be embedded in any tooling environment (editors, CLI helpers, automations)
without pulling in naming or behavior tied to a specific upstream project.

Synchronous convenience functions are provided in :mod:`glean_mcp.api`:
 - ``glean_search(query: str, page_size: int = 10) -> str``
 - ``glean_chat(message: str) -> str``
 - ``glean_read_documents(specs: list[dict]) -> str``

They return JSON strings for maximum portability (easy to log, pipe, or parse)
while internally using the async ``GleanClient`` for efficient IO.
"""

from .api import glean_search, glean_chat, glean_read_documents  # noqa: F401

# Keep version in sync with pyproject.toml. Avoid importing importlib.metadata at
# runtime for speed; update manually during release bumps.
__version__ = "0.1.2"

__all__ = [
	"glean_search",
	"glean_chat",
	"glean_read_documents",
	"__version__",
]
