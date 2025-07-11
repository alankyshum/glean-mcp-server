#!/usr/bin/env python3
"""
Cookie health check script for Glean MCP Server.

This script checks if your current cookies are still valid and provides
renewal instructions if they're expired.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Simple dotenv replacement
def load_dotenv():
    """Simple .env file loader."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print(f"❌ .env file not found at {env_path}")
        return False
    return True

async def check_cookie_validity():
    """Check if current cookies are still valid."""
    try:
        from glean_client import GleanClient
        
        base_url = os.getenv("GLEAN_BASE_URL")
        cookies = os.getenv("GLEAN_COOKIES")
        
        if not base_url or not cookies:
            print("❌ Missing GLEAN_BASE_URL or GLEAN_COOKIES in environment")
            return False
        
        print(f"🔍 Testing connection to {base_url}...")
        
        client = GleanClient(base_url=base_url, cookies=cookies)
        
        # Try a simple search
        result = await client.search("test", page_size=1, max_snippet_size=50)
        await client.close()
        
        if result and 'results' in result:
            print("✅ Cookies are valid and working!")
            return True
        else:
            print("⚠️  Unexpected response format")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'unauthorized' in error_msg or '401' in error_msg or '403' in error_msg:
            print("❌ Cookies have expired or are invalid")
        elif 'timeout' in error_msg or 'connection' in error_msg:
            print("⚠️  Connection timeout - check your network or Glean URL")
        else:
            print(f"❌ Error testing cookies: {e}")
        return False

def show_renewal_instructions():
    """Show instructions for renewing cookies."""
    print("\n🔄 Cookie Renewal Instructions:")
    print("=" * 50)
    print("1. Open your browser and go to your Glean instance")
    print("2. Make sure you're logged in")
    print("3. Open Developer Tools (F12) → Network tab")
    print("4. Perform a search in Glean to trigger API requests")
    print("5. Find any search API request → Right-click → Copy as cURL")
    print("6. Extract the Cookie header value from the cURL command")
    print("7. Run: python scripts/update-cookies.py \"PASTE_COOKIES_HERE\"")
    print("\nOr manually update your .env file with the new GLEAN_COOKIES value")

def estimate_cookie_age():
    """Try to estimate when cookies might expire."""
    try:
        env_file = Path('.env')
        if env_file.exists():
            mtime = datetime.fromtimestamp(env_file.stat().st_mtime)
            age = datetime.now() - mtime
            
            print(f"📅 .env file last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Age: {age.days} days, {age.seconds // 3600} hours")
            
            # Estimate expiry (assuming 7-day expiry)
            estimated_expiry = mtime + timedelta(days=7)
            if datetime.now() > estimated_expiry:
                print("🚨 Cookies likely expired (>7 days old)")
            elif datetime.now() > estimated_expiry - timedelta(days=1):
                print("⚠️  Cookies expiring soon (<1 day remaining)")
            else:
                days_left = (estimated_expiry - datetime.now()).days
                print(f"✅ Cookies should be valid (~{days_left} days remaining)")
    except Exception as e:
        print(f"⚠️  Could not estimate cookie age: {e}")

async def main():
    """Main function."""
    print("🍪 Glean Cookie Health Check")
    print("=" * 30)
    
    # Load environment
    if not load_dotenv():
        print("\n💡 Create a .env file first:")
        print("cp .env.example .env")
        print("# Then edit .env with your Glean URL and cookies")
        return
    
    # Estimate cookie age
    estimate_cookie_age()
    print()
    
    # Test cookie validity
    is_valid = await check_cookie_validity()
    
    if not is_valid:
        show_renewal_instructions()
        sys.exit(1)
    else:
        print("\n🎉 All good! Your cookies are working properly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Check cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
