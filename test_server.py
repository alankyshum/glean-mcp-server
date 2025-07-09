#!/usr/bin/env python3
"""
Test script for Glean MCP Server
"""
import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

from glean_client import GleanClient


async def test_glean_client():
    """Test the Glean client functionality."""
    load_dotenv()
    
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES")
    
    if not base_url or not cookies:
        print("❌ Missing required environment variables:")
        print("   - GLEAN_BASE_URL")
        print("   - GLEAN_COOKIES")
        print("\nPlease copy .env.example to .env and configure it.")
        return False
    
    print(f"🔍 Testing Glean client with base URL: {base_url}")
    
    client = GleanClient(base_url=base_url, cookies=cookies)
    
    try:
        # Test search
        print("📡 Performing test search...")
        results = await client.search("testing", page_size=5)
        
        print("✅ Search successful!")
        print(f"📊 Results summary:")
        print(f"   - Total results: {len(results.get('results', []))}")
        print(f"   - Has facets: {bool(results.get('facets'))}")
        print(f"   - Has spellcheck: {bool(results.get('spellcheck'))}")
        
        # Print first result if available
        if results.get('results'):
            first_result = results['results'][0]
            print(f"\n📄 First result:")
            print(f"   - Title: {first_result.get('title', 'N/A')}")
            print(f"   - URL: {first_result.get('url', 'N/A')}")
            print(f"   - Snippet: {first_result.get('snippet', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return False
    
    finally:
        await client.close()


async def main():
    """Main test function."""
    print("🚀 Glean MCP Server Test")
    print("=" * 40)
    
    success = await test_glean_client()
    
    if success:
        print("\n✅ All tests passed! The server should work correctly.")
        print("\n🐳 To run with Docker:")
        print("   docker-compose up -d")
        print("\n🔧 To run locally:")
        print("   python src/glean_mcp_server.py")
    else:
        print("\n❌ Tests failed. Please check your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
