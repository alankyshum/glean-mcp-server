"""
Glean API client for making search requests.
"""

import httpx
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import os


class CookieExpiredError(Exception):
    """Raised when cookies are expired and need renewal."""

    pass


class GleanClient:
    """Client for interacting with Glean API."""

    def __init__(
        self,
        base_url: str,
        cookies: str,
        cookie_renewal_callback: Optional[Callable[[], str]] = None,
    ):
        """
        Initialize the Glean client.

        Args:
            base_url: Base URL for Glean API (e.g., https://your-company-be.glean.com)
            cookies: Cookie string for authentication
            cookie_renewal_callback: Optional callback function to prompt for new cookies
        """
        # Ensure HTTPS is used for secure communication
        if not base_url.startswith("https://"):
            raise ValueError("Base URL must use HTTPS for secure communication")

        self.base_url = base_url.rstrip("/")
        self.cookies = cookies
        self.cookie_renewal_callback = cookie_renewal_callback
        self._cookies_validated = False
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/json",
                "origin": "https://app.glean.com",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://app.glean.com/",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            },
        )

    async def _validate_cookies(self) -> bool:
        """
        Validate current cookies by making a test request.

        Returns:
            True if cookies are valid, False otherwise
        """
        try:
            # Make a search request mirroring scripts/check-cookies.py to validate auth
            url = f"{self.base_url}/api/v1/search"

            # Params aligned with checker (allow override via env)
            client_version = os.getenv(
                "GLEAN_CLIENT_VERSION", "fe-release-2025-08-07-25f2142"
            )
            params = {
                "clientVersion": client_version,
                "locale": "en",
            }

            # Dynamic timestamp/session like checker
            now_iso = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

            def _rand_token(n: int = 16) -> str:
                import random
                import string

                return "".join(
                    random.choices(string.ascii_letters + string.digits, k=n)
                )

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
                    "clientVersion": client_version,
                    "initiator": "PAGE_LOAD",
                    "isDebug": False,
                    "modality": "FULLPAGE",
                },
                "timeoutMillis": 10000,
                "timestamp": now_iso,
            }

            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/json",
                "cookie": self.cookies,
                "origin": "https://app.glean.com",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://app.glean.com/",
                "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            }

            response = await self.client.post(
                url,
                json=payload,
                headers=headers,
                params=params,
                timeout=10.0,
            )

            # Only treat explicit auth errors as invalid; tolerate other codes (payload drift)
            if response.status_code in (401, 403):
                return False
            return True
        except httpx.TimeoutException:
            # Network flake shouldn't mark cookies invalid
            return True
        except Exception:
            # Be permissive to avoid false negatives; read_documents will surface real auth failures
            return True

    async def _handle_cookie_expiration(self):
        """
        Handle cookie expiration by attempting renewal if callback is available.
        """
        if self.cookie_renewal_callback:
            try:
                new_cookies = self.cookie_renewal_callback()
                if new_cookies and new_cookies.strip():
                    self.cookies = new_cookies.strip()
                    self._cookies_validated = False
                    # Test the new cookies
                    if await self._validate_cookies():
                        self._cookies_validated = True
                        return
            except Exception:
                pass

        # If renewal failed or no callback available, raise error
        raise CookieExpiredError("Cookies have expired and need manual renewal")

    async def _ensure_authenticated(self):
        """
        Ensure the client is authenticated, attempting renewal if needed.
        """
        if not self._cookies_validated:
            if await self._validate_cookies():
                self._cookies_validated = True
            else:
                await self._handle_cookie_expiration()

    async def search(
        self,
        query: str,
        page_size: int = 14,
        max_snippet_size: int = 215,
        timeout_millis: int = 10000,
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
        # Ensure we're authenticated before making the request
        await self._ensure_authenticated()

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
                    "SPELLCHECK_METADATA",
                ],
                "timezoneOffset": 420,
            },
            "sc": "",
            "sessionInfo": {
                "lastSeen": datetime.utcnow().isoformat() + "Z",
                "sessionTrackingToken": "mcp_server_session",
                "tabId": "mcp_server_tab",
                "clickedInJsSession": True,
                "firstEngageTsSec": int(datetime.utcnow().timestamp()),
            },
            "sourceInfo": {
                "clientVersion": "mcp-server-1.6.0",
                "initiator": "USER",
                "isDebug": False,
                "modality": "FULLPAGE",
            },
            "timeoutMillis": timeout_millis,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        # Add query parameters
        params = {"clientVersion": "mcp-server-1.6.0", "locale": "en"}

        response = await self.client.post(
            url, json=payload, params=params, headers={"Cookie": self.cookies}
        )

        # Handle potential authentication issues
        if response.status_code in [401, 403]:
            await self._handle_cookie_expiration()
            # Retry the request with potentially renewed cookies
            response = await self.client.post(
                url, json=payload, params=params, headers={"Cookie": self.cookies}
            )

        response.raise_for_status()
        return response.json()

    async def chat(
        self, message: str, conversation_id: str = "", timeout_millis: int = 30000
    ) -> str:
        """
        Perform a chat query against Glean's chat API.

        Args:
            message: User message/question
            conversation_id: Optional conversation id for continuity
            timeout_millis: Request timeout in milliseconds

        Returns:
            Complete chat response as a string
        """
        # Ensure we're authenticated before making the request
        await self._ensure_authenticated()

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
                    "paper": {"version": 1, "canCreate": False, "canEdit": False},
                },
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
                                "version": 1,
                            },
                        },
                    },
                    "author": "USER",
                    "fragments": [{"text": message}],
                    "messageType": "CONTENT",
                    "uploadedFileIds": [],
                }
            ],
            "saveChat": True,
            "sourceInfo": {
                "initiator": "USER",
                "platform": "WEB",
                "hasCopyPaste": False,
                "isDebug": False,
            },
            "stream": False,
            "sc": "",
            "sessionInfo": {
                "lastSeen": datetime.utcnow().isoformat() + "Z",
                "sessionTrackingToken": "mcp_server_session",
                "tabId": "mcp_server_tab",
                "clickedInJsSession": True,
                "firstEngageTsSec": int(datetime.utcnow().timestamp()),
                "lastQuery": message,
            },
        }

        # If a conversation id is provided, include it in the payload for continuity
        if conversation_id:
            payload["conversationId"] = conversation_id

        # Add query parameters
        params = {
            "timezoneOffset": 420,
            "clientVersion": "mcp-server-1.6.0",
            "locale": "en",
        }

        # Use text/plain content type for chat API
        headers = {"Cookie": self.cookies, "content-type": "text/plain"}

        response = await self.client.post(
            url,
            json=payload,
            params=params,
            headers=headers,
            timeout=timeout_millis / 1000.0,
        )

        # Handle potential authentication issues
        if response.status_code in [401, 403]:
            await self._handle_cookie_expiration()
            # Retry the request with potentially renewed cookies
            headers["Cookie"] = self.cookies
            response = await self.client.post(
                url,
                json=payload,
                params=params,
                headers=headers,
                timeout=timeout_millis / 1000.0,
            )

        response.raise_for_status()

        # Parse the non-streaming response
        data = response.json()
        return self._parse_chat_response(data)

    def _parse_chat_response(self, data: dict) -> str:
        """
        Parse the chat response and extract content from search steps and final response.

        Args:
            data: JSON response from chat API

        Returns:
            Complete chat response as a string with citations
        """
        complete_text = ""
        citations = []
        search_context = ""

        # Process messages to extract both search context and response
        if "messages" in data and data["messages"]:
            for message in data["messages"]:
                if message.get("author") == "GLEAN_AI":
                    step_id = message.get("stepId")

                    # Extract search/documentation steps (various step IDs possible)
                    if step_id and (
                        "search" in step_id.lower()
                        or "documentation" in step_id.lower()
                        or "runbook" in step_id.lower()
                        or "context" in step_id.lower()
                    ):
                        if "fragments" in message:
                            search_text = ""
                            for fragment in message["fragments"]:
                                if "text" in fragment:
                                    search_text += fragment["text"]
                            if search_text.strip():
                                if search_context:
                                    search_context += "\n\n" + search_text.strip()
                                else:
                                    search_context = search_text.strip()

                    # Extract the main response (step IDs containing "respond" or "synthesize")
                    elif step_id and (
                        "respond" in step_id.lower() or "synthesize" in step_id.lower()
                    ):
                        # Extract text fragments and citations
                        if "fragments" in message:
                            for fragment in message["fragments"]:
                                if "text" in fragment:
                                    complete_text += fragment["text"]
                                elif "citation" in fragment:
                                    citations.append(fragment["citation"])

        # Combine search context and response
        result = ""
        if search_context:
            result += search_context + "\n\n"

        result += complete_text

        # Add citations if available
        if citations:
            result += "\n\n**Sources:**\n"
            seen_urls = set()
            citation_num = 1
            for citation in citations:
                if "sourceDocument" in citation:
                    doc = citation["sourceDocument"]
                    title = doc.get("title", "Unknown")
                    url = doc.get("url", "")
                    if url and url not in seen_urls:
                        result += f"{citation_num}. [{title}]({url})\n"
                        seen_urls.add(url)
                        citation_num += 1

        return result.strip()

    async def read_documents(
        self, document_specs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Read documents from Glean by ID or URL.

        Args:
            document_specs: List of document specifications, each containing either 'id' or 'url'

        Returns:
            Dictionary containing the documents data
        """
        # Ensure we're authenticated before making the request
        await self._ensure_authenticated()

        # Use the correct endpoint format from the curl command
        url = f"{self.base_url}/api/v1/getdocuments"

        # Add query parameters like in the curl command
        params = {"clientVersion": "fe-release-2025-07-29-7e37358", "locale": "en"}

        payload = {
            "documentSpecs": document_specs,
            "includeFields": ["DOCUMENT_CONTENT", "LAST_VIEWED_AT", "VISITORS_COUNT"],
        }

        # Use headers that match the curl command exactly
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "cookie": self.cookies,  # Use lowercase 'cookie' header
            "origin": "https://app.glean.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://app.glean.com/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        try:
            response = await self.client.post(
                url, json=payload, headers=headers, params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise CookieExpiredError(
                    "Authentication failed - cookies may have expired"
                )
            else:
                raise Exception(
                    f"HTTP error {e.response.status_code}: {e.response.text}"
                )
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
