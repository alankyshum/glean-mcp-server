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
import random
import string
import httpx

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


# Simple dotenv replacement
def load_dotenv():
    """Simple .env file loader."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print(f"❌ .env file not found at {env_path}")
        return False
    return True


def _rand_token(n: int = 16) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


async def check_cookie_validity():
    """Check if current cookies are still valid by mimicking the working curl."""
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES")
    # Sanitize possible surrounding quotes/spaces from .env
    if cookies:
        c = cookies.strip()
        if (c.startswith('"') and c.endswith('"')) or (
            c.startswith("'") and c.endswith("'")
        ):
            cookies = c[1:-1]
        else:
            cookies = c

    if not base_url or not cookies:
        print("❌ Missing GLEAN_BASE_URL or GLEAN_COOKIES in environment")
        return False

    print(f"🔍 Testing connection to {base_url}...")
    # Minimal debug without leaking secrets
    try:
        parts = [p.strip() for p in cookies.split(";") if p.strip()]
        names = [p.split("=", 1)[0] for p in parts]
        print(
            f"   Using cookies: {', '.join(names[:5])}{'...' if len(names)>5 else ''}"
        )
    except Exception:
        pass

    # Match the curl as closely as possible
    params = {
        "clientVersion": os.getenv(
            "GLEAN_CLIENT_VERSION", "fe-release-2025-08-07-25f2142"
        ),
        "locale": "en",
    }

    now_iso = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
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
            "clientVersion": params["clientVersion"],
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
        "cookie": cookies,
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

    url = f"{base_url.rstrip('/')}/api/v1/search"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(url, params=params, json=payload, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "results" in data:
                    print("✅ Cookies are valid and working!")
                    return True
                print(
                    "⚠️  Unexpected response format (200) – treating as valid for auth, but structure differs."
                )
                return True
            elif r.status_code in (401, 403):
                print("❌ Cookies have expired or are invalid (auth error)")
                return False
            else:
                body = r.text[:500].replace("\n", " ")
                print(f"⚠️  Non-200 response: {r.status_code}")
                print(f"    Body (truncated): {body}")
                print("    This may be due to payload/param drift rather than cookies.")
                return False
        except httpx.TimeoutException:
            print("⚠️  Connection timeout - check your network or Glean URL")
            return False
        except Exception as e:
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
    print('7. Run: python scripts/update-cookies.py "PASTE_COOKIES_HERE"')
    print("\nOr manually update your .env file with the new GLEAN_COOKIES value")


def estimate_cookie_age():
    """Try to estimate when cookies might expire."""
    try:
        env_file = Path(".env")
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
