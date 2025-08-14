"""MCP server entrypoint for Glean.

Run with:
    python -m glean_mcp.server

Implements the tools:
  - glean_search
  - glean_research
  - read_documents
"""
from __future__ import annotations

import asyncio
import os
import sys
import webbrowser
from typing import Any
import json
import httpx
import time

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

from .glean_client import GleanClient, CookieExpiredError  # type: ignore
from .glean_filter import filter_glean_response  # type: ignore

load_dotenv()

DEFAULT_PAGE_SIZE = int(os.getenv("GLEAN_DEFAULT_PAGE_SIZE", "14"))
DEFAULT_SNIPPET_SIZE = int(os.getenv("GLEAN_DEFAULT_SNIPPET_SIZE", "215"))
TOOL_DESCRIPTION = os.getenv("GLEAN_TOOL_DESCRIPTION", "Search for internal company information")
AUTO_OPEN_BROWSER = os.getenv("GLEAN_AUTO_OPEN_BROWSER", "true").lower() == "true"

server = Server("glean-mcp-server")
glean_client: GleanClient | None = None


def prompt_for_new_cookies() -> str:
    raise CookieExpiredError(
        "Cookies have expired. Please update your MCP configuration with fresh cookies and restart."
    )


def generate_auth_error_message() -> str:
    base_url = os.getenv("GLEAN_BASE_URL", "your-glean-instance.com")
    clean_url = base_url
    if clean_url.endswith('/api/v1/search'):
        clean_url = clean_url.replace('/api/v1/search', '')

    company_name = "your company"
    if "-be.glean.com" in clean_url:
        try:
            company_part = clean_url.replace("https://", "").replace("http://", "")
            if company_part.endswith("-be.glean.com"):
                company_name = company_part.replace("-be.glean.com", "")
        except:  # noqa: E722
            pass

    browser_opened = False
    if AUTO_OPEN_BROWSER:
        try:
            webbrowser.open(clean_url)
            browser_opened = True
        except:  # noqa: E722
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
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    if uri.scheme != "glean":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
    if uri.path == "/search":
        return json.dumps({
            "description": "Glean search resource",
            "usage": "Use the glean_search tool to perform searches",
            "available_tools": ["glean_search"]
        })
    if uri.path == "/research":
        return json.dumps({
            "description": "Glean research resource",
            "usage": "Use the glean_research tool to get AI-powered answers from your knowledge base",
            "available_tools": ["glean_research"]
        })
    raise ValueError(f"Unknown resource path: {uri.path}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="glean_search",
            description=TOOL_DESCRIPTION,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to execute"},
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
        ),
        Tool(
            name="glean_research",
            description="Research and get AI-powered answers from your company's knowledge base using Glean's chat AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The research question or topic to investigate"}
                },
                "required": ["query"]
            }
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
                                "id": {"type": "string", "description": "Glean Document ID"},
                                "url": {"type": "string", "description": "Document URL"}
                            },
                            "anyOf": [
                                {"required": ["id"]},
                                {"required": ["url"]}
                            ]
                        },
                        "minItems": 1
                    }
                },
                "required": ["documentSpecs"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name == "glean_search":
        query = arguments.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        page_size = arguments.get("page_size", DEFAULT_PAGE_SIZE)
        max_snippet_size = arguments.get("max_snippet_size", DEFAULT_SNIPPET_SIZE)
        try:
            results = await glean_client.search(  # type: ignore[union-attr]
                query=query,
                page_size=page_size,
                max_snippet_size=max_snippet_size
            )
            filtered_results = filter_glean_response(results)
            filtered_results["query"] = query
            return [TextContent(type="text", text=json.dumps(filtered_results, indent=2, ensure_ascii=False))]
        except CookieExpiredError as e:
            error_response = generate_auth_error_message()
            error_response += f"\n\n⚠️ Automatic cookie renewal not available in MCP mode.\n\nTechnical details: {str(e)}"
            return [TextContent(type="text", text=error_response)]
        except httpx.HTTPStatusError as e:  # pragma: no cover - network path
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"
                return [TextContent(type="text", text=error_response)]
            return [TextContent(type="text", text=f"HTTP Error {e.response.status_code}: {str(e)}")]
        except Exception as e:  # noqa: BLE001
            error_msg = str(e).lower()
            if 'unauthorized' in error_msg or '401' in error_msg or '403' in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"
                return [TextContent(type="text", text=error_response)]
            return [TextContent(type="text", text=f"Error performing search: {str(e)}")]
    if name == "glean_research":
        query = arguments.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        try:
            result = await glean_client.chat(query=query)  # type: ignore[union-attr]
            return [TextContent(type="text", text=result)]
        except CookieExpiredError as e:
            error_response = generate_auth_error_message()
            error_response += f"\n\n⚠️ Automatic cookie renewal not available in MCP mode.\n\nTechnical details: {str(e)}"
            return [TextContent(type="text", text=error_response)]
        except httpx.HTTPStatusError as e:  # pragma: no cover - network path
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"
                return [TextContent(type="text", text=error_response)]
            return [TextContent(type="text", text=f"HTTP Error {e.response.status_code}: {str(e)}")]
        except Exception as e:  # noqa: BLE001
            error_msg = str(e).lower()
            if 'unauthorized' in error_msg or '401' in error_msg or '403' in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"
                return [TextContent(type="text", text=error_response)]
            return [TextContent(type="text", text=f"Error performing research: {str(e)}")]
    if name == "read_documents":
        document_specs = arguments.get("documentSpecs")
        if not document_specs:
            raise ValueError("documentSpecs parameter is required")
        for spec in document_specs:
            if not isinstance(spec, dict):
                raise ValueError("Each document spec must be an object")
            if not spec.get("id") and not spec.get("url"):
                raise ValueError("Each document spec must have either 'id' or 'url'")
        try:
            result = await glean_client.read_documents(document_specs)  # type: ignore[union-attr]
            formatted_result = format_documents_response(result)
            return [TextContent(type="text", text=formatted_result)]
        except CookieExpiredError as e:
            error_response = generate_auth_error_message()
            error_response += f"\n\n⚠️ Automatic cookie renewal not available in MCP mode.\n\nTechnical details: {str(e)}"
            return [TextContent(type="text", text=error_response)]
        except httpx.HTTPStatusError as e:  # pragma: no cover - network path
            if e.response.status_code in [401, 403]:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: HTTP {e.response.status_code} - {e.response.reason_phrase}"
                return [TextContent(type="text", text=error_response)]
            return [TextContent(type="text", text=f"HTTP Error {e.response.status_code}: {str(e)}")]
        except Exception as e:  # noqa: BLE001
            error_msg = str(e).lower()
            if 'unauthorized' in error_msg or '401' in error_msg or '403' in error_msg:
                error_response = generate_auth_error_message()
                error_response += f"\n\nTechnical details: {str(e)}"
                return [TextContent(type="text", text=error_response)]
            return [TextContent(type="text", text=f"Error reading documents: {str(e)}")]
    raise ValueError(f"Unknown tool: {name}")


def format_documents_response(documents_response: dict) -> str:
    if not documents_response or not documents_response.get("documents"):
        return "No documents found."
    documents = documents_response["documents"]
    if isinstance(documents, dict):
        documents = list(documents.values())
    if not documents:
        return "No documents found."
    formatted_documents: list[str] = []
    for index, doc in enumerate(documents):
        title = doc.get("title", "No title")
        url = doc.get("url", "")
        doc_type = doc.get("docType", "Document")
        datasource = doc.get("datasource", "Unknown source")
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
        metadata = ""
        if doc.get("metadata"):
            if doc["metadata"].get("author", {}).get("name"):
                metadata += f"Author: {doc['metadata']['author']['name']}\n"
            if doc["metadata"].get("createTime"):
                try:
                    from datetime import datetime
                    create_time = datetime.fromisoformat(doc["metadata"]["createTime"].replace("Z", "+00:00"))
                    metadata += f"Created: {create_time.strftime('%Y-%m-%d')}\n"
                except:  # noqa: E722
                    metadata += f"Created: {doc['metadata']['createTime']}\n"
            if doc["metadata"].get("updateTime"):
                try:
                    from datetime import datetime
                    update_time = datetime.fromisoformat(doc["metadata"]["updateTime"].replace("Z", "+00:00"))
                    metadata += f"Updated: {update_time.strftime('%Y-%m-%d')}\n"
                except:  # noqa: E722
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


async def main():  # pragma: no cover - runtime entry
    global glean_client
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES")
    if not base_url:
        raise ValueError("GLEAN_BASE_URL environment variable is required")
    if not cookies:
        raise ValueError("GLEAN_COOKIES environment variable is required")
    start_ts = time.time()
    print(f"[glean-mcp-server] Starting with base_url={base_url} len(cookies)={len(cookies)}", file=sys.stderr)
    glean_client = GleanClient(base_url=base_url, cookies=cookies, cookie_renewal_callback=prompt_for_new_cookies)
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        print(f"[glean-mcp-server] stdio server established after {time.time()-start_ts:.3f}s", file=sys.stderr)

        async def run_server():
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

        # Run server in background and keep process alive indefinitely.
        task = asyncio.create_task(run_server())
        try:
            while True:
                if task.done():
                    # If it finished unexpectedly, log and break
                    print("[glean-mcp-server] server task completed early", file=sys.stderr)
                    exc = task.exception()
                    if exc:
                        print(f"[glean-mcp-server] server task exception: {exc}", file=sys.stderr)
                    break
                await asyncio.sleep(2)
        except asyncio.CancelledError:  # pragma: no cover
            pass
    print("[glean-mcp-server] Shutdown complete", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - module exec
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        print("Server stopped by user")
    except Exception as e:  # noqa: BLE001
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if glean_client:
            asyncio.run(glean_client.close())
