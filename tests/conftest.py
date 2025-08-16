import asyncio
import os
import sys
from pathlib import Path
import pytest

# Make src importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from glean_mcp.cookie_client import GleanClient  # noqa: E402
from glean_mcp.token_client import TokenBasedGleanClient  # noqa: E402
from glean_mcp import test_support  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def load_env():
    # Mimic our scripts .env loader
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            os.environ[k] = v


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("GLEAN_BASE_URL")
    if not url:
        pytest.skip("GLEAN_BASE_URL not set")
    return url


def _sanitize(v: str | None) -> str | None:
    if not v:
        return None
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (
        v.startswith("'") and v.endswith("'")
    ):
        return v[1:-1]
    return v


@pytest.fixture(scope="session")
def token() -> str | None:
    return _sanitize(os.environ.get("GLEAN_API_TOKEN"))


@pytest.fixture(scope="session")
def cookies() -> str | None:
    return _sanitize(os.environ.get("GLEAN_COOKIES"))


@pytest.fixture(scope="session", autouse=True)
def verify_auth_before_all(load_env, base_url, token, cookies):
    # Run token and cookie checkers if envs exist
    # Token checker
    if token:
        ok, info = asyncio.run(test_support.check_token())
        if not ok:
            pytest.skip(f"Token invalid according to test_support.check_token: {info}")
    # Cookie checker
    if cookies:
        ok, info = asyncio.run(test_support.check_cookies())
        if not ok:
            pytest.skip(
                f"Cookies invalid according to test_support.check_cookies: {info}"
            )


@pytest.fixture(scope="function")
def clients(base_url, token, cookies):
    clis = []
    if token:
        clis.append(
            ("token", TokenBasedGleanClient(base_url=base_url, api_token=token))
        )
    if cookies:
        clis.append(("cookie", GleanClient(base_url=base_url, cookies=cookies)))
    if not clis:
        pytest.skip("No auth configured (token or cookies)")
    return clis
