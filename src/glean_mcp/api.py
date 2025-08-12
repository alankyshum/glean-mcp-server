"""Generic synchronous helper API (captain‑agnostic).

These helpers wrap the async :class:`glean_mcp.glean_client.GleanClient` to
provide simple, blocking functions that return JSON *strings* so callers do not
need to manage an event loop. Returning JSON text keeps the surface area small
and avoids committing to Python object shapes across versions.

Environment variables required:
 - ``GLEAN_BASE_URL``  (e.g. https://your-company-be.glean.com)
 - ``GLEAN_COOKIES``   (browser cookie string for authentication)

Future auth mechanisms (e.g., OAuth/token) can be added without changing the
public function signatures by extending ``_get_client`` logic.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

from .glean_client import GleanClient, CookieExpiredError

_CLIENT_SINGLETON: GleanClient | None = None


def _get_client() -> GleanClient:
    """Return a process‑wide singleton ``GleanClient``.

    The singleton keeps connection pooling efficient for repeated short‑lived
    CLI style invocations within the same process.
    """
    global _CLIENT_SINGLETON
    if _CLIENT_SINGLETON is not None:
        return _CLIENT_SINGLETON

    base_url = os.environ.get("GLEAN_BASE_URL")
    cookies = os.environ.get("GLEAN_COOKIES")
    if not base_url:
        raise RuntimeError("GLEAN_BASE_URL is required (e.g. https://company-be.glean.com)")
    if not cookies:
        raise RuntimeError("GLEAN_COOKIES is required for authentication")
    _CLIENT_SINGLETON = GleanClient(base_url=base_url, cookies=cookies)
    return _CLIENT_SINGLETON


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Nested event loop scenario (e.g., within Jupyter) – delegate safely.
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    return asyncio.run(coro)


def _error_json(message: str, status: int | None = None, **extra: Any) -> str:
    payload: Dict[str, Any] = {"error": {"message": message}}
    if status is not None:
        payload["error"]["status"] = status
    if extra:
        payload["error"].update(extra)
    return json.dumps(payload, indent=2)


def glean_search(query: str, page_size: int = 10) -> str:
    """Perform a search request.

    Returns a JSON string shaped as:
    {"results": [...], "metadata": {"searchedQuery": str}, "totalResults": int}
    """
    try:
        client = _get_client()
        raw = _run(client.search(query=query, page_size=page_size))
        return json.dumps(
            {
                "results": raw.get("results", []),
                "metadata": {"searchedQuery": query},
                "totalResults": raw.get("total_results") or len(raw.get("results", [])),
            },
            indent=2,
        )
    except CookieExpiredError as e:  # pragma: no cover - simple branch
        return _error_json(str(e), status=401)
    except Exception as e:  # pragma: no cover - defensive fallback
        return _error_json("search_failed", detail=str(e))


def glean_chat(message: str) -> str:
    """Send a chat style query returning a minimal message array JSON string."""
    try:
        client = _get_client()
        text = _run(client.chat(query=message))
        return json.dumps(
            {
                "messages": [
                    {
                        "author": "ASSISTANT",
                        "messageType": "CONTENT",
                        "fragments": [{"text": text}],
                        "citations": [],
                    }
                ]
            },
            indent=2,
        )
    except CookieExpiredError as e:  # pragma: no cover
        return _error_json(str(e), status=401)
    except Exception as e:  # pragma: no cover
        return _error_json("chat_failed", detail=str(e))


def glean_read_documents(specs: List[Dict[str, str]]) -> str:
    """Retrieve documents by specification list.

    Each spec should contain either an ``id`` or ``url`` field.
    Returns JSON string shaped as: {"documents": {...}}
    """
    try:
        client = _get_client()
        raw = _run(client.read_documents(document_specs=specs))
        return json.dumps({"documents": raw.get("documents", {})}, indent=2)
    except CookieExpiredError as e:  # pragma: no cover
        return _error_json(str(e), status=401)
    except Exception as e:  # pragma: no cover
        return _error_json("read_documents_failed", detail=str(e))


+__all__ = ["glean_search", "glean_chat", "glean_read_documents"]
