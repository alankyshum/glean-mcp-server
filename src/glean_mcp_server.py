"""
Glean MCP Server - A Model Context Protocol server for Glean search functionality.
"""
import asyncio
import os
import sys
import webbrowser
from typing import Any
import json
import httpx

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)
from pydantic import AnyUrl
from dotenv import load_dotenv

from glean_client import GleanClient
from glean_filter import filter_glean_response

# Load environment variables
load_dotenv()

# Get configuration from environment variables
DEFAULT_PAGE_SIZE = int(os.getenv("GLEAN_DEFAULT_PAGE_SIZE", "14"))
DEFAULT_SNIPPET_SIZE = int(os.getenv("GLEAN_DEFAULT_SNIPPET_SIZE", "215"))
TOOL_DESCRIPTION = os.getenv("GLEAN_TOOL_DESCRIPTION", "Search for internal company information")
AUTO_OPEN_BROWSER = os.getenv("GLEAN_AUTO_OPEN_BROWSER", "true").lower() == "true"

# Initialize the MCP server
server = Server("glean-mcp-server")

# Global client instance
glean_client: GleanClient = None


def generate_auth_error_message() -> str:
    """Generate a personalized authentication error message and optionally open browser."""
    base_url = os.getenv("GLEAN_BASE_URL", "your-glean-instance.com")

    # Clean up the URL to get the main domain
    clean_url = base_url
    if clean_url.endswith('/api/v1/search'):
        clean_url = clean_url.replace('/api/v1/search', '')
    if clean_url.endswith('-be.glean.com'):
        clean_url = clean_url.replace('-be.glean.com', '.glean.com')

    # Extract company name from URL for personalization
    company_name = "your company"
    if ".glean.com" in clean_url:
        try:
            # Extract company name from URL like https://company.glean.com
            company_part = clean_url.replace("https://", "").replace("http://", "")
            if company_part.endswith(".glean.com"):
                company_name = company_part.replace(".glean.com", "")
        except:
            pass

    # Try to open the browser automatically (if enabled)
    browser_opened = False
    if AUTO_OPEN_BROWSER:
        try:
            webbrowser.open(clean_url)
            browser_opened = True
        except:
            pass

    browser_message = "🌐 Opening your Glean page in browser..." if browser_opened else ""

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


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=AnyUrl("glean://search"),
            name="Glean Search",
            description="Search functionality for Glean knowledge base",
            mimeType="application/json",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    if uri.scheme != "glean":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    if uri.path == "/search":
        return json.dumps({
            "description": "Glean search resource",
            "usage": "Use the glean_search tool to perform searches",
            "available_tools": ["glean_search"]
        })
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
                        "description": "The search query to execute"
                    },
                    "page_size": {
                        "type": "integer",
                        "description": f"Number of results to return (default: {DEFAULT_PAGE_SIZE}, configurable via GLEAN_DEFAULT_PAGE_SIZE)",
                        "default": DEFAULT_PAGE_SIZE,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "max_snippet_size": {
                        "type": "integer",
                        "description": f"Maximum size of result snippets (default: {DEFAULT_SNIPPET_SIZE}, configurable via GLEAN_DEFAULT_SNIPPET_SIZE)",
                        "default": DEFAULT_SNIPPET_SIZE,
                        "minimum": 50,
                        "maximum": 1000
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    if name == "glean_search":
        query = arguments.get("query")
        if not query:
            raise ValueError("Query parameter is required")

        page_size = arguments.get("page_size", DEFAULT_PAGE_SIZE)
        max_snippet_size = arguments.get("max_snippet_size", DEFAULT_SNIPPET_SIZE)

        try:
            results = await glean_client.search(
                query=query,
                page_size=page_size,
                max_snippet_size=max_snippet_size
            )

            # Filter the results to remove unnecessary data
            filtered_results = filter_glean_response(results)

            # Add query information
            filtered_results["query"] = query

            return [
                TextContent(
                    type="text",
                    text=json.dumps(filtered_results, indent=2, ensure_ascii=False)
                )
            ]
        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors specifically
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"

                return [
                    TextContent(
                        type="text",
                        text=error_response
                    )
                ]
            else:
                # Other HTTP errors
                return [
                    TextContent(
                        type="text",
                        text=f"HTTP Error {e.response.status_code}: {str(e)}"
                    )
                ]
        except Exception as e:
            error_msg = str(e).lower()

            # Check for authentication errors in general exceptions
            if 'unauthorized' in error_msg or '401' in error_msg or '403' in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"

                return [
                    TextContent(
                        type="text",
                        text=error_response
                    )
                ]
            else:
                # Other errors (network, timeout, etc.)
                return [
                    TextContent(
                        type="text",
                        text=f"Error performing search: {str(e)}"
                    )
                ]
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the server."""
    global glean_client

    # Get configuration from environment variables
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES")

    if not base_url:
        raise ValueError("GLEAN_BASE_URL environment variable is required")
    if not cookies:
        raise ValueError("GLEAN_COOKIES environment variable is required")

    # Initialize the Glean client
    glean_client = GleanClient(base_url=base_url, cookies=cookies)

    # Run the server using stdio transport
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="glean-mcp-server",
                server_version="1.3.0",
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
