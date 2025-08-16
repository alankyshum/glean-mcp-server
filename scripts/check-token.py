#!/usr/bin/env python3
"""
Token health check script for Glean MCP Server.

This script verifies that your GLEAN_API_TOKEN works by making a minimal
search call to the token-based endpoint, mirroring Glean docs guidance.

Reads configuration from .env (same as check-cookies):
- GLEAN_BASE_URL
- GLEAN_API_TOKEN

Optional environment overrides:
- GLEAN_CLIENT_VERSION (defaults to 'mcp-server-token-check')
- GLEAN_ACT_AS (optional, sets X-Glean-ActAs for admin tokens)
- GLEAN_AUTH_TYPE (optional, e.g., 'OAUTH' to set X-Glean-Auth-Type: OAUTH)
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

# Add src to path (not strictly needed here, but consistent with other scripts)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def load_dotenv() -> bool:
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print(f"⚠️  .env not found at {env_path}")
        return False
    try:
        for line in env_path.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith('#') or '=' not in s:
                continue
            k, v = s.split('=', 1)
            os.environ[k] = v
        return True
    except Exception as e:
        print(f"⚠️  Failed to load .env: {e}")
        return False


def _header_overrides() -> dict:
    hdrs = {}
    auth_type = os.getenv('GLEAN_AUTH_TYPE')
    act_as = os.getenv('GLEAN_ACT_AS')
    if auth_type:
        hdrs['X-Glean-Auth-Type'] = auth_type
    if act_as:
        hdrs['X-Glean-ActAs'] = act_as
    return hdrs


async def check_token() -> bool:
    loaded = load_dotenv()

    base_url = os.getenv('GLEAN_BASE_URL')
    api_token = os.getenv('GLEAN_API_TOKEN')
    # Sanitize token from .env (strip quotes/spaces)
    if api_token:
        t = api_token.strip()
        if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
            api_token = t[1:-1]
        else:
            api_token = t

    if loaded:
        print("Loaded env from .env")
    if not base_url:
        print('❌ Missing GLEAN_BASE_URL')
        return False
    if not api_token:
        print('❌ Missing GLEAN_API_TOKEN')
        return False

    # Normalize endpoint: allow base_url with or without '/rest/api/v1'
    base = base_url.rstrip('/')
    if base.endswith('/rest/api/v1'):
        url = f"{base}/search"
    else:
        url = f"{base}/rest/api/v1/search"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        # Optional parity headers (not strictly required)
        'User-Agent': 'glean-mcp-token-check/1.0',
    }
    headers.update(_header_overrides())

    payload = {
        'query': 'test',
        'pageSize': 1,
    }

    print(f"🔍 Testing token against {base_url} ...")
    try:
        print(f"   Token length: {len(api_token) if api_token else 0}")
    except Exception:
        pass
    if 'X-Glean-Auth-Type' in headers:
        print(f"   Auth-Type: {headers['X-Glean-Auth-Type']}")
    if 'X-Glean-ActAs' in headers:
        print(f"   Act-As: {headers['X-Glean-ActAs']}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and 'results' in data:
                    print("✅ Token is valid and working!")
                    return True
                print("⚠️  200 OK but response shape unexpected — token auth likely OK.")
                return True
            elif r.status_code in (401, 403):
                print("❌ Token is invalid or expired (auth error)")
                return False
            else:
                body = r.text[:500].replace('\n', ' ')
                print(f"⚠️  Non-200 response: {r.status_code}")
                print(f"    Body (truncated): {body}")
                return False
        except httpx.TimeoutException:
            print("⚠️  Connection timeout - check network or base URL")
            return False
        except Exception as e:
            print(f"❌ Error testing token: {e}")
            return False


def main() -> int:
    ok = asyncio.run(check_token())
    if ok:
        print("\n🎉 Token check passed")
        return 0
    else:
        print("\n🔄 If needed, update GLEAN_API_TOKEN in .env and rerun.")
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
