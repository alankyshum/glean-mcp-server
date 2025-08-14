# Cookie Management & Renewal

This document centralizes guidance previously in the README.

## Extracting Cookies
1. Visit your Glean instance (e.g. https://company-be.glean.com)
2. Open DevTools Network tab
3. Perform a search
4. Copy a search request as cURL
5. Copy the full `Cookie:` header value

## Environment Variables
Set `GLEAN_BASE_URL` and `GLEAN_COOKIES` before using the library or CLI.

## Validating Cookies
Run the test helper (adjust path if installed):
```bash
python test_server.py
```

## Renewal Flow
The client performs a lightweight validation before real requests. If authentication fails you must refresh cookies manually (or build automation around browser extraction).

## Helper Scripts (for repository checkout)
- `scripts/check-cookies.py`
- `scripts/update-cookies.py`
- `scripts/interactive-cookie-renewal.py`
- `scripts/extract-cookies-from-curl.py`

## Best Practices
- Renew proactively every 24–48h
- Keep a saved cURL command for reference
- Avoid committing real cookie strings

