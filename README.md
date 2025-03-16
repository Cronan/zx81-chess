```
 _____ _  _ ___  _      ___ _  _ ___ ___ ___
|_  / | \/ |__ \/ |    / __| || | __/ __/ __|
  / /\>  < / _/| |   | (__| __ | _|\__ \__ \
 /___/_/\_\/ __|_|    \___|_||_|___|___/___/

  "KING OF THE CASTLE"

  A complete chess game in 672 bytes of Z80 machine code
  Running in 1K of RAM on the Sinclair ZX81

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

## What Is This?

This is a chess game that runs on the **Sinclair ZX81** (or Timex Sinclair 1000) in just **1 kilobyte of RAM** - the standard, unexpanded machine with no RAM pack.

672 bytes of hand-crafted Z80A machine code. No BASIC interpreter overhead. No 16K RAM pack. Just raw metal.

The entire program - board state, display engine, player input, move validation, and a computer opponent with material-based evaluation - fits inside a single `REM` statement in a two-line BASIC program:

```
1 REM ... (672 bytes of machine code hiding in here)
2 RAND USR 16514
```

That's it. Two lines. One kilobyte. A game of chess.

---

## How to Play

### On a Real ZX81

1. Type in the BASIC loader from `src/loader.bas` (requires 16K RAM pack for the loader)
2. Run it to POKE the machine code into memory
3. `SAVE "CHESS"` to tape
4. Remove the 16K RAM pack (yes, really)
5. `LOAD "CHESS"` on the 1K machine
6. The game starts automatically

### On an Emulator (Recommended!)

See **[docs/EMULATOR.md](docs/EMULATOR.md)** for detailed instructions on running this with modern ZX81 emulators.

Quick start: use [EightyOne](https://sourceforge.net/projects/eightyone-sinclair-emulator/) (Windows) or [sz81](http://sz81.sourceforge.net/) (Linux/Mac).

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

---

## What's In This Repository

```
zx81-chess/
|
+-- README.md ............... You are here
|
+-- src/
|   +-- chess.asm ........... Z80 assembly source (fully commented)
|   +-- loader.bas .......... BASIC loader program listing
|
+-- docs/
|   +-- ANNOTATED.md ........ Deep walkthrough of every routine
|   +-- THE-CHALLENGE.md .... How to fit chess in 1024 bytes
|   +-- MY-STORY.md ......... A 14-year-old, a ZX81, and a dream
|   +-- ZX81-GUIDE.md ....... ZX81 technical reference & resources
|   +-- EMULATOR.md ......... Running this on modern hardware
|   +-- MEMORY-MAP.md ....... Complete memory layout
|
+-- hexdump.txt ............. Raw hex bytes for manual entry
```

---

## Technical Highlights

| Feature | Detail |
|---|---|
| **Target Machine** | Sinclair ZX81 / Timex Sinclair 1000 |
| **CPU** | Zilog Z80A @ 3.25 MHz |
| **RAM Required** | 1024 bytes (1K) - no expansion needed |
| **Code Size** | 672 bytes of Z80 machine code |
| **Language** | Z80A assembly, hand-assembled |
| **Board Storage** | 64 bytes inside the REM statement |
| **AI Depth** | 1-ply with material evaluation |
| **Display** | Direct display-file manipulation |
| **Input** | Algebraic notation (E2E4 style) |

### Tricks Used to Save Space

- **Board lives in the REM statement** - The 64-byte chess board is stored at the very start of the machine code area, inside the BASIC REM statement. This means the board data *is* the REM content. The ZX81 doesn't care what's in a REM - it skips right past it. But `USR 16514` jumps right into it as machine code. Dual-purpose memory!

- **Direction bitmask for sliding pieces** - Bishop, Rook, and Queen all use the same 8-direction loop. A bitmask ($A5 for Bishop, $5A for Rook, $FF for Queen) selects which directions are active. One loop, three piece types, massive byte savings.

- **No separate initialisation data** - The starting position is generated algorithmically rather than stored as a 64-byte lookup table. The back rank pattern `R N B Q K B N R` is stored once (8 bytes) and reused for both White and Black.

- **Pawn promotion in 12 bytes** - Just checks if a pawn reached the far rank, and replaces it with a Queen. No choice of piece - you get a Queen and you'll like it.

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
- Slight queenside bias (scans a-h, keeps first equally-scored move)
- No opening theory (improvises from move 1)
- Doesn't understand check (can move its King into danger)
- No castling, en passant, or promotion choice

---

## Historical Context

The ZX81 was released by Sinclair Research in March 1981. With its membrane keyboard, 1K of RAM, and a TV for a monitor, it brought computing to hundreds of thousands of people — from London to Durban — who could never have afforded a "real" computer.

The idea that you could fit a chess game into 1K of RAM was considered somewhere between ambitious and daft. The entire program — board state, display routines, input handling, and a computer opponent — has to coexist in 1024 bytes alongside the system variables and display file. There's no room for elegance. There's barely room for anything.

This particular version was originally written in 1983 by a fourteen-year-old in Durban, South Africa, hand-assembled with pencil and graph paper from Rodnay Zaks' *Programming the Z80* (Sybex, 624 pages of Z80 enlightenment). The code was typed into the machine one POKE command at a time over three evenings, and saved to a C15 cassette tape that eventually degraded beyond recovery.

This repository is a reconstruction from memory.

For context, this README file is about 8 kilobytes. The entire chess game would fit in the first few paragraphs.

See **[docs/MY-STORY.md](docs/MY-STORY.md)** for the full story.

---

## Building from Source

If you have a Z80 cross-assembler:

```bash
# Using z80asm
z80asm -o chess.bin src/chess.asm

# Using zmac
zmac src/chess.asm -o chess.bin

# Using pasmo
pasmo src/chess.asm chess.bin
```

Then convert to a ZX81 .P file using a tool like `bin2p` or `zx81-utils`.

Or just type in the hex dump. That's the authentic experience.

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

*672 bytes. Every one of them earned.*
