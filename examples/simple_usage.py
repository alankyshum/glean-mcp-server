#!/usr/bin/env python3
"""
Simple usage examples for the Glean MCP clients.

This example demonstrates the simplified structure with just 3 files:
- cookie_client.py: Cookie-based authentication
- token_client.py: Token-based authentication  
- glean_mcp_server.py: MCP server with auto-detection

Prerequisites:
Set one of these environment variables:
- GLEAN_API_TOKEN (preferred): Your Glean API token
- GLEAN_COOKIES: Browser cookies from Glean session

And optionally:
- GLEAN_BASE_URL: Your Glean instance URL
- GLEAN_INSTANCE: Your company name (if no base URL)
"""

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def cookie_client_example():
    """Example using cookie-based authentication directly."""
    print("=== Cookie Client Example ===")
    
    from cookie_client import GleanClient, CookieExpiredError
    
    base_url = os.getenv("GLEAN_BASE_URL", "https://linkedin-be.glean.com")
    cookies = os.getenv("GLEAN_COOKIES")
    
    if not cookies:
        print("❌ GLEAN_COOKIES not set, skipping cookie example")
        return
    
    try:
        client = GleanClient(base_url, cookies)
        print(f"✅ Created cookie-based client for {base_url}")
        
        # Example search
        results = await client.search("onboarding", page_size=3)
        print(f"🔍 Search found {len(results.get('results', []))} results")
        
        await client.close()
        
    except CookieExpiredError as e:
        print(f"🍪 Cookie expired: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def token_client_example():
    """Example using token-based authentication directly."""
    print("\n=== Token Client Example ===")
    
    from token_client import TokenBasedGleanClient, TokenExpiredError
    
    base_url = os.getenv("GLEAN_BASE_URL", "https://linkedin-be.glean.com")
    api_token = os.getenv("GLEAN_API_TOKEN")
    
    if not api_token:
        print("❌ GLEAN_API_TOKEN not set, skipping token example")
        return
    
    try:
        client = TokenBasedGleanClient(base_url, api_token)
        print(f"✅ Created token-based client for {base_url}")
        
        # Example search
        results = await client.search("team structure", page_size=3)
        print(f"🔍 Search found {len(results.get('results', []))} results")
        
        await client.close()
        
    except TokenExpiredError as e:
        print(f"🔑 Token expired: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def auto_detection_example():
    """Example using the MCP server's auto-detection."""
    print("\n=== Auto-Detection Example ===")
    
    from glean_mcp_server import create_glean_client
    
    try:
        client = create_glean_client()
        client_type = "Token-based" if "Token" in type(client).__name__ else "Cookie-based"
        print(f"✅ Auto-detected {client_type} authentication")
        
        # Example search
        results = await client.search("company policies", page_size=3)
        print(f"🔍 Search found {len(results.get('results', []))} results")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print("Glean MCP Clients - Simple Usage Examples")
    print("=" * 50)
    
    # Check configuration
    has_token = bool(os.getenv("GLEAN_API_TOKEN"))
    has_cookies = bool(os.getenv("GLEAN_COOKIES"))
    
    if not has_token and not has_cookies:
        print("❌ No authentication configured!")
        print("\nPlease set one of:")
        print("  export GLEAN_API_TOKEN='your-token-here'")
        print("  export GLEAN_COOKIES='your-cookies-here'")
        return
    
    print(f"🔧 Configuration:")
    print(f"  - Token auth: {'✅' if has_token else '❌'}")
    print(f"  - Cookie auth: {'✅' if has_cookies else '❌'}")
    print(f"  - Base URL: {os.getenv('GLEAN_BASE_URL', 'Not set (will use instance)')}")
    print(f"  - Instance: {os.getenv('GLEAN_INSTANCE', 'linkedin')}")
    
    # Run examples
    asyncio.run(cookie_client_example())
    asyncio.run(token_client_example())
    asyncio.run(auto_detection_example())
    
    print("\n" + "=" * 50)
    print("✅ Examples completed!")
    print("\n📁 Simplified structure:")
    print("  src/")
    print("    ├── cookie_client.py      # Cookie-based auth")
    print("    ├── token_client.py       # Token-based auth")
    print("    ├── glean_mcp_server.py   # MCP server (auto-detects)")
    print("    └── glean_filter.py       # Response filtering")


if __name__ == "__main__":
    main()
