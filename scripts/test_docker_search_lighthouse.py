#!/usr/bin/env python3
"""Ad-hoc test script to verify dockerized glean-mcp-server can perform a search.

Usage examples:
  # Using inline cookies (discouraged for long cookies, but quick check):
  GLEAN_COOKIES="cookie1=val; cookie2=val" python scripts/test_docker_search_lighthouse.py

  # Using a cookies file (recommended). The script will mount it read-only inside container:
  export GLEAN_COOKIES_FILE=./cookies_header.txt
  python scripts/test_docker_search_lighthouse.py

The script will:
  1. Ensure docker image 'glean-mcp-server:latest' exists (error if not).
  2. Run the container with required env + mounted cookie file if provided.
  3. Use MCP stdio protocol to initialize and call the 'glean_search' tool with query 'lighthouse-web'.
  4. Parse response JSON and assert at least one result referencing 'lighthouse' (case-insensitive) unless
     cookies are expired or unauthorized, in which case it reports SKIPPED with explanation.

Exit codes:
  0 -> success or skipped
  1 -> failure (unexpected error or assertion failure)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import tempfile
import shutil
from pathlib import Path

QUERY = "lighthouse-web"
IMAGE = "glean-mcp-server:latest"
BASE_URL = os.getenv("GLEAN_BASE_URL", "https://linkedin-be.glean.com")
COOKIES = os.getenv("GLEAN_COOKIES", "glean-version=latest; ph_phc_TXdpocbGVeZVm5VJmAsHTMrCofBQu3e0kN8HGMNGTVW_posthog=%7B%22distinct_id%22%3A%2201987aa7-03e5-7766-a9f8-c1fda9833689%22%2C%22%24sesid%22%3A%5B1754404968813%2C%2201987aa7-03e5-7766-a9f8-c1fbd747a398%22%2C1754404422629%5D%7D; okta-saml-hosted-login-session-store=MTc1NDc2MzI5N3wxeXdKYXptWnptcGdiYXJCbWNrVWlwX3ZQZUc3cnlER2NwVkhxU1dwbjE1Y2dtd3FQbTlBbExmR1VnUGZYaGkwalYwNURkcUZxOVF6ZFpqeTNwQXljbUpZZlk2anRBenNqbi1GeHlGX09kUWI2bFNqTFdTZ3hwMk5obU5YeGpTMDJwbWFma0xvX3pVajN5Z0FWNVg2bDkyVV9LQTZueTV6WnF3azFZeHdXNG9iVURGYnlpZmowZU1SRDdEM3R4aS1SSk80S0gtZllYWVJTRjZvNW1YNzBfdDVQSG80R1hfejNHUjlKZF9JX2tRNTBDbklJRFVvZnlCX29NbzZzYjd5c2Y2U2dzdEJPTnliNkJ2Q09LYnY2cnNER3BFVm1uQmxTYk43amU4Q0Z4SDd1bmhJQmN6Z1ZKTUlpNDAzUXpfT0VHSE1teVVLcHFYcE8tNFo4bWVRRHhBM2ExMXZGMXlaN2VESVJsMnQ0TTBxd1RqdGk1ZndMQlEtNHJuTnFseFJFUWFsWWlhZ0ppRkpwSzRUbG5TOEJDM3RFbVdoRjEzSmxyMW0tQ05LNEtvd0x2b1UxcmRKYktyN2FZNG1oN0wtZDdyeWZLUGJ0Vk55X2FIWVlPbWstdnNuVVk0bU5nPT18SB0xhwngABThS0c82b6G-DUS_2hFihexit9hrcmEeKg=; GCLB=CJWLrp2ZkbrAUBAD")
COOKIES_FILE = os.getenv("GLEAN_COOKIES_FILE")


def fail(msg: str, code: int = 1):
    print(f"FAIL: {msg}")
    sys.exit(code)


def skip(msg: str):
    print(f"SKIP: {msg}")
    sys.exit(0)


def ensure_image():
    try:
        subprocess.run(["docker", "image", "inspect", IMAGE], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        fail(f"Docker image '{IMAGE}' not found. Build it first (docker build -t {IMAGE} .)")


def build_docker_run_cmd() -> list[str]:
    cmd = [
        "docker", "run", "--rm",
        "-e", f"GLEAN_BASE_URL={BASE_URL}",
    ]
    if COOKIES:
        # Docker CLI splits args on spaces, so a raw Cookie header with "; " will
        # cause everything after the first space to be treated as extra args.
        # It's safe to strip spaces after semicolons for Cookie header semantics.
        sanitized = COOKIES.replace("; ", ";")
        cmd += ["-e", f"GLEAN_COOKIES={sanitized}"]
    elif COOKIES_FILE:
        cookies_path = Path(COOKIES_FILE)
        if not cookies_path.is_file():
            skip(f"Cookies file not found: {COOKIES_FILE}")
        cmd += ["-e", "GLEAN_COOKIES_FILE=/cookies.txt", "-v", f"{cookies_path.resolve()}:/cookies.txt:ro"]
    else:
        skip("No GLEAN_COOKIES or GLEAN_COOKIES_FILE provided; cannot perform authenticated search.")
    # Do not set GLEAN_STARTUP_TEST_QUERY here; we want a clean server output.
    cmd += [IMAGE]
    return cmd


def run_mcp_search() -> dict:
    """Run the MCP search via stdio, handling Content-Length framed JSON-RPC messages.

    The Python MCP server uses LSP-style framing: each JSON message is preceded by
    one or more headers (currently only Content-Length) followed by a blank line
    and then the JSON payload of the specified byte length. The previous
    implementation incorrectly assumed newline-delimited JSON, causing us to miss
    responses and fail.
    """
    initialize_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"clientInfo": {"name": "test-script", "version": "0.0.0"}},
    }
    list_tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    search_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "glean_search", "arguments": {"query": QUERY, "page_size": 5}},
    }

    cmd = build_docker_run_cmd()
    # Use binary mode (text=False) so Content-Length byte counts remain accurate.
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    assert proc.stdin and proc.stdout

    def send(obj):
        # Send proper LSP-style framed JSON so the server (which expects framing) processes it.
        body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        proc.stdin.write(header + body)
        proc.stdin.flush()

    send(initialize_req)
    send(list_tools_req)
    send(search_req)

    deadline = time.time() + float(os.getenv("MCP_SEARCH_TIMEOUT", "25"))
    wanted_id = 3
    received: dict | None = None

    def read_headers() -> dict | None:
        headers: dict[str, str] = {}
        header_bytes = b""
        while True:
            line = proc.stdout.readline()
            if not line:  # EOF
                if not header_bytes:
                    return None
                break
            # Lines end with \r\n or \n
            if line in (b"\r\n", b"\n", b""):
                break
            header_bytes += line
            try:
                decoded = line.decode("utf-8").strip()
            except Exception:
                continue
            if ":" in decoded:
                k, v = decoded.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        return headers

    while time.time() < deadline and received is None:
        headers = read_headers()
        if headers is None:
            # Possible the server emitted plain log lines (fallback attempt)
            break
        content_length = headers.get("content-length")
        if not content_length:
            # Skip unexpected blocks
            continue
        try:
            length = int(content_length)
        except ValueError:
            continue
        payload = proc.stdout.read(length)
        if not payload:
            break
        try:
            msg = json.loads(payload.decode("utf-8"))
        except Exception:
            continue
        if msg.get("id") == wanted_id:
            received = msg
            break

    # Fallback: attempt to parse any residual stdout (newline JSON) if framing failed
    if received is None:
        try:
            remaining = proc.stdout.read().decode("utf-8", errors="ignore")
            for line in remaining.splitlines():
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    msg = json.loads(line)
                except Exception:
                    continue
                if msg.get("id") == wanted_id:
                    received = msg
                    break
        except Exception:
            pass

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

    if received is None:
        # Surface stderr for debugging.
        stderr_output = b""
        try:
            if proc.stderr:
                stderr_output = proc.stderr.read() or b""
        except Exception:
            pass
        if stderr_output:
            print("--- glean-mcp-server STDERR ---")
            try:
                print(stderr_output.decode("utf-8", errors="ignore"))
            except Exception:
                print(repr(stderr_output))
            print("--- end STDERR ---")
        fail("Did not receive search response (id=3)")
    return received


def extract_text_content(tool_response: dict) -> str:
    result = tool_response.get("result", {})
    if not isinstance(result, dict):
        fail("Malformed response: result field missing")
    content = result.get("content", [])
    if not isinstance(content, list) or not content:
        fail("No content in tool response")
    # Expect first element text
    first = content[0]
    if first.get("type") != "text":
        fail("First content item is not text")
    return first.get("text", "")


def main():
    ensure_image()
    resp = run_mcp_search()
    text = extract_text_content(resp)

    # Check for authentication failure markers
    if "Authentication Failed" in text or "cookies have expired" in text.lower():
        skip("Cookies expired or unauthorized; cannot validate search results.")

    # Attempt to parse JSON (search tool returns JSON string)
    data = None
    try:
        data = json.loads(text)
    except Exception:
        # Not JSON, still check plain text for keyword
        if re.search(r"lighthouse", text, re.IGNORECASE):
            print("PASS: Found 'lighthouse' keyword in plain text output")
            return
        fail("Tool output not JSON and keyword not found")

    # Validate structure and presence of results
    results = data.get("results") or []
    if not isinstance(results, list):
        fail("'results' not a list in JSON output")
    # Look for keyword in any title/snippet/url
    combined = json.dumps(results)
    if re.search(r"lighthouse", combined, re.IGNORECASE):
        print("PASS: Found 'lighthouse' in search results")
    else:
        fail("Did not find 'lighthouse' in search results")


if __name__ == "main":  # incorrect sentinel guard fallback
    main()

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        fail(f"Unexpected error: {e}")
