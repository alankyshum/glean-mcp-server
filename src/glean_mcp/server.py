"""
Glean MCP Server - A Model Context Protocol server for Glean search functionality.
"""

import asyncio
import os
import sys
import webbrowser
import json
import httpx

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl
from dotenv import load_dotenv

from .cookie_client import GleanClient, CookieExpiredError
from .token_client import TokenBasedGleanClient, TokenExpiredError
from .glean_filter import filter_glean_response

# Load environment variables
load_dotenv()

# Get configuration from environment variables
DEFAULT_PAGE_SIZE = int(os.getenv("GLEAN_DEFAULT_PAGE_SIZE", "14"))
DEFAULT_SNIPPET_SIZE = int(os.getenv("GLEAN_DEFAULT_SNIPPET_SIZE", "215"))
TOOL_DESCRIPTION = os.getenv(
    "GLEAN_TOOL_DESCRIPTION", "Search for internal company information"
)
AUTO_OPEN_BROWSER = os.getenv("GLEAN_AUTO_OPEN_BROWSER", "true").lower() == "true"

# Initialize the MCP server
server = Server("glean-mcp-server")

# Global client instance (can be either GleanClient or TokenBasedGleanClient)
glean_client = None


def prompt_for_new_cookies() -> str:
    """
    Prompt the user for new cookies when the current ones expire.

    Returns:
        New cookie string provided by the user
    """
    # For MCP, we'll return a special message that instructs the user
    # Since MCP doesn't support direct user input, we provide clear instructions
    raise CookieExpiredError(
        "Cookies have expired. Please update your MCP configuration with fresh cookies and restart."
    )


def generate_auth_error_message() -> str:
    """Generate a personalized authentication error message and optionally open browser."""
    base_url = os.getenv("GLEAN_BASE_URL", "your-glean-instance.com")

    # Clean up the URL to get the main domain
    clean_url = base_url
    if clean_url.endswith("/api/v1/search"):
        clean_url = clean_url.replace("/api/v1/search", "")

    # Extract company name from URL for personalization
    company_name = "your company"
    if "-be.glean.com" in clean_url:
        try:
            # Extract company name from URL like https://company-be.glean.com
            company_part = clean_url.replace("https://", "").replace("http://", "")
            if company_part.endswith("-be.glean.com"):
                company_name = company_part.replace("-be.glean.com", "")
        except Exception:
            pass

    # Try to open the browser automatically (if enabled)
    browser_opened = False
    if AUTO_OPEN_BROWSER:
        try:
            webbrowser.open(clean_url)
            browser_opened = True
        except Exception:
            pass

    browser_message = (
        "🌐 Opening your Glean page in browser..." if browser_opened else ""
    )

    return f"""🚨 Authentication Failed - Cookies Expired

{browser_message}

Your {company_name} Glean cookies have expired and need to be renewed.

✅ Quick Fix (60 seconds):
1. {"Browser opened automatically! Switch to it, or go to:" if browser_opened else "Go to:"} {clean_url}
2. Make sure you're logged in to {company_name} Glean
3. Press F12 → Network tab
4. Perform a search in Glean to trigger API requests
5. Find any search API request → Right-click → Copy as cURL
6. Extract the Cookie header value from the cURL command
7. Update your MCP configuration with the new cookies

🔧 Update Methods:

For Docker users:
- Update GLEAN_COOKIES in your MCP settings file
- Restart Cursor/VS Code

For local installation:
- Update GLEAN_COOKIES in your .env file
- Restart the MCP server

💡 Pro tips:
   • Extract cookies: python scripts/extract-cookies-from-curl.py --interactive
   • Update cookies: python scripts/update-cookies.py "paste_new_cookies_here"

Your Glean instance: {clean_url}"""


def prompt_for_new_token() -> str:
    """
    Prompt the user for a new API token when the current one expires.

    Returns:
        New API token from user input
    """
    # For MCP, we'll return a special message that instructs the user
    # Since MCP doesn't support direct user input, we provide clear instructions
    raise TokenExpiredError(
        "API token has expired. Please update your MCP configuration with a fresh token and restart."
    )


def create_glean_client():
    """
    Create a Glean client with auto-detection of authentication method.

    Returns:
        Either GleanClient (cookie-based) or TokenBasedGleanClient (token-based)
    """
    base_url = os.getenv("GLEAN_BASE_URL")
    api_token = os.getenv("GLEAN_API_TOKEN")
    cookies = os.getenv("GLEAN_COOKIES")
    instance = os.getenv("GLEAN_INSTANCE", "linkedin")

    # Derive base_url from instance if not provided
    if not base_url:
        if instance:
            base_url = f"https://{instance}-be.glean.com"
        else:
            raise ValueError(
                "Either GLEAN_BASE_URL or GLEAN_INSTANCE environment variable is required"
            )

    # Auto-detect authentication method (prefer token over cookies)
    if api_token:
        print("🔑 Using token-based authentication")
        return TokenBasedGleanClient(
            base_url=base_url,
            api_token=api_token,
            token_renewal_callback=prompt_for_new_token,
        )
    elif cookies:
        print("🍪 Using cookie-based authentication")
        return GleanClient(
            base_url=base_url,
            cookies=cookies,
            cookie_renewal_callback=prompt_for_new_cookies,
        )
    else:
        raise ValueError(
            "Authentication not configured. Set either GLEAN_API_TOKEN (preferred) "
            "or GLEAN_COOKIES environment variable."
        )


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=AnyUrl("glean://search"),
            name="Glean Search",
            description="Search functionality for Glean knowledge base",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("glean://research"),
            name="Glean Research",
            description="AI-powered research functionality for Glean knowledge base",
            mimeType="text/plain",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    if uri.scheme != "glean":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    if uri.path == "/search":
        return json.dumps(
            {
                "description": "Glean search resource",
                "usage": "Use the glean_search tool to perform searches",
                "available_tools": ["glean_search"],
            }
        )
    elif uri.path == "/research":
        return json.dumps(
            {
                "description": "Glean research resource",
                "usage": "Use the glean_research tool to get AI-powered answers from your knowledge base",
                "available_tools": ["glean_research"],
            }
        )
    else:
        raise ValueError(f"Unknown resource path: {uri.path}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="glean_search",
            description=TOOL_DESCRIPTION,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": f"Number of results to return (default: {DEFAULT_PAGE_SIZE}, configurable via GLEAN_DEFAULT_PAGE_SIZE)",
                        "default": DEFAULT_PAGE_SIZE,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "max_snippet_size": {
                        "type": "integer",
                        "description": f"Maximum size of result snippets (default: {DEFAULT_SNIPPET_SIZE}, configurable via GLEAN_DEFAULT_SNIPPET_SIZE)",
                        "default": DEFAULT_SNIPPET_SIZE,
                        "minimum": 50,
                        "maximum": 1000,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="glean_research",
            description="Research and get AI-powered answers from your company's knowledge base using Glean's chat AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The research question or topic to investigate",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="read_documents",
            description="Read documents from Glean by ID or URL to retrieve their full content",
            inputSchema={
                "type": "object",
                "properties": {
                    "documentSpecs": {
                        "type": "array",
                        "description": "List of document specifications to retrieve",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Glean Document ID",
                                },
                                "url": {
                                    "type": "string",
                                    "description": "Document URL",
                                },
                            },
                            "anyOf": [{"required": ["id"]}, {"required": ["url"]}],
                        },
                        "minItems": 1,
                    }
                },
                "required": ["documentSpecs"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    if name == "glean_search":
        query = arguments.get("query")
        if not query:
            raise ValueError("Query parameter is required")

        page_size = arguments.get("page_size", DEFAULT_PAGE_SIZE)
        max_snippet_size = arguments.get("max_snippet_size", DEFAULT_SNIPPET_SIZE)

        try:
            results = await glean_client.search(
                query=query, page_size=page_size, max_snippet_size=max_snippet_size
            )

            # Filter the results to remove unnecessary data
            filtered_results = filter_glean_response(results)

            # Add query information
            filtered_results["query"] = query

            return [
                TextContent(
                    type="text",
                    text=json.dumps(filtered_results, indent=2, ensure_ascii=False),
                )
            ]
        except CookieExpiredError as e:
            # Handle cookie expiration with enhanced guidance
            error_response = generate_auth_error_message()
            error_response += f"\n\n⚠️ Automatic cookie renewal not available in MCP mode.\n\nTechnical details: {str(e)}"

            return [TextContent(type="text", text=error_response)]
        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors specifically
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"

                return [TextContent(type="text", text=error_response)]
            else:
                # Other HTTP errors
                return [
                    TextContent(
                        type="text",
                        text=f"HTTP Error {e.response.status_code}: {str(e)}",
                    )
                ]
        except Exception as e:
            error_msg = str(e).lower()

            # Check for authentication errors in general exceptions
            if "unauthorized" in error_msg or "401" in error_msg or "403" in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"

                return [TextContent(type="text", text=error_response)]
            else:
                # Other errors (network, timeout, etc.)
                return [
                    TextContent(type="text", text=f"Error performing search: {str(e)}")
                ]
    elif name == "glean_research":
        query = arguments.get("query")
        if not query:
            raise ValueError("Query parameter is required")

        try:
            # Use the chat API for research
            result = await glean_client.chat(query=query)

            return [TextContent(type="text", text=result)]
        except CookieExpiredError as e:
            # Handle cookie expiration with enhanced guidance
            error_response = generate_auth_error_message()
            error_response += f"\n\n⚠️ Automatic cookie renewal not available in MCP mode.\n\nTechnical details: {str(e)}"

            return [TextContent(type="text", text=error_response)]
        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors specifically
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"

                return [TextContent(type="text", text=error_response)]
            else:
                # Other HTTP errors
                return [
                    TextContent(
                        type="text",
                        text=f"HTTP Error {e.response.status_code}: {str(e)}",
                    )
                ]
        except Exception as e:
            error_msg = str(e).lower()

            # Check for authentication errors in general exceptions
            if "unauthorized" in error_msg or "401" in error_msg or "403" in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"

                return [TextContent(type="text", text=error_response)]
            else:
                # Other errors (network, timeout, etc.)
                return [
                    TextContent(
                        type="text", text=f"Error performing research: {str(e)}"
                    )
                ]
    elif name == "read_documents":
        document_specs = arguments.get("documentSpecs")
        if not document_specs:
            raise ValueError("documentSpecs parameter is required")

        # Validate document specs
        for spec in document_specs:
            if not isinstance(spec, dict):
                raise ValueError("Each document spec must be an object")
            if not spec.get("id") and not spec.get("url"):
                raise ValueError("Each document spec must have either 'id' or 'url'")

        try:
            # Use the read_documents API
            result = await glean_client.read_documents(document_specs)

            # Format the response similar to the official implementation
            formatted_result = format_documents_response(result)

            return [TextContent(type="text", text=formatted_result)]
        except CookieExpiredError as e:
            # Handle cookie expiration with enhanced guidance
            error_response = generate_auth_error_message()
            error_response += f"\n\n⚠️ Automatic cookie renewal not available in MCP mode.\n\nTechnical details: {str(e)}"

            return [TextContent(type="text", text=error_response)]
        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors specifically
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"

                return [TextContent(type="text", text=error_response)]
            else:
                # Other HTTP errors
                return [
                    TextContent(
                        type="text",
                        text=f"HTTP Error {e.response.status_code}: {str(e)}",
                    )
                ]
        except Exception as e:
            error_msg = str(e).lower()

            # Check for authentication errors in general exceptions
            if "unauthorized" in error_msg or "401" in error_msg or "403" in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"

                return [TextContent(type="text", text=error_response)]
            else:
                # Other errors (network, timeout, etc.)
                return [
                    TextContent(type="text", text=f"Error reading documents: {str(e)}")
                ]
    else:
        raise ValueError(f"Unknown tool: {name}")


def format_documents_response(documents_response: dict) -> str:
    """
    Format documents response into a human-readable text format.

    Args:
        documents_response: The raw documents response from Glean API

    Returns:
        Formatted documents as text
    """
    if not documents_response or not documents_response.get("documents"):
        return "No documents found."

    documents = documents_response["documents"]
    if isinstance(documents, dict):
        # Convert dict to list of documents
        documents = list(documents.values())

    if not documents:
        return "No documents found."

    formatted_documents = []

    for index, doc in enumerate(documents):
        title = doc.get("title", "No title")
        url = doc.get("url", "")
        doc_type = doc.get("docType", "Document")
        datasource = doc.get("datasource", "Unknown source")

        # Extract content
        content = ""
        if doc.get("content"):
            if isinstance(doc["content"], dict):
                if doc["content"].get("fullTextList"):
                    content = "\n".join(doc["content"]["fullTextList"])
                elif doc["content"].get("fullText"):
                    content = doc["content"]["fullText"]
            elif isinstance(doc["content"], str):
                content = doc["content"]

        if not content:
            content = "No content available"

        # Extract metadata
        metadata = ""
        if doc.get("metadata"):
            if doc["metadata"].get("author", {}).get("name"):
                metadata += f"Author: {doc['metadata']['author']['name']}\n"
            if doc["metadata"].get("createTime"):
                try:
                    from datetime import datetime

                    create_time = datetime.fromisoformat(
                        doc["metadata"]["createTime"].replace("Z", "+00:00")
                    )
                    metadata += f"Created: {create_time.strftime('%Y-%m-%d')}\n"
                except Exception:
                    metadata += f"Created: {doc['metadata']['createTime']}\n"
            if doc["metadata"].get("updateTime"):
                try:
                    from datetime import datetime

                    update_time = datetime.fromisoformat(
                        doc["metadata"]["updateTime"].replace("Z", "+00:00")
                    )
                    metadata += f"Updated: {update_time.strftime('%Y-%m-%d')}\n"
                except Exception:
                    metadata += f"Updated: {doc['metadata']['updateTime']}\n"

        formatted_doc = f"""[{index + 1}] {title}
Type: {doc_type}
Source: {datasource}
{metadata}URL: {url}

Content:
{content}"""

        formatted_documents.append(formatted_doc)

    total_documents = len(documents)
    result = f"Retrieved {total_documents} document{'s' if total_documents != 1 else ''}:\n\n"
    result += "\n\n---\n\n".join(formatted_documents)

    return result


async def main():
    """Main entry point for the server."""
    global glean_client

    # Initialize the Glean client with auto-detection
    try:
        glean_client = create_glean_client()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Run the server using stdio transport
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="glean-mcp-server",
                server_version="1.6.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if glean_client:
            asyncio.run(glean_client.close())
