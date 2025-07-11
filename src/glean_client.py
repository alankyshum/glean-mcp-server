"""
Glean API client for making search requests.
"""
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os


class GleanClient:
    """Client for interacting with Glean API."""

    def __init__(self, base_url: str, cookies: str):
        """
        Initialize the Glean client.

        Args:
            base_url: Base URL for Glean API (e.g., https://your-company.glean.com)
            cookies: Cookie string for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.cookies = cookies
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
                'origin': 'https://app.glean.com',
                'pragma': 'no-cache',
                'priority': 'u=1, i',
                'referer': 'https://app.glean.com/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
        )

    async def search(
        self,
        query: str,
        page_size: int = 14,
        max_snippet_size: int = 215,
        timeout_millis: int = 10000
    ) -> Dict[str, Any]:
        """
        Perform a search query against Glean API.

        Args:
            query: Search query string
            page_size: Number of results per page
            max_snippet_size: Maximum size of result snippets
            timeout_millis: Request timeout in milliseconds

        Returns:
            Search results from Glean API
        """
        url = f"{self.base_url}/api/v1/search"

        # Build request payload based on the provided curl example
        payload = {
            "inputDetails": {"hasCopyPaste": False},
            "maxSnippetSize": max_snippet_size,
            "pageSize": page_size,
            "query": query,
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
                    "SPELLCHECK_METADATA"
                ],
                "timezoneOffset": 420
            },
            "sc": "",
            "sessionInfo": {
                "lastSeen": datetime.utcnow().isoformat() + "Z",
                "sessionTrackingToken": "mcp_server_session",
                "tabId": "mcp_server_tab",
                "clickedInJsSession": True,
                "firstEngageTsSec": int(datetime.utcnow().timestamp())
            },
            "sourceInfo": {
                "clientVersion": "mcp-server-1.3.0",
                "initiator": "USER",
                "isDebug": False,
                "modality": "FULLPAGE"
            },
            "timeoutMillis": timeout_millis,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Add query parameters
        params = {
            "clientVersion": "mcp-server-1.3.0",
            "locale": "en"
        }

        response = await self.client.post(
            url,
            json=payload,
            params=params,
            headers={"Cookie": self.cookies}
        )

        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
