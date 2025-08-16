#!/usr/bin/env python3
"""
Interactive cookie renewal script for Glean MCP Server.

This script demonstrates how cookie renewal could work in an interactive environment.
For MCP usage, users need to manually update their configuration when cookies expire.
"""
import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from glean_client import GleanClient, CookieExpiredError


def prompt_for_cookies() -> str:
    """
    Interactively prompt the user for new cookies.

    Returns:
        New cookie string from user input
    """
    print("\n🔑 Cookie Renewal Required")
    print("=" * 50)
    print("Your Glean cookies have expired. Please provide new cookies.")
    print("\nTo get new cookies:")
    print("1. Go to your Glean instance in browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Network tab")
    print("4. Perform a search to trigger API requests")
    print("5. Find a search API request → Right-click → Copy as cURL")
    print("6. Extract the Cookie header value")
    print("\nPaste your new cookies below:")

    new_cookies = input("Cookies: ").strip()

    if not new_cookies:
        raise ValueError("No cookies provided")

    return new_cookies


async def test_cookie_renewal():
    """Test the cookie renewal functionality."""
    # Use environment variables for initial setup
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES", "invalid_cookies_for_testing")

    if not base_url:
        print("Error: GLEAN_BASE_URL environment variable is required")
        return

    print(f"Testing cookie renewal with Glean instance: {base_url}")

    # Create client with cookie renewal callback
    client = GleanClient(
        base_url=base_url, cookies=cookies, cookie_renewal_callback=prompt_for_cookies
    )

    try:
        # Test search - this should trigger cookie validation
        print("\n🔍 Testing search functionality...")
        results = await client.search("test query", page_size=1)
        print("✅ Search successful!")
        print(f"Found {results.get('total_results', 0)} results")

    except CookieExpiredError as e:
        print(f"❌ Cookie renewal failed: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.close()


async def test_chat_renewal():
    """Test the chat functionality with cookie renewal."""
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES", "invalid_cookies_for_testing")

    if not base_url:
        print("Error: GLEAN_BASE_URL environment variable is required")
        return

    client = GleanClient(
        base_url=base_url, cookies=cookies, cookie_renewal_callback=prompt_for_cookies
    )

    try:
        # Test chat - this should trigger cookie validation
        print("\n💬 Testing chat functionality...")
        response = await client.chat(message="What is the current deployment status?")
        print("✅ Chat successful!")
        print(f"Response length: {len(response)} characters")

    except CookieExpiredError as e:
        print(f"❌ Cookie renewal failed: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    print("🧪 Glean MCP Server - Interactive Cookie Renewal Test")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        asyncio.run(test_chat_renewal())
    else:
        asyncio.run(test_cookie_renewal())

    print("\n💡 For MCP usage:")
    print("   - Update GLEAN_COOKIES in your MCP configuration")
    print("   - Restart Cursor/VS Code to reload the MCP server")
