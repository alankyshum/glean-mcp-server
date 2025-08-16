"""
Lightweight test support utilities for external projects.

This module exposes cookie and token health checks that mirror the behavior of the
CLI scripts in scripts/check-cookies.py and scripts/check-token.py, but in a
programmatic, dependency-friendly form (no prints by default, returns rich info).

Usage examples:

    from glean_mcp.test_support import check_token, check_cookies

    ok, info = await check_token()
    assert ok, info

    ok, info = await check_cookies()
    assert ok, info

Both functions accept explicit parameters; when omitted, they fall back to
environment variables and a .env file (loaded via python-dotenv):
    - GLEAN_BASE_URL
    - GLEAN_API_TOKEN (for token check)
    - GLEAN_COOKIES (for cookie check)
    - GLEAN_CLIENT_VERSION (optional; defaults provided)
    - GLEAN_AUTH_TYPE (optional, token check)
    - GLEAN_ACT_AS (optional, token check)

They return a tuple: (ok: bool, info: dict). The info dict includes keys like
"status_code", "url", and either "details" or "error".
"""

from __future__ import annotations

import asyncio
import os
import random
import string
from datetime import datetime
from typing import Dict, Optional, Tuple

import httpx
from dotenv import load_dotenv


def _load_env_once() -> None:
    """Load .env if present (idempotent)."""
    # load_dotenv is safe to call multiple times; it won't overwrite set variables by default
    load_dotenv(override=False)


def _sanitize_quotes(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = value.strip()
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        return s[1:-1]
    return s


def _header_overrides_from_env() -> Dict[str, str]:
    hdrs: Dict[str, str] = {}
    auth_type = os.getenv("GLEAN_AUTH_TYPE")
    act_as = os.getenv("GLEAN_ACT_AS")
    if auth_type:
        hdrs["X-Glean-Auth-Type"] = auth_type
    if act_as:
        hdrs["X-Glean-ActAs"] = act_as
    return hdrs


async def check_token(
    *,
    base_url: Optional[str] = None,
    api_token: Optional[str] = None,
    auth_type: Optional[str] = None,
    act_as: Optional[str] = None,
    timeout: float = 10.0,
) -> Tuple[bool, Dict[str, object]]:
    """
    Validate a token-based Glean API configuration by issuing a minimal search request.

    Parameters can be provided explicitly or via environment variables. A .env file is
    automatically loaded (if present).

    Returns: (ok, info) where info contains diagnostic details.
    """
    _load_env_once()

    base = _sanitize_quotes(base_url or os.getenv("GLEAN_BASE_URL"))
    token = _sanitize_quotes(api_token or os.getenv("GLEAN_API_TOKEN"))
    if not base:
        return False, {"error": "Missing GLEAN_BASE_URL", "status_code": None}
    if not token:
        return False, {"error": "Missing GLEAN_API_TOKEN", "status_code": None}

    # Determine endpoint: allow base_url with or without '/rest/api/v1'
    base_norm = base.rstrip("/")
    if base_norm.endswith("/rest/api/v1"):
        url = f"{base_norm}/search"
    else:
        url = f"{base_norm}/rest/api/v1/search"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "glean-mcp-test-support/1.0",
    }

    # Allow explicit overrides or env-based ones
    if auth_type:
        headers["X-Glean-Auth-Type"] = auth_type
    if act_as:
        headers["X-Glean-ActAs"] = act_as
    headers.update(_header_overrides_from_env())

    payload = {"query": "test", "pageSize": 1}

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException:
            return False, {"error": "timeout", "url": url, "status_code": None}
        except Exception as e:  # pragma: no cover - transport errors
            return False, {"error": str(e), "url": url, "status_code": None}

    info: Dict[str, object] = {"url": url, "status_code": r.status_code}
    if r.status_code == 200:
        try:
            data = r.json()
            if isinstance(data, dict) and "results" in data:
                info["details"] = "ok"
                return True, info
            info["details"] = "200 but response shape unexpected"
            return True, info
        except Exception as e:
            info["details"] = f"200 but JSON parse failed: {e}"
            return True, info
    elif r.status_code in (401, 403):
        info["error"] = "auth"
        info["body"] = r.text[:500]
        return False, info
    else:
        info["error"] = "non-200"
        info["body"] = r.text[:500]
        return False, info


def _rand_token(n: int = 16) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


async def check_cookies(
    *,
    base_url: Optional[str] = None,
    cookies: Optional[str] = None,
    client_version: Optional[str] = None,
    timeout: float = 10.0,
) -> Tuple[bool, Dict[str, object]]:
    """
    Validate a cookie-based Glean configuration using the web endpoint.

    Parameters can be provided explicitly or read from env (GLEAN_BASE_URL, GLEAN_COOKIES,
    optional GLEAN_CLIENT_VERSION). A .env file is automatically loaded if present.

    Returns: (ok, info) where info contains diagnostic details.
    """
    _load_env_once()

    base = _sanitize_quotes(base_url or os.getenv("GLEAN_BASE_URL"))
    raw_cookies = _sanitize_quotes(cookies or os.getenv("GLEAN_COOKIES"))
    if not base:
        return False, {"error": "Missing GLEAN_BASE_URL", "status_code": None}
    if not raw_cookies:
        return False, {"error": "Missing GLEAN_COOKIES", "status_code": None}

    # Endpoint used by the web client
    url = f"{base.rstrip('/')}/api/v1/search"

    # Keep payload similar-but-not-brittle versus the browser call
    now_iso = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    cv = client_version or os.getenv("GLEAN_CLIENT_VERSION", "mcp-test-support")
    params = {"clientVersion": cv, "locale": "en"}
    payload = {
        "inputDetails": {"hasCopyPaste": False},
        "maxSnippetSize": 215,
        "pageSize": 1,
        "query": "test",
        "requestOptions": {
            "debugOptions": {},
            "disableQueryAutocorrect": False,
            "facetBucketSize": 30,
            "facetFilters": [],
            "fetchAllDatasourceCounts": True,
            "queryOverridesFacetFilters": True,
            "responseHints": [
                "RESULTS",
                "FACET_RESULTS",
                "ALL_RESULT_COUNTS",
                "SPELLCHECK_METADATA",
            ],
            "timezoneOffset": 420,
        },
        "resultTabIds": ["all"],
        "sc": "",
        "sessionInfo": {
            "lastSeen": now_iso,
            "sessionTrackingToken": _rand_token(16),
            "tabId": _rand_token(16),
        },
        "sourceInfo": {
            "clientVersion": cv,
            "initiator": "PAGE_LOAD",
            "isDebug": False,
            "modality": "FULLPAGE",
        },
        "timeoutMillis": int(timeout * 1000),
        "timestamp": now_iso,
    }

    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "cookie": raw_cookies,
        "origin": "https://app.glean.com",
        "referer": "https://app.glean.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(url, params=params, json=payload, headers=headers)
        except httpx.TimeoutException:
            return False, {"error": "timeout", "url": url, "status_code": None}
        except Exception as e:  # pragma: no cover - transport errors
            return False, {"error": str(e), "url": url, "status_code": None}

    info: Dict[str, object] = {"url": url, "status_code": r.status_code}
    if r.status_code == 200:
        try:
            data = r.json()
            if isinstance(data, dict) and "results" in data:
                info["details"] = "ok"
                return True, info
            info["details"] = "200 but response shape unexpected"
            return True, info
        except Exception as e:
            info["details"] = f"200 but JSON parse failed: {e}"
            return True, info
    elif r.status_code in (401, 403):
        info["error"] = "auth"
        info["body"] = r.text[:500]
        return False, info
    else:
        info["error"] = "non-200"
        info["body"] = r.text[:500]
        return False, info


# Optional sync wrappers for convenience in synchronous tests


def check_token_sync(**kwargs) -> Tuple[bool, Dict[str, object]]:
    return asyncio.run(check_token(**kwargs))


def check_cookies_sync(**kwargs) -> Tuple[bool, Dict[str, object]]:
    return asyncio.run(check_cookies(**kwargs))


__all__ = [
    "check_token",
    "check_cookies",
    "check_token_sync",
    "check_cookies_sync",
]
