"""Run a single Glean search inside the docker image.

Usage (host):
  docker run --rm \
    -e GLEAN_BASE_URL="$GLEAN_BASE_URL" \
    -e GLEAN_COOKIES="$GLEAN_COOKIES" \
    glean-mcp-server:latest \
    python scripts/docker_happy_path_search.py lighthouse-web

Outputs compact JSON: {"query":..., "totalResults": int, "sampleTitles": [...]}.
Exits non‑zero on failure. Does NOT echo full cookies.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict

from glean_mcp.glean_client import GleanClient, CookieExpiredError


async def run(query: str) -> Dict[str, Any]:
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES")
    if not base_url or not cookies:
        raise SystemExit("Missing GLEAN_BASE_URL or GLEAN_COOKIES env vars")

    client = GleanClient(base_url, cookies)
    try:
        data = await client.search(query=query, page_size=10)
    finally:
        await client.close()

    # Try to derive result list
    results = []
    # Glean search response structures can vary; attempt common paths
    if isinstance(data, dict):
        # Path 1: data['results']['items'] style
        if 'results' in data and isinstance(data['results'], dict):
            items = data['results'].get('items') or data['results'].get('results')
            if isinstance(items, list):
                results = items
        # Path 2: top-level 'searchResults'
        if not results and 'searchResults' in data and isinstance(data['searchResults'], list):
            results = data['searchResults']

    titles = []
    for r in results[:5]:  # sample first 5
        if isinstance(r, dict):
            title = r.get('title') or r.get('name') or r.get('documentTitle')
            if title:
                titles.append(str(title)[:120])

    return {
        "query": query,
        "totalResults": len(results),
        "sampleTitles": titles,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/docker_happy_path_search.py <query>", file=sys.stderr)
        raise SystemExit(2)
    query = " ".join(sys.argv[1:])
    try:
        out = asyncio.run(run(query))
        print(json.dumps(out, indent=2))
    except CookieExpiredError as ce:  # specific auth issue
        print(json.dumps({"error": "cookie_expired", "message": str(ce)}), file=sys.stderr)
        raise SystemExit(10)
    except Exception as e:  # generic failure
        print(json.dumps({"error": "search_failed", "message": str(e)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
