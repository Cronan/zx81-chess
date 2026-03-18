# ZX81 1K Chess — King of the Castle

Complete chess game in 672 bytes of Z80 machine code, running on a Sinclair ZX81 with 1K RAM. Playable online at https://cronan.github.io/zx81-chess/play/.

## Build and test

Requires `pasmo` (Z80 assembler), Python 3, and Node.js.

```bash
make              # build + test
make build        # assemble chess.asm → chess.bin → chess.p
make test         # python3 test_harness.py && python3 tests/test_chess.py
make clean        # remove built artefacts
```

CI runs on every push via GitHub Actions (`.github/workflows/ci.yml`).

## Repository structure

```
src/chess.asm           # Z80 assembly source (the game)
src/loader.bas          # BASIC loader for manual entry on real hardware
test_harness.py         # Python Z80 emulator + test runner
tests/test_chess.py     # 16 unit tests (board init, pieces, captures, promotion)
play/index.html         # Browser UI with touch keyboard
play/z80.js             # JavaScript Z80 CPU emulator
play/zx81.js            # JavaScript ZX81 system emulation (keyboard, display)
tools/make_p_file.py    # Binary to ZX81 .P tape format converter
docs/                   # Deep-dive documentation (annotated source, memory map, etc.)
```

## Architecture

**Z80 assembly** (`src/chess.asm`): the actual game. 64-byte board lives inside a BASIC REM statement at $4082. Piece encoding: bits 0-2 = type (0=empty, 1=pawn ... 6=king), bit 3 = colour. AI is 1-ply material evaluation scanning all legal moves.

**Python test harness** (`test_harness.py`): minimal Z80 emulator (~72 instructions) that loads chess.bin and intercepts RST $10 for display, HALT for keyboard input. Used by both the sanity test and the unit test suite.

**JavaScript emulator** (`play/`): separate Z80 + ZX81 emulation for browser play. Has had subtle bugs (JR off-by-one, stack collision, register mapping) so treat with care and test thoroughly.

## Key memory layout

| Address | Content |
|---|---|
| $4082-$40C1 | Board (64 bytes, inside REM) |
| $40C2-$40C8 | Working variables (cursor, move_from/to, best_from/to, best_score, side) |
| $40C9-$40EE | Lookup tables (piece chars, values, directions, init rank) |
| $40EF-$4325 | Machine code (all routines) |
| $4355-$43FF | Stack (grows downward) |

## Conventions

- Z80 assembly changes must fit within 1024 bytes total. Every byte matters. Run `make build` to verify size.
- When fixing JS emulator bugs, add a regression test. Recent history shows recurring issues with instruction accuracy.
- Test both Python harness and JS emulator; they can diverge.
- Documentation in `docs/` is extensive. Read `docs/ANNOTATED.md` before modifying chess.asm.

## Known limitations (intentional)

No castling, en passant, check/checkmate detection, stalemate, or multi-ply search. These are deliberate trade-offs for the 1K constraint, not bugs.

## Git

- Default branch: `main`.
- All commits authored by Ivan Cronyn, not Claude.
