#!/usr/bin/env python3
"""Query the digitized Kent repertory as JSON using Python's standard library.

Examples:
  python query.py stats
  python query.py sections
  python query.py search "fear night"
  python query.py search "anxiety" --scope pages
  python query.py children --section 1
  python query.py children --parent 123
  python query.py node 123
  python query.py remedy "acon" --exact
  python query.py page 40
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from viewer import DEFAULT_DB, Repertory


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--compact", action="store_true", help="Emit one compact JSON value.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stats", help="Counts, provenance, and metadata")
    commands.add_parser("sections", help="List repertory sections")
    search = commands.add_parser("search", help="Search words across rubric paths/text or full pages")
    search.add_argument("query")
    search.add_argument("--scope", choices=("rubrics", "pages"), default="rubrics")
    search.add_argument("--section", type=int)
    children = commands.add_parser("children", help="List direct child rubrics in book order")
    selection = children.add_mutually_exclusive_group(required=True)
    selection.add_argument("--section", type=int)
    selection.add_argument("--parent", type=int)
    node = commands.add_parser("node", help="Full rubric, remedies, children, ancestors, and provenance")
    node.add_argument("id", type=int)
    remedy = commands.add_parser("remedy", help="Find occurrences by abbreviation, name, or raw token")
    remedy.add_argument("query")
    remedy.add_argument("--exact", action="store_true")
    page = commands.add_parser("page", help="Full page transcription and rubric links")
    page.add_argument("number", type=int)
    for command in (search, children, remedy):
        command.add_argument("--limit", type=int, default=40)
        command.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    repertory = Repertory(args.database)
    try:
        if args.command == "stats":
            result = repertory.stats()
        elif args.command == "sections":
            result = repertory.sections()
        elif args.command == "search":
            result = repertory.search(args.query, scope=args.scope, section=args.section, limit=args.limit, offset=args.offset)
        elif args.command == "children":
            result = repertory.children(section=args.section, parent=args.parent, limit=args.limit, offset=args.offset)
        elif args.command == "node":
            result = repertory.node(args.id)
        elif args.command == "remedy":
            result = repertory.remedy(args.query, exact=args.exact, limit=args.limit, offset=args.offset)
        elif args.command == "page":
            result = repertory.page(args.number)
    except Exception as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
