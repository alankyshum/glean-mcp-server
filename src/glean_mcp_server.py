"""
Glean MCP Server - A Model Context Protocol server for Glean search functionality.
"""
import asyncio
import os
import sys
from typing import Any, Sequence
import json

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl
from dotenv import load_dotenv

from glean_client import GleanClient

# Load environment variables
load_dotenv()

# Get configuration from environment variables
DEFAULT_PAGE_SIZE = int(os.getenv("GLEAN_DEFAULT_PAGE_SIZE", "14"))
DEFAULT_SNIPPET_SIZE = int(os.getenv("GLEAN_DEFAULT_SNIPPET_SIZE", "215"))
TOOL_DESCRIPTION = os.getenv("GLEAN_TOOL_DESCRIPTION", "Search for internal company information")

# Initialize the MCP server
server = Server("glean-mcp-server")

# Global client instance
glean_client: GleanClient = None


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

            # Format the results for better readability
            formatted_results = {
                "query": query,
                "total_results": len(results.get("results", [])),
                "results": results.get("results", []),
                "facets": results.get("facets", []),
                "spellcheck": results.get("spellcheck", {}),
                "debug_info": results.get("debugInfo", {})
            }

            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_results, indent=2, ensure_ascii=False)
                )
            ]
        except Exception as e:
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
                server_version="1.0.0",
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
