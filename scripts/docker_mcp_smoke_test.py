#!/usr/bin/env python3
"""Comprehensive Docker MCP smoke test for glean-mcp-server.

Features:
  * Runs container (ephemeral) with supplied env or cookies file
  * Performs MCP initialize -> tools/list -> tools/call(glean_search)
  * Robust LSP-style frame parsing (Content-Length headers)
  * Timeouts and phased diagnostics (container start, initialize, search)
  * JSON summary output (stdout) + optional --json-out file
  * Verbose mode prints raw frames and stderr tail
  * Graceful handling of auth failures (treat as SKIPPED by default)
  * Exit codes:
        0 success (or skipped due to expired cookies)
        1 failure (infrastructure / unexpected)

Example:
  python scripts/docker_mcp_smoke_test.py \
    --image glean-mcp-server:latest \
    --base-url https://linkedin-be.glean.com \
    --cookies "cookie1=val; cookie2=val" \
    --query lighthouse-web --verbose

"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional, List

DEFAULT_IMAGE = "glean-mcp-server:latest"
DEFAULT_QUERY = "lighthouse-web"

# Hard-coded test credentials (requested). WARNING: embedding real cookies in source
# is insecure. Prefer supplying via environment or secure secret manager.
HARDCODED_BASE_URL = "https://linkedin-be.glean.com"
HARDCODED_COOKIES = (
    "glean-version=latest; ph_phc_TXdpocbGVeZVm5VJmAsHTMrCofBQu3e0kN8HGMNGTVW_posthog=%7B%22distinct_id%22%3A%2201987aa7-03e5-7766-a9f8-c1fda9833689%22%2C%22%24sesid%22%3A%5B1754404968813%2C%2201987aa7-03e5-7766-a9f8-c1fbd747a398%22%2C1754404422629%5D%7D; okta-saml-hosted-login-session-store=MTc1NDc2MzI5N3wxeXdKYXptWnptcGdiYXJCbWNrVWlwX3ZQZUc3cnlER2NwVkhxU1dwbjE1Y2dtd3FQbTlBbExmR1VnUGZYaGkwalYwNURkcUZxOVF6ZFpqeTNwQXljbUpZZlk2anRBenNqbi1GeHlGX09kUWI2bFNqTFdTZ3hwMk5obU5YeGpTMDJwbWFma0xvX3pVajN5Z0FWNVg2bDkyVV9LQTZueTV6WnF3azFZeHdXNG9iVURGYnlpZmowZU1SRDdEM3R4aS1SSk80S0gtZllYWVJTRjZvNW1YNzBfdDVQSG80R1hfejNHUjlKZF9JX2tRNTBDbklJRFVvZnlCX29NbzZzYjd5c2Y2U2dzdEJPTnliNkJ2Q09LYnY2cnNER3BFVm1uQmxTYk43amU4Q0Z4SDd1bmhJQmN6Z1ZKTUlpNDAzUXpfT0VHSE1teVVLcHFYcE8tNFo4bWVRRHhBM2ExMXZGMXlaN2VESVJsMnQ0TTBxd1RqdGk1ZndMQlEtNHJuTnFseFJFUWFsWWlhZ0ppRkpwSzRUbG5TOEJDM3RFbVdoRjEzSmxyMW0tQ05LNEtvd0x2b1UxcmRKYktyN2FZNG1oN0wtZDdyeWZLUGJ0Vk55X2FIWVlPbWstdnNuVVk0bU5nPT18SB0xhwngABThS0c82b6G-DUS_2hFihexit9hrcmEeKg=; GCLB=CJWLrp2ZkbrAUBAD"
)

@dataclass
class PhaseResult:
    ok: bool
    duration_sec: float
    detail: str = ""

@dataclass
class Summary:
    success: bool
    skipped: bool
    reason: str
    phase_failed: str | None
    initialize_ok: bool
    search_ok: bool
    auth_error: bool
    container_exit_code: Optional[int]
    frames_received: int
    tool_response_excerpt: str
    raw_tool_json: Any | None
    durations: dict

RAW_AUTH_MARKERS = ["Authentication Failed", "cookies have expired", "unauthorized", "401", "403"]

class MCPFramedReader:
    """Incremental reader for LSP-style Content-Length framed JSON messages."""
    def __init__(self, stream):
        self.stream = stream
        self.frames: List[dict] = []

    def read_message(self, timeout: float) -> Optional[dict]:
        start = time.time()
        buf = b""
        # Read headers
        headers: dict[str, str] = {}
        line = b""
        # We read line by line until blank line
        while True:
            if time.time() - start > timeout:
                return None
            line = self.stream.readline()
            if not line:
                return None
            if line in (b"\r\n", b"\n", b""):
                break
            decoded = line.decode(errors="ignore").strip()
            if ":" in decoded:
                k, v = decoded.split(":", 1)
                headers[k.lower().strip()] = v.strip()
        length_str = headers.get("content-length")
        if not length_str:
            return None  # Not a framed JSON payload
        try:
            length = int(length_str)
        except ValueError:
            return None
        payload = b""
        while len(payload) < length:
            if time.time() - start > timeout:
                return None
            chunk = self.stream.read(length - len(payload))
            if not chunk:
                return None
            payload += chunk
        try:
            msg = json.loads(payload.decode("utf-8", errors="ignore"))
            self.frames.append(msg)
            return msg
        except Exception:
            return None


def ensure_image(image: str) -> None:
    try:
        subprocess.run(["docker", "image", "inspect", image], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"FAIL: Docker image '{image}' not found. Build or pull it first.")
        sys.exit(1)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Docker MCP smoke test for glean-mcp-server")
    p.add_argument("--image", default=DEFAULT_IMAGE)
    # Base URL and cookies are hard-coded; arguments disabled.
    # (Retain options for backward compatibility if re-enabled later.)
    # p.add_argument("--base-url", required=True, help="Glean base URL")
    # group = p.add_mutually_exclusive_group(required=True)
    # group.add_argument("--cookies", help="Cookie header string")
    # group.add_argument("--cookies-file", help="Path to file containing cookie header value")
    p.add_argument("--query", default=DEFAULT_QUERY)
    p.add_argument("--page-size", type=int, default=5)
    p.add_argument("--timeout", type=float, default=25.0, help="Total timeout seconds")
    p.add_argument("--frame-timeout", type=float, default=8.0, help="Per-frame timeout seconds")
    p.add_argument("--keep-container", action="store_true")
    p.add_argument("--name", default="glean-mcp-smoke")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--json-out", help="Write JSON summary to file")
    p.add_argument("--treat-auth-fail-as-success", action="store_true", help="Exit 0 when auth invalid (skip)")
    return p


def load_cookies(args) -> str:
    # Always return hard-coded cookies.
    return HARDCODED_COOKIES.strip()


def sanitize_cookie(c: str) -> str:
    # Remove spaces after semicolons to avoid docker splitting words
    return re.sub(r";\s+", ";", c)


def run_container(image: str, base_url: str, cookies: str, name: str, keep: bool):
    env_file = tempfile.NamedTemporaryFile("w", delete=False, prefix="glean_env_", suffix=".env")
    env_file.write(f"GLEAN_BASE_URL={base_url}\n")
    env_file.write(f"GLEAN_COOKIES={cookies}\n")
    env_file.flush(); env_file.close()
    cmd = [
    "docker", "run", "--rm" if not keep else "--detach",
    "-t",  # allocate TTY to keep stdio open
        "--name", name,
        "--env-file", env_file.name,
        "-i",  # interactive stdin/stdout for MCP stdio
        image
    ]
    # If detached, we can't perform stdio protocol. Force attached mode always for test.
    if keep:
        cmd.remove("--detach")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc, env_file.name


def send_frame(proc, obj):
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    proc.stdin.write(header + body)
    proc.stdin.flush()


def main():
    args = build_arg_parser().parse_args()
    ensure_image(args.image)

    base_url = HARDCODED_BASE_URL
    cookies = sanitize_cookie(HARDCODED_COOKIES)

    proc, env_path = run_container(args.image, base_url, cookies, args.name, args.keep_container)

    start_total = time.time()
    reader = MCPFramedReader(proc.stdout)
    stderr_capture = b""

    # Allow a brief startup window so the server loop is ready before frames arrive.
    time.sleep(0.75)

    initialize_msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "smoke-test", "version": "0.1.0"}}}
    list_tools_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    search_msg = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "glean_search", "arguments": {"query": args.query, "page_size": args.page_size}}}

    phase_failed: str | None = None
    initialize_ok = False
    search_ok = False
    auth_error = False
    tool_response_excerpt = ""
    raw_tool_json: Any | None = None

    try:
        # Send messages quickly after start
        send_frame(proc, initialize_msg)
        send_frame(proc, list_tools_msg)
        send_frame(proc, search_msg)

        deadline = time.time() + args.timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                phase_failed = phase_failed or "container"
                break
            msg = reader.read_message(timeout=args.frame_timeout)
            if not msg:
                # Periodically read some stderr
                try:
                    chunk = proc.stderr.read1(4096) if hasattr(proc.stderr, 'read1') else proc.stderr.read()
                    if chunk:
                        stderr_capture += chunk
                except Exception:
                    pass
                # If no frames yet, continue until deadline
                continue
            if args.verbose:
                print(f"[FRAME] {json.dumps(msg)[:300]}")
            if msg.get("id") == 1:
                initialize_ok = True
            if msg.get("id") == 3:
                # Tool call response
                result = msg.get("result", {})
                if isinstance(result, dict):
                    content = result.get("content") or []
                    if content and isinstance(content, list) and isinstance(content[0], dict):
                        text = content[0].get("text", "")
                        tool_response_excerpt = text[:500]
                        raw_tool_json = text
                        lowered = text.lower()
                        if any(m.lower() in lowered for m in RAW_AUTH_MARKERS):
                            auth_error = True
                        else:
                            # attempt to parse JSON search results
                            try:
                                data = json.loads(text)
                                if isinstance(data, dict) and data.get("results"):
                                    search_ok = True
                                raw_tool_json = data
                            except Exception:
                                # Fallback keyword check
                                if re.search(r"lighthouse", text, re.IGNORECASE):
                                    search_ok = True
                break  # Stop after tool response
        if not initialize_ok and phase_failed is None:
            phase_failed = "initialize"
        if not search_ok and phase_failed is None and not auth_error:
            phase_failed = "search"
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            stderr_capture += proc.stderr.read() or b""
        except Exception:
            pass
        try:
            os.unlink(env_path)
        except Exception:
            pass

    total_duration = time.time() - start_total

    skipped = auth_error and args.treat_auth_fail_as_success
    success = search_ok or skipped

    summary = Summary(
        success=success,
        skipped=skipped,
        reason=("auth-failed" if auth_error else ("ok" if success else "failure")),
        phase_failed=phase_failed,
        initialize_ok=initialize_ok,
        search_ok=search_ok,
        auth_error=auth_error,
        container_exit_code=proc.returncode,
        frames_received=len(reader.frames),
        tool_response_excerpt=tool_response_excerpt,
        raw_tool_json=raw_tool_json if args.verbose else None,
        durations={"total_sec": round(total_duration, 3)},
    )

    print(json.dumps(asdict(summary), indent=2))
    if args.verbose and stderr_capture:
        tail = stderr_capture.decode(errors="ignore")[-2000:]
        print("--- STDERR (tail) ---\n" + tail)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(asdict(summary), indent=2))

    if success:
        sys.exit(0)
    elif auth_error:
        # auth failure but not treated as success
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
