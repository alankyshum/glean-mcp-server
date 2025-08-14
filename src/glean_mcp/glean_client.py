"""Wrapper module exposing GleanClient within the glean_mcp package namespace.

The implementation lives at the top-level module ``glean_client`` so we just
re-export the public classes here to preserve imports like
``from glean_mcp.glean_client import GleanClient`` used by tests and callers.
"""
from __future__ import annotations

import importlib

try:  # pragma: no cover - simple import guard
    _impl = importlib.import_module("glean_client")
except ModuleNotFoundError as e:  # pragma: no cover
    raise ImportError("glean_client implementation module not found") from e

GleanClient = getattr(_impl, "GleanClient")
CookieExpiredError = getattr(_impl, "CookieExpiredError")

__all__ = ["GleanClient", "CookieExpiredError"]
