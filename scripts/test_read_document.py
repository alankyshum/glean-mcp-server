#!/usr/bin/env python3
"""
Quick tester for read_documents using token and/or cookie auth.

Usage:
  export GLEAN_BASE_URL="https://<your>-be.glean.com"
    export GLEAN_COOKIES '<cookie string>'
    export GLEAN_API_TOKEN='<your-api-token>'
    python3 scripts/test_read_document.py --id <DOCUMENT_ID>
  # or
  python3 scripts/test_read_document.py --url <DOCUMENT_URL>

Note: This prints only high-level fields of the response to avoid leaking sensitive content.
"""
import asyncio
import os
import sys
import argparse
from pathlib import Path

# Ensure src on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from glean_mcp.cookie_client import GleanClient, CookieExpiredError
from glean_mcp.token_client import TokenBasedGleanClient, TokenExpiredError


def load_dotenv() -> bool:
    """Simple .env loader to align with other scripts."""
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


async def main() -> int:
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--id', dest='doc_id')
    g.add_argument('--url', dest='doc_url')
    args = parser.parse_args()

    # Load .env if present so we use the verified cookie/base URL
    loaded = load_dotenv()
    base_url = os.environ.get('GLEAN_BASE_URL')
    api_token = os.environ.get('GLEAN_API_TOKEN')
    cookies = os.environ.get('GLEAN_COOKIES')
    # Sanitize token and cookies similar to check scripts
    if api_token:
        t = api_token.strip()
        if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
            api_token = t[1:-1]
        else:
            api_token = t
    # Sanitize cookies similar to check-cookies.py
    if cookies:
        c = cookies.strip()
        if (c.startswith('"') and c.endswith('"')) or (c.startswith("'") and c.endswith("'")):
            cookies = c[1:-1]
        else:
            cookies = c
    if loaded:
        print("Loaded env from .env")
    if not base_url:
        print('Missing GLEAN_BASE_URL'); return 2
    if not api_token and not cookies:
        print('Missing GLEAN_API_TOKEN and GLEAN_COOKIES'); return 2

    spec = {'id': args.doc_id} if args.doc_id else {'url': args.doc_url}

    # Try both modes when available; token first, then cookie
    modes = []
    if api_token:
        modes.append(('token', TokenBasedGleanClient(base_url=base_url, api_token=api_token)))
    if cookies:
        modes.append(('cookie', GleanClient(base_url=base_url, cookies=cookies)))

    overall_ok = True
    for auth_mode, client in modes:
        try:
            resp = await client.read_documents([spec])
            docs = resp.get('documents') or {}
            print(f'OK (auth={auth_mode})')
            print(f"keys: {list(docs.keys())[:5]}")
            # If a single doc id, show brief info
            if isinstance(docs, dict) and len(docs) == 1:
                for k, v in docs.items():
                    title = v.get('title') or v.get('document', {}).get('title')
                    print(f"docId: {k}")
                    if title:
                        print(f"title: {title[:120]}")
                    if 'url' in v:
                        print(f"url: {v['url'][:200]}")
        except (CookieExpiredError, TokenExpiredError) as e:
            overall_ok = False
            print(f"AUTH ERROR ({auth_mode}): {e}")
        except Exception as e:
            overall_ok = False
            print(f"ERROR ({auth_mode}): {e}")
        finally:
            try:
                await client.close()
            except Exception:
                pass

    return 0 if overall_ok else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
