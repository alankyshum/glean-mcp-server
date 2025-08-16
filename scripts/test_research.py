#!/usr/bin/env python3
"""
Quick tester for research-like calls (search/chat) using token and/or cookie auth.

Usage:
  export GLEAN_BASE_URL="https://<your>-be.glean.com"
  export GLEAN_COOKIES='<cookie string>'
  export GLEAN_API_TOKEN='<your-api-token>'
  python3 scripts/test_research.py --query "what is foo" [--mode search|chat]

Note: Prints concise outputs to avoid leaking sensitive content.
"""
import asyncio
import os
import sys
import argparse
from pathlib import Path
from typing import Tuple

# Ensure src on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from glean_mcp.cookie_client import GleanClient, CookieExpiredError
from glean_mcp.token_client import TokenBasedGleanClient, TokenExpiredError


def load_dotenv() -> bool:
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        return False
    try:
        for line in env_path.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith('#') or '=' not in s:
                continue
            k, v = s.split('=', 1)
            os.environ[k] = v
        return True
    except Exception:
        return False


def _sanitize(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


async def run_mode(mode: str, client: GleanClient, query: str) -> Tuple[bool, str]:
    try:
        if mode == 'search':
            res = await client.search(query=query, page_size=1)
            # Extract a minimal summary
            total = res.get('resultCounts', {}).get('ALL', {}).get('count') if isinstance(res, dict) else None
            keys = list(res.keys())[:5] if isinstance(res, dict) else []
            return True, f"OK ({mode}) keys={keys} total={total}"
        else:
            text = await client.chat(query)
            snippet = (text or '').strip().splitlines()[0][:160] if isinstance(text, str) else ''
            return True, f"OK ({mode}) snippet={snippet}"
    except (CookieExpiredError, TokenExpiredError) as e:
        return False, f"AUTH ERROR: {e}"
    except Exception as e:
        return False, f"ERROR: {e}"


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True)
    parser.add_argument('--mode', choices=['search', 'chat'], default='search')
    args = parser.parse_args()

    loaded = load_dotenv()
    base_url = os.environ.get('GLEAN_BASE_URL')
    api_token = _sanitize(os.environ.get('GLEAN_API_TOKEN'))
    cookies = _sanitize(os.environ.get('GLEAN_COOKIES'))
    if loaded:
        print('Loaded env from .env')
    if not base_url:
        print('Missing GLEAN_BASE_URL'); return 2
    if not api_token and not cookies:
        print('Missing GLEAN_API_TOKEN and GLEAN_COOKIES'); return 2

    modes = []
    if api_token:
        modes.append(('token', TokenBasedGleanClient(base_url=base_url, api_token=api_token)))
    if cookies:
        modes.append(('cookie', GleanClient(base_url=base_url, cookies=cookies)))

    overall_ok = True
    for auth_mode, client in modes:
        ok, msg = await run_mode(args.mode, client, args.query)
        print(f"{auth_mode}: {msg}")
        try:
            await client.close()
        except Exception:
            pass
        if not ok:
            overall_ok = False

    return 0 if overall_ok else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
