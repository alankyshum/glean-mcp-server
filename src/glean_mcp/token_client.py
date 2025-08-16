"""
Token-based Glean Client Addon.

This module provides a polymorphic addon for the GleanClient that supports
token-based authentication using Glean API tokens (Bearer authentication).

The addon extends the base GleanClient to use different API endpoints and
authentication methods for token-based access:

Token-based endpoints (base is https://{instance}-be.glean.com):
- Search: POST {base}/rest/api/v1/search
- Chat: POST {base}/rest/api/v1/chat
- Read documents: POST {base}/rest/api/v1/getdocuments

Cookie-based endpoints (base is https://{instance}-be.glean.com):
- Search: POST {base}/api/v1/search
- Chat: POST {base}/api/v1/chat
- Read documents: POST {base}/api/v1/getdocuments

Environment variables:
- GLEAN_API_TOKEN: Bearer token for authentication
- GLEAN_BASE_URL: Base URL (optional, derived from instance if not provided)
- GLEAN_INSTANCE: Instance name (default: "linkedin")
"""

from typing import Any, Dict, List, Optional, Callable
import json
import os
import asyncio

import httpx

from .cookie_client import GleanClient


class TokenExpiredError(Exception):
    """Raised when API token has expired or is invalid."""

    pass


class TokenBasedGleanClient(GleanClient):
    """
    Token-based Glean client that extends the base GleanClient.

    This client uses Bearer token authentication and different API endpoints
    compared to the cookie-based client.
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        token_renewal_callback: Optional[Callable[[], str]] = None,
    ):
        """
        Initialize the token-based Glean client.

        Args:
            base_url: Base URL for Glean API (e.g., https://your-company-be.glean.com)
            api_token: Bearer token for authentication
            token_renewal_callback: Optional callback function to prompt for new token
        """
        # Initialize the parent class with dummy cookies since we'll override auth
        super().__init__(base_url, "", token_renewal_callback)
        self.api_token = api_token
        self.token_renewal_callback = token_renewal_callback
        self._token_validated = False

    async def _validate_token(self) -> bool:
        """
        Validate the current API token by making a test request.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Make a simple search request to validate the token
            url = f"{self.base_url}/rest/api/v1/search"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_token}",
            }
            payload = {"query": "test", "pageSize": 1}

            response = await self.client.post(url, json=payload, headers=headers)
            return response.status_code not in [401, 403]
        except Exception:
            return False

    async def _handle_token_expiration(self):
        """
        Handle token expiration by attempting renewal or raising an error.
        """
        if self.token_renewal_callback:
            try:
                new_token = self.token_renewal_callback()
                if new_token:
                    self.api_token = new_token
                    self._token_validated = False
                    return
            except Exception:
                pass

        # If no callback or renewal failed, raise an error
        raise TokenExpiredError(
            "API token has expired. Please obtain a new token from your Glean instance "
            "and set the GLEAN_API_TOKEN environment variable."
        )

    async def _ensure_authenticated(self):
        """
        Ensure the client is authenticated, attempting renewal if needed.
        """
        if not self._token_validated:
            if await self._validate_token():
                self._token_validated = True
            else:
                await self._handle_token_expiration()

    async def search(
        self,
        query: str,
        page_size: int = 14,
        max_snippet_size: int = 215,
        timeout_millis: int = 10000,
    ) -> Dict[str, Any]:
        """
        Perform a search query against Glean API using token authentication.

        Args:
            query: Search query string
            page_size: Number of results per page
            max_snippet_size: Maximum size of result snippets
            timeout_millis: Request timeout in milliseconds

        Returns:
            Dictionary containing search results
        """
        # Ensure we're authenticated before making the request
        await self._ensure_authenticated()

        # Use token-based endpoint
        url = f"{self.base_url}/rest/api/v1/search"

        # Build simplified payload for token-based API
        payload = {"query": query, "pageSize": page_size}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        response = await self.client.post(
            url, json=payload, headers=headers, timeout=timeout_millis / 1000.0
        )

        # Handle potential authentication issues
        if response.status_code in [401, 403]:
            await self._handle_token_expiration()
            # Retry the request with potentially renewed token
            headers["Authorization"] = f"Bearer {self.api_token}"
            response = await self.client.post(
                url, json=payload, headers=headers, timeout=timeout_millis / 1000.0
            )

        response.raise_for_status()
        return response.json()

    async def chat(
        self, message: str, conversation_id: str = "", timeout_millis: int = 30000
    ) -> str:
        """
        Have a conversational interaction with Glean using token authentication.

        Args:
            message: User message/question
            conversation_id: Optional conversation id for continuity
            timeout_millis: Request timeout in milliseconds

        Returns:
            Complete chat response as a string with citations
        """
        # Ensure we're authenticated before making the request
        await self._ensure_authenticated()

        # Use token-based endpoint
        url = f"{self.base_url}/rest/api/v1/chat"

        # Build simplified payload for token-based API
        payload: Dict[str, Any] = {
            "messages": [
                {
                    "author": "USER",
                    "messageType": "CONTENT",
                    "fragments": [{"text": message}],
                }
            ]
        }

        if conversation_id:
            payload["conversationId"] = conversation_id

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        response = await self.client.post(
            url, json=payload, headers=headers, timeout=timeout_millis / 1000.0
        )

        # Handle potential authentication issues
        if response.status_code in [401, 403]:
            await self._handle_token_expiration()
            # Retry the request with potentially renewed token
            headers["Authorization"] = f"Bearer {self.api_token}"
            response = await self.client.post(
                url, json=payload, headers=headers, timeout=timeout_millis / 1000.0
            )

        response.raise_for_status()

        # Parse the response
        data = response.json()
        return self._parse_chat_response(data)

    def _normalize_url(self, u: str) -> str:
        """Strip fragments (#...) and query (?...) for stable document identity."""
        try:
            # Remove fragment (#...)
            u = u.split("#", 1)[0]
            # Remove query (?...)
            u = u.split("?", 1)[0]
            return u
        except Exception:
            return u

    async def read_documents(
        self, document_specs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Read documents from Glean by ID or URL using token authentication.

        Args:
            document_specs: List of document specifications, each containing either 'id' or 'url'

        Returns:
            Dictionary containing the documents data
        """
        # Ensure we're authenticated before making the request
        await self._ensure_authenticated()

        # Use token-based endpoint
        url = f"{self.base_url}/rest/api/v1/getdocuments"

        # Build API payload
        docs_payload: List[Dict[str, str]] = []
        for spec in document_specs:
            entry: Dict[str, str] = {}
            if spec.get("id"):
                entry["id"] = spec["id"]
            if spec.get("url"):
                entry["url"] = self._normalize_url(spec["url"])
            if entry:
                docs_payload.append(entry)

        payload = {
            "documentSpecs": docs_payload,
            "includeFields": ["DOCUMENT_CONTENT", "LAST_VIEWED_AT", "VISITORS_COUNT"],
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)

            # Handle potential authentication issues
            if response.status_code in [401, 403]:
                await self._handle_token_expiration()
                # Retry the request with potentially renewed token
                headers["Authorization"] = f"Bearer {self.api_token}"
                response = await self.client.post(url, json=payload, headers=headers)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise TokenExpiredError(
                    "Authentication failed - token may have expired"
                )
            else:
                raise Exception(
                    f"HTTP error {e.response.status_code}: {e.response.text}"
                )
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")


# ---------------- Factory Functions ---------------- #


def create_token_based_client(
    base_url: Optional[str] = None,
    api_token: Optional[str] = None,
    instance: Optional[str] = None,
    token_renewal_callback: Optional[Callable[[], str]] = None,
) -> TokenBasedGleanClient:
    """
    Create a token-based Glean client from environment variables or parameters.

    Args:
        base_url: Base URL for Glean API (optional, derived from instance if not provided)
        api_token: Bearer token for authentication (optional, read from GLEAN_API_TOKEN if not provided)
        instance: Instance name (optional, defaults to "linkedin")
        token_renewal_callback: Optional callback function to prompt for new token

    Returns:
        TokenBasedGleanClient instance

    Raises:
        ValueError: If no API token is provided and GLEAN_API_TOKEN is not set
    """
    # Get configuration from environment or parameters
    token = api_token or os.environ.get("GLEAN_API_TOKEN")
    if not token:
        raise ValueError(
            "API token not configured. Set GLEAN_API_TOKEN environment variable "
            "or provide api_token parameter."
        )

    # Determine base URL
    if not base_url:
        instance_name = instance or os.environ.get("GLEAN_INSTANCE", "linkedin")
        base_url = (
            os.environ.get("GLEAN_BASE_URL") or f"https://{instance_name}-be.glean.com"
        )

    # Ensure HTTPS is used for secure communication
    if not base_url.startswith("https://"):
        raise ValueError("Base URL must use HTTPS for secure communication")

    return TokenBasedGleanClient(base_url, token, token_renewal_callback)


def get_client_for_auth_type(auth_type: str = "auto", **kwargs) -> GleanClient:
    """
    Get a Glean client based on the authentication type.

    Args:
        auth_type: Authentication type ("token", "cookie", or "auto")
        **kwargs: Additional arguments passed to the client constructor

    Returns:
        GleanClient instance (either TokenBasedGleanClient or regular GleanClient)

    Raises:
        ValueError: If authentication configuration is invalid
    """
    if auth_type == "token":
        return create_token_based_client(**kwargs)
    elif auth_type == "cookie":
        # Use the regular cookie-based client
        base_url = kwargs.get("base_url") or os.environ.get("GLEAN_BASE_URL")
        cookies = kwargs.get("cookies") or os.environ.get("GLEAN_COOKIES")
        if not base_url or not cookies:
            raise ValueError(
                "Cookie authentication requires GLEAN_BASE_URL and GLEAN_COOKIES "
                "environment variables or base_url and cookies parameters."
            )
        return GleanClient(base_url, cookies, kwargs.get("cookie_renewal_callback"))
    elif auth_type == "auto":
        # Auto-detect based on available environment variables
        if os.environ.get("GLEAN_API_TOKEN"):
            return create_token_based_client(**kwargs)
        elif os.environ.get("GLEAN_COOKIES"):
            return get_client_for_auth_type("cookie", **kwargs)
        else:
            raise ValueError(
                "No authentication configured. Set either GLEAN_API_TOKEN "
                "or GLEAN_COOKIES environment variable."
            )
    else:
        raise ValueError(
            f"Invalid auth_type: {auth_type}. Must be 'token', 'cookie', or 'auto'."
        )


# ---------------- Synchronous API Functions ---------------- #


def glean_search_with_token(query: str, page_size: int = 10) -> str:
    """
    Synchronous search function using token-based authentication.

    Args:
        query: Search query string
        page_size: Number of results (default 10)

    Returns:
        JSON string of results or error info
    """

    async def _search():
        client = create_token_based_client()
        try:
            result = await client.search(query, page_size)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": True, "exception": str(e)}, indent=2)
        finally:
            await client.close()

    return asyncio.run(_search())


def glean_chat_with_token(message: str, conversation_id: str = "") -> str:
    """
    Synchronous chat function using token-based authentication.

    Args:
        message: User message/question
        conversation_id: Optional conversation id for continuity

    Returns:
        JSON string of response or error info
    """

    async def _chat():
        client = create_token_based_client()
        try:
            result = await client.chat(message, conversation_id)
            return result
        except Exception as e:
            return json.dumps({"error": True, "exception": str(e)}, indent=2)
        finally:
            await client.close()

    return asyncio.run(_chat())


def glean_read_documents_with_token(document_specs: List[Dict[str, str]]) -> str:
    """
    Synchronous document reading function using token-based authentication.

    Args:
        document_specs: list of {"id": str} or {"url": str}

    Returns:
        JSON string of results or error info
    """

    async def _read_docs():
        client = create_token_based_client()
        try:
            result = await client.read_documents(document_specs)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": True, "exception": str(e)}, indent=2)
        finally:
            await client.close()

    return asyncio.run(_read_docs())


# ---------------- Module Exports ---------------- #

__all__ = [
    "TokenBasedGleanClient",
    "TokenExpiredError",
    "create_token_based_client",
    "get_client_for_auth_type",
    "glean_search_with_token",
    "glean_chat_with_token",
    "glean_read_documents_with_token",
]
