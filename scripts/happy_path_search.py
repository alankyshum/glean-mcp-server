#!/usr/bin/env python3
"""Happy path direct search test (bypasses MCP framing).

Hard-coded base URL and cookie supplied earlier. Performs one search for
'lighthouse-web' and prints minimal JSON with success flag and titles.
"""
from __future__ import annotations
import asyncio, json, os, sys

try:
    from glean_mcp.glean_client import GleanClient, CookieExpiredError  # type: ignore
except ModuleNotFoundError:
    # Add src directory for direct execution without installation
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from glean_mcp.glean_client import GleanClient, CookieExpiredError  # type: ignore

BASE_URL = "https://linkedin-be.glean.com"
COOKIES = ("glean-version=latest; ph_phc_TXdpocbGVeZVm5VJmAsHTMrCofBQu3e0kN8HGMNGTVW_posthog=%7B%22distinct_id%22%3A%2201987aa7-03e5-7766-a9f8-c1fda9833689%22%2C%22%24sesid%22%3A%5B1754404968813%2C%2201987aa7-03e5-7766-a9f8-c1fbd747a398%22%2C1754404422629%5D%7D; okta-saml-hosted-login-session-store=MTc1NDc2MzI5N3wxeXdKYXptWnptcGdiYXJCbWNrVWlwX3ZQZUc3cnlER2NwVkhxU1dwbjE1Y2dtd3FQbTlBbExmR1VnUGZYaGkwalYwNURkcUZxOVF6ZFpqeTNwQXljbUpZZlk2anRBenNqbi1GeHlGX09kUWI2bFNqTFdTZ3hwMk5obU5YeGpTMDJwbWFma0xvX3pVajN5Z0FWNVg2bDkyVV9LQTZueTV6WnF3azFZeHdXNG9iVURGYnlpZmowZU1SRDdEM3R4aS1SSk80S0gtZllYWVJTRjZvNW1YNzBfdDVQSG80R1hfejNHUjlKZF9JX2tRNTBDbklJRFVvZnlCX29NbzZzYjd5c2Y2U2dzdEJPTnliNkJ2Q09LYnY2cnNER3BFVm1uQmxTYk43amU4Q0Z4SDd1bmhJQmN6Z1ZKTUlpNDAzUXpfT0VHSE1teVVLcHFYcE8tNFo4bWVRRHhBM2ExMXZGMXlaN2VESVJsMnQ0TTBxd1RqdGk1ZndMQlEtNHJuTnFseFJFUWFsWWlhZ0ppRkpwSzRUbG5TOEJDM3RFbVdoRjEzSmxyMW0tQ05LNEtvd0x2b1UxcmRKYktyN2FZNG1oN0wtZDdyeWZLUGJ0Vk55X2FIWVlPbWstdnNuVVk0bU5nPT18SB0xhwngABThS0c82b6G-DUS_2hFihexit9hrcmEeKg=; GCLB=CJWLrp2ZkbrAUBAD")
QUERY = "lighthouse-web"

async def run():
    client = GleanClient(base_url=BASE_URL, cookies=COOKIES)
    try:
        results = await client.search(QUERY, page_size=5)
    except CookieExpiredError as e:
        print(json.dumps({"success": False, "reason": "cookie_expired", "error": str(e)}))
        return
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"success": False, "reason": "error", "error": str(e)}))
        return
    docs = results.get("results") or []
    titles = []
    for item in docs:
        title = item.get("title") or item.get("result", {}).get("title") if isinstance(item, dict) else None
        if title:
            titles.append(title)
    print(json.dumps({
        "success": True,
        "count": len(docs),
        "titles": titles[:5]
    }, ensure_ascii=False))
    await client.close()

if __name__ == "__main__":
    asyncio.run(run())
