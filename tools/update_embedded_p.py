#!/usr/bin/env python3
"""Sync the base64 CHESS_P constant in play/index.html with chess.p.

The browser page embeds the whole .P tape image as a base64 string so it
works as a single static file. Nothing else keeps that copy in sync with
the assembled binary, so this runs as part of `make build` (rewrite) and
`make test` (--check: fail if the page embeds a stale binary).

Usage:
  python3 tools/update_embedded_p.py           # rewrite index.html in place
  python3 tools/update_embedded_p.py --check   # exit 1 if out of sync
"""

import base64
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFILE = os.path.join(ROOT, 'chess.p')
HTML = os.path.join(ROOT, 'play', 'index.html')

PATTERN = re.compile(r"(const CHESS_P = ')([^']*)(';)")


def main():
    check = '--check' in sys.argv[1:]

    with open(PFILE, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    with open(HTML, 'r') as f:
        html = f.read()

    m = PATTERN.search(html)
    if not m:
        print("ERROR: const CHESS_P = '...' not found in play/index.html")
        return 1

    if m.group(2) == b64:
        print("play/index.html embedded binary matches chess.p")
        return 0

    if check:
        print("FAIL: play/index.html embeds a stale binary - run 'make build'")
        return 1

    html = PATTERN.sub(lambda mm: mm.group(1) + b64 + mm.group(3), html, count=1)
    with open(HTML, 'w') as f:
        f.write(html)
    print(f"Updated CHESS_P in play/index.html ({len(b64)} base64 chars)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
