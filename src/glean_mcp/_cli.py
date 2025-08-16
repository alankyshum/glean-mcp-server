"""Console script entry point for the Glean MCP helper utilities.

This provides a thin CLI so users can run `python -m glean_mcp` or
`glean-mcp` after installation.
"""

from __future__ import annotations

import argparse

from .api import glean_search, glean_chat, glean_read_documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="glean-mcp", description="Glean MCP utilities"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Perform a search")
    p_search.add_argument("query")
    p_search.add_argument("--page-size", type=int, default=10)

    p_chat = sub.add_parser("chat", help="Send a chat style question")
    p_chat.add_argument("message")

    p_docs = sub.add_parser("read-docs", help="Read documents by id/url")
    p_docs.add_argument(
        "spec", nargs="+", help="Document specs like id=123 or url=https://..."
    )

    # No server subcommand exposed – distribution focuses on client helpers only.

    args = parser.parse_args(argv)

    if args.command == "search":
        print(glean_search(args.query, page_size=args.page_size))
        return 0
    if args.command == "chat":
        print(glean_chat(args.message))
        return 0
    if args.command == "read-docs":
        specs = []
        for raw in args.spec:
            if "=" not in raw:
                parser.error(f"Invalid spec '{raw}'. Expected key=value")
            k, v = raw.split("=", 1)
            if k not in {"id", "url"}:
                parser.error("Spec keys must be 'id' or 'url'")
            specs.append({k: v})
        print(glean_read_documents(specs))
        return 0
    parser.error("Unhandled command")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

__all__ = ["main"]
