#!/usr/bin/env python3
"""Cross-emulator differential test.

Replays the scripted games from tests/games.json through BOTH emulators:

  - the Python Z80 harness (test_harness.py), which runs chess.bin
  - the JS Z80/ZX81 emulator (play/z80.js + play/zx81.js, the one the
    browser uses), driven by tools/diff_runner.js, which runs chess.p

and compares board state, the AI's chosen move (best_from/best_to) and
run status after startup and after every move. The two emulators have
silently diverged before (JR off-by-one, register mapping, rook mask);
this test makes any future divergence fail CI with a board diff.

FRAMES ($4034) is pinned to 0 in both emulators so the AI's tie-break
coin flip is deterministic and identical on both sides.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from test_harness import Z80, setup_zx81_memory, encode_key  # noqa: E402

BOARD = 0x4082
BEST_FROM = 0x40C5
BEST_TO = 0x40C6
FRAMES = 0x4034
ENTRY_POINT = 0x40EF


class Session:
    """One game session in the Python emulator."""

    def __init__(self, code):
        self.cpu = Z80()
        setup_zx81_memory(self.cpu)
        self.cpu.load_binary(code, BOARD)
        self.cpu.sp = 0x7FFF
        self.cpu.ww(FRAMES, 0)
        self.cpu.max_cycles = 5_000_000

    def _run(self, start_pc):
        self.cpu.cycles = 0  # per-move budget, not per-game
        status = self.cpu.run(start_pc, stop_on_halt_no_keys=True)
        return self._normalize(status)

    def _normalize(self, status):
        if self.kings_present() < 2:
            return "gameover"
        return "idle" if status == "halt_no_keys" else f"abnormal:{status}"

    def start(self):
        return self._run(ENTRY_POINT)

    def play(self, move):
        for ch in move:
            self.cpu.key_queue.append(encode_key(ch))
        return self._run(self.cpu.pc)

    def kings_present(self):
        return sum(
            1 for i in range(64) if self.cpu.rb(BOARD + i) & 0x07 == 6
        )

    def record(self, game, move, status):
        return {
            "game": game,
            "move": move,
            "board": "".join(f"{self.cpu.rb(BOARD + i):02x}" for i in range(64)),
            "bestFrom": self.cpu.rb(BEST_FROM),
            "bestTo": self.cpu.rb(BEST_TO),
            "status": status,
        }


def run_python_games(games, code):
    records = []
    for name, moves in games.items():
        session = Session(code)
        status = session.start()
        records.append(session.record(name, "start", status))
        for move in moves:
            if status == "gameover":
                break
            status = session.play(move)
            records.append(session.record(name, move, status))
    return records


def run_js_games():
    result = subprocess.run(
        ["node", os.path.join(ROOT, "tools", "diff_runner.js")],
        capture_output=True, text=True, check=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def board_to_string(board_hex):
    piece_chars = {0: ".", 1: "P", 2: "N", 3: "B", 4: "R", 5: "Q", 6: "K"}
    rows = []
    for rank in range(7, -1, -1):
        row = f"{rank + 1}|"
        for file in range(8):
            piece = int(board_hex[2 * (rank * 8 + file):][:2], 16)
            ch = piece_chars.get(piece & 0x07, "?")
            if piece & 0x08:
                ch = ch.lower()
            row += ch
        rows.append(row)
    rows.append("  abcdefgh")
    return "\n".join(rows)


def main():
    with open(os.path.join(ROOT, "tests", "games.json")) as f:
        games = json.load(f)["games"]
    with open(os.path.join(ROOT, "chess.bin"), "rb") as f:
        code = f.read()

    py_records = run_python_games(games, code)
    js_records = run_js_games()

    if len(py_records) != len(js_records):
        print(f"FAIL: Python produced {len(py_records)} positions, JS {len(js_records)}")
        return 1

    checked = 0
    for py, js in zip(py_records, js_records):
        if py != js:
            print(f"FAIL: divergence in game '{py['game']}' after move '{py['move']}'")
            for key in ("game", "move", "status", "bestFrom", "bestTo"):
                if py[key] != js[key]:
                    print(f"  {key}: python={py[key]!r} js={js[key]!r}")
            if py["board"] != js["board"]:
                print("  Python board:            JS board:")
                py_rows = board_to_string(py["board"]).splitlines()
                js_rows = board_to_string(js["board"]).splitlines()
                for a, b in zip(py_rows, js_rows):
                    marker = "   " if a == b else " * "
                    print(f"  {a}{marker}      {b}")
            return 1
        checked += 1

    print(f"PASS: Python and JS emulators agree on {checked} positions "
          f"across {len(games)} games")
    return 0


if __name__ == "__main__":
    sys.exit(main())
