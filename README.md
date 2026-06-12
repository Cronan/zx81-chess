[![Build and Test](https://github.com/Cronan/zx81-chess/actions/workflows/ci.yml/badge.svg)](https://github.com/Cronan/zx81-chess/actions/workflows/ci.yml)

```
 _____ _  _ ___  _      ___ _  _ ___ ___ ___
|_  / | \/ |__ \/ |    / __| || | __/ __/ __|
  / /\>  < / _/| |   | (__| __ | _|\__ \__ \
 /___/_/\_\/ __|_|    \___|_||_|___|___/___/

  "KING OF THE CASTLE"

  A complete chess game in 918 bytes of Z80 machine code
  Born in 1K of RAM on the Sinclair ZX81

  +-+-+-+-+-+-+-+-+
 8|r|n|b|q|k|b|n|r|
  +-+-+-+-+-+-+-+-+
 7|p|p|p|p|p|p|p|p|
  +-+-+-+-+-+-+-+-+
 6|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 5|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 4|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 3|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 2|P|P|P|P|P|P|P|P|
  +-+-+-+-+-+-+-+-+
 1|R|N|B|Q|K|B|N|R|
  +-+-+-+-+-+-+-+-+
   A B C D E F G H
```

---

## Try It Now

### [▶ Play Online](https://cronan.github.io/zx81-chess/play/)

**Play directly in your browser** - no installation required! The JavaScript emulator runs real Z80 machine code.

Or use a dedicated emulator for the authentic experience:
- [EightyOne](https://sourceforge.net/projects/eightyone-sinclair-emulator/) (Windows)
- [sz81](http://sz81.sourceforge.net/) (Linux/Mac)
- [JtyOne Online](https://www.zx81stuff.org.uk/zx81/jtyone.html) (load `chess.p`; needs more than the 1K setting - see honesty note below)

---

## What Is This?

This is a chess game for the **Sinclair ZX81** (or Timex Sinclair 1000), written in the spirit of the unexpanded 1K machine.

918 bytes of hand-crafted Z80A machine code. No BASIC interpreter overhead. Just raw metal.

The entire program - board state, display engine, player input, move execution (including en passant!), and a computer opponent with material-based evaluation - fits inside a single `REM` statement in a two-line BASIC program:

```
1 REM ... (918 bytes of machine code hiding in here)
2 RAND USR 16514
```

That's it. Two lines. A game of chess.

**An honesty note about "1K":** the original 1983 version fitted in the unexpanded machine's 1024 bytes. This rewrite started there too, then gained features (win messages, centre-bonus evaluation, random tie-breaking, en passant) and outgrew the boundary. A deduplication pass has since clawed most of that back - the REM now ends at $4418, just 24 bytes past the 1K limit of $43FF - but the current build still needs a 2K+ (or emulated) machine. The build enforces a hard 984-byte ceiling, leaving 66 bytes of banked headroom for future features.

---

## Where the 918 Bytes Go

```
Component        Bytes   What it does
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Board Data         64    █████░░░░░░░░░░░░░░░░░░░░░░  The 8x8 board (1 byte/square)
Variables           7    █░░░░░░░░░░░░░░░░░░░░░░░░░░  EP square, move coords, best move
Lookup Tables      38    ███░░░░░░░░░░░░░░░░░░░░░░░░  Piece chars, values, directions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Board Init         59    ████░░░░░░░░░░░░░░░░░░░░░░░  Set up the starting position
Display            93    ██████░░░░░░░░░░░░░░░░░░░░░  Draw board to screen
Input              82    █████░░░░░░░░░░░░░░░░░░░░░░  Read player moves from keyboard
Move Logic         92    ██████░░░░░░░░░░░░░░░░░░░░░  Execute moves, en passant, promotion
AI Engine         380    ███████████████████████████  Generate moves, evaluate, choose
Game Loop & Msgs  103    ███████░░░░░░░░░░░░░░░░░░░░  Main loop, king check, win/lose
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL             918    Every byte accounted for
                         (ceiling: 984 - 66 bytes banked for features)
```

The AI alone - scanning pieces, generating legal moves, evaluating captures, picking the best - takes 41% of the entire program. Display and input together are another 19%. Everything else fights over what's left.

---

## How to Play

### Playing the Game

```
YOUR MOVE:
  Type the SOURCE square: file letter (A-H) then rank number (1-8)
  Type the DESTINATION:   file letter (A-H) then rank number (1-8)
  Example: E2E4 moves the King's pawn two squares forward

DISPLAY:
  White pieces: K Q R B N P  (normal video)
  Black pieces: K Q R B N P  (inverse video - white on black)
  Empty squares: .

THE COMPUTER:
  After your move, the computer "thinks" and plays Black.
  It's not Deep Blue, but it'll take your pieces if you
  leave them hanging!

GAME OVER:
  The game ends when a King is captured.
  "YOU WIN" or "I WIN" is displayed.
  Press BREAK (SHIFT+SPACE) to return to BASIC.
```

### On a Real ZX81

1. Type in the bytes from `hexdump.txt` with a POKE loop (the listing in
   `src/loader.bas` is historical and stale - don't type that one in)
2. `SAVE "CHESS"` to tape
3. `LOAD "CHESS"` on a ZX81 with a RAM pack (the current build has
   outgrown the unexpanded 1K machine - see the honesty note above)
4. The game starts automatically

See **[docs/EMULATOR.md](docs/EMULATOR.md)** for detailed emulator setup instructions.

---

## Technical Highlights

| Feature | Detail |
|---|---|
| **Target Machine** | Sinclair ZX81 / Timex Sinclair 1000 |
| **CPU** | Zilog Z80A @ 3.25 MHz |
| **RAM Required** | 2K+ (the rewrite outgrew its 1K origins - see honesty note above) |
| **Code Size** | 918 bytes of Z80 machine code (hard ceiling: 984) |
| **Language** | Z80A assembly, hand-assembled |
| **Board Storage** | 64 bytes inside the REM statement |
| **AI Depth** | 1-ply with material evaluation |
| **Display** | Direct display-file manipulation |
| **Input** | Algebraic notation (E2E4 style) |

### Tricks Used to Save Space

- **Board lives in the REM statement** - The 64-byte chess board is stored at the very start of the machine code area, inside the BASIC REM statement. This means the board data *is* the REM content. The ZX81 doesn't care what's in a REM - it skips right past it. But `USR 16514` jumps right into it as machine code. Dual-purpose memory!

- **Direction bitmask for sliding pieces** - Bishop, Rook, and Queen all use the same 8-direction loop. A bitmask ($A5 for Bishop, $5A for Rook, $FF for Queen) selects which directions are active. One loop, three piece types, massive byte savings.

- **No separate initialisation data** - The starting position is generated algorithmically rather than stored as a 64-byte lookup table. The back rank pattern `R N B Q K B N R` is stored once (8 bytes) and reused for both White and Black.

- **Pawn promotion in one path for both colours** - Just checks if a pawn reached the far rank, and crowns `5 OR side` - the Queen of whoever moved. No choice of piece - you get a Queen and you'll like it.

- **En passant paid for by deduplication** - The full en passant rule (set on double push, lasts one ply, removes the bypassed pawn, AI considers it) costs ~57 bytes. Those bytes were freed by deduplicating code paths: shared board-indexing helper, shared column-delta check, shared piece-value scoring, and one print routine for the header and footer file letters. The ep square itself reuses a byte that was reserved for a cursor feature that never happened.

- **King capture = checkmate** - Full check/checkmate detection would cost ~80 bytes we don't have. Instead, the game ends when someone captures the King. You can technically move into check (the computer won't stop you, but it *will* take your King).

---

## The Chess Engine

The computer plays a **1-ply search with material evaluation**:

1. Scans all 64 squares for its own (Black) pieces
2. Generates all legal-ish moves for each piece using direction tables
3. Scores each move: captures score the value of the captured piece
4. Picks the highest-scoring move
5. Plays it

It won't win any tournaments, but it will:
- Always capture undefended pieces
- Prefer capturing Queens over Pawns
- Make reasonable developing moves when no captures are available
- Occasionally surprise you with a decent combination

### Known Weaknesses

- No look-ahead (doesn't see traps or forks)
- No opening theory (improvises from move 1)
- Doesn't understand check (can move its King into danger)
- No castling or promotion choice (en passant, though? Got that.)

---

## What's In This Repository

```
zx81-chess/
│
├── README.md ............... You are here
├── LICENSE ................. MIT License
│
├── src/
│   ├── chess.asm ........... Z80 assembly source (fully commented)
│   └── loader.bas .......... Historical BASIC loader (stale - use hexdump.txt)
│
├── tests/
│   ├── test_chess.py ....... Comprehensive test suite (40 tests)
│   └── games.json .......... Scripted games for cross-emulator testing
│
├── play/
│   ├── index.html .......... Online emulator web interface
│   ├── z80.js .............. JavaScript Z80 CPU emulator
│   ├── zx81.js ............. ZX81 system emulation
│   ├── emu_test_lib.js ..... Shared Node helpers for driving the emulator
│   └── test_js_emulator.js . JS emulator regression tests
│
├── docs/
│   ├── ANNOTATED.md ........ Deep walkthrough of every routine
│   ├── THE-CHALLENGE.md .... How to fit chess in 1024 bytes
│   ├── MY-STORY.md ......... A 14-year-old, a ZX81, and a dream
│   ├── ZX81-GUIDE.md ....... ZX81 technical reference & resources
│   ├── EMULATOR.md ......... Running this on modern hardware
│   └── MEMORY-MAP.md ....... Complete memory layout
│
├── tools/
│   ├── make_p_file.py ...... Convert binary to ZX81 .P format
│   ├── make_hexdump.py ..... Regenerate hexdump.txt from the binary
│   ├── diff_runner.js ...... JS half of the cross-emulator tests
│   └── diff_test.py ........ Cross-emulator differential test driver
│
├── chess.bin ............... Assembled binary (918 bytes)
├── chess.p ................. Ready-to-load ZX81 tape file
└── hexdump.txt ............. Raw hex bytes for manual entry (auto-generated)
```

---

## Building & Testing

```bash
# Build from source (requires pasmo assembler)
make build

# Run the test suite
make test

# Or do both
make
```

The build fails if the binary exceeds its 984-byte ceiling, so the size
constraint is enforced by CI rather than by vigilance.

The test suite includes **40 unit tests** covering:
- Board initialization and piece placement
- All piece movement patterns (knight L-shapes, bishop diagonals, etc.)
- Capture logic and priority (prefers high-value targets)
- Edge cases (board boundaries, blocking, pawn promotion)
- En passant (player capture, AI capture, one-ply expiry)
- Game-over detection

Tests run against actual Z80 machine code in the Python emulator. On top
of that, a **cross-emulator differential suite** replays scripted games
through both the Python harness and the JavaScript browser emulator and
compares board state, AI move choice, and en passant state after every
move - the two emulators have diverged subtly in the past, and now any
divergence fails CI with a board diff.

---

## Historical Context

The ZX81 was released by Sinclair Research in March 1981. With its membrane keyboard, 1K of RAM, and a TV for a monitor, it brought computing to hundreds of thousands of people — from London to Durban — who could never have afforded a "real" computer.

The idea that you could fit a chess game into 1K of RAM was considered somewhere between ambitious and daft. The entire program — board state, display routines, input handling, and a computer opponent — has to coexist in 1024 bytes alongside the system variables and display file. There's no room for elegance. There's barely room for anything.

The original version of this game was written over the course of 1982-83 by a kid in Durban, South Africa, who'd taught himself Z80 machine code from Rodnay Zaks' *Programming the Z80* (Sybex, 624 pages). He was twelve when he started, fourteen when he got it working. The code was hand-assembled with pencil and graph paper, typed into the machine one POKE command at a time, and saved to a C15 cassette tape that eventually degraded beyond recovery.

**This repository is not that original code.** That code is lost. This is a complete rewrite, done as an adult, in the spirit of that kid. The constraints are real — 1K, Z80A, every byte earned — but the implementation benefits from decades of hindsight. See [docs/MY-STORY.md](docs/MY-STORY.md) for the honest version.

For context, this README file is about 9 kilobytes. The entire chess game would fit in the first few paragraphs.

---

## Further Reading

- **[docs/ANNOTATED.md](docs/ANNOTATED.md)** - Line-by-line walkthrough of the code
- **[docs/THE-CHALLENGE.md](docs/THE-CHALLENGE.md)** - Design decisions and trade-offs
- **[docs/MY-STORY.md](docs/MY-STORY.md)** - The personal story behind this program
- **[docs/ZX81-GUIDE.md](docs/ZX81-GUIDE.md)** - ZX81 technical reference and links
- **[docs/EMULATOR.md](docs/EMULATOR.md)** - Running on modern hardware
- **[docs/MEMORY-MAP.md](docs/MEMORY-MAP.md)** - Where every byte lives

---

```
 _________________________________
|                                 |
|   S I N C L A I R  Z X 8 1     |
|                                 |
|  1K RAM      Z80A @ 3.25 MHz   |
|_________________________________|
|                                 |
| 1 2 3 4 5 6 7 8 9 0            |
|  Q W E R T Y U I O P           |
|   A S D F G H J K L  NEWLINE   |
|  SHIFT Z X C V B N M . SPACE   |
|_________________________________|
```

*918 bytes. Every one of them earned.*

---

## License

MIT License - see [LICENSE](LICENSE) for details.
