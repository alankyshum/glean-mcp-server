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
                "clientVersion": "mcp-server-1.4.0",
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

    async def chat(
        self,
        query: str,
        timeout_millis: int = 30000
    ) -> str:
        """
        Perform a chat query against Glean's chat API.

        Args:
            query: Chat query string
            timeout_millis: Request timeout in milliseconds

        Returns:
            Complete chat response as a string
        """
        url = f"{self.base_url}/api/v1/chat"

        # Build request payload based on the provided curl example
        payload = {
            "agentConfig": {
                "agent": "DEFAULT",
                "mode": "DEFAULT",
                "useDeepReasoning": False,
                "useDeepResearch": False,
                "clientCapabilities": {
                    "canRenderImages": True,
                    "paper": {
                        "version": 1,
                        "canCreate": False,
                        "canEdit": False
                    }
                }
            },
            "messages": [
                {
                    "agentConfig": {
                        "agent": "DEFAULT",
                        "mode": "DEFAULT",
                        "useDeepReasoning": False,
                        "useDeepResearch": False,
                        "clientCapabilities": {
                            "canRenderImages": True,
                            "paper": {
                                "canCreate": False,
                                "canEdit": False,
                                "version": 1
                            }
                        }
                    },
                    "author": "USER",
                    "fragments": [{"text": query}],
                    "messageType": "CONTENT",
                    "uploadedFileIds": []
                }
            ],
            "saveChat": True,
            "sourceInfo": {
                "initiator": "USER",
                "platform": "WEB",
                "hasCopyPaste": False,
                "isDebug": False
            },
            "stream": False,
            "sc": "",
            "sessionInfo": {
                "lastSeen": datetime.utcnow().isoformat() + "Z",
                "sessionTrackingToken": "mcp_server_session",
                "tabId": "mcp_server_tab",
                "clickedInJsSession": True,
                "firstEngageTsSec": int(datetime.utcnow().timestamp()),
                "lastQuery": query
            }
        }

        # Add query parameters
        params = {
            "timezoneOffset": 420,
            "clientVersion": "mcp-server-1.4.0",
            "locale": "en"
        }

        # Use text/plain content type for chat API
        headers = {
            "Cookie": self.cookies,
            "content-type": "text/plain"
        }

        response = await self.client.post(
            url,
            json=payload,
            params=params,
            headers=headers,
            timeout=timeout_millis / 1000.0
        )

        response.raise_for_status()

        # Parse the non-streaming response
        data = response.json()
        return self._parse_chat_response(data)

    def _parse_chat_response(self, data: dict) -> str:
        """
        Parse the chat response and extract only the useful content from RESPOND step.

        Args:
            data: JSON response from chat API

        Returns:
            Complete chat response as a string with citations
        """
        complete_text = ""
        citations = []

        # Find the RESPOND message
        if 'messages' in data and data['messages']:
            for message in data['messages']:
                if (message.get('author') == 'GLEAN_AI' and
                    message.get('stepId') == 'RESPOND'):

                    # Extract text fragments and citations
                    if 'fragments' in message:
                        for fragment in message['fragments']:
                            if 'text' in fragment:
                                complete_text += fragment['text']
                            elif 'citation' in fragment:
                                citations.append(fragment['citation'])
                    break

        # Add citations if available
        if citations:
            complete_text += "\n\n**Sources:**\n"
            seen_urls = set()
            citation_num = 1
            for citation in citations:
                if 'sourceDocument' in citation:
                    doc = citation['sourceDocument']
                    title = doc.get('title', 'Unknown')
                    url = doc.get('url', '')
                    if url and url not in seen_urls:
                        complete_text += f"{citation_num}. [{title}]({url})\n"
                        seen_urls.add(url)
                        citation_num += 1

        return complete_text.strip()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
