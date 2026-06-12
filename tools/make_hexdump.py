#!/usr/bin/env python3
"""Regenerate hexdump.txt from chess.bin.

The dump is the authoritative listing for typing the machine code in by
hand (the historical loader.bas listing is stale). Addresses start at
$4082, where the REM content begins on the ZX81.
"""

import sys

ORG = 0x4082


def main():
    src, dest = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        data = f.read()

    lines = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        hexpart = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{ORG + offset:04x}  {hexpart:<47}  |{ascii_part}|")

    with open(dest, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {dest}: {len(data)} bytes from {src}")


if __name__ == "__main__":
    main()
