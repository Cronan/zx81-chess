```
 _____ _  _ ___    ___ _  _   _   _    _    ___ _  _  ___ ___
|_   _| || | __|  / __| || | /_\ | |  | |  | __| \| |/ __| __|
  | | | __ | _|  | (__| __ |/ _ \| |__| |__| _|| .` | (_ | _|
  |_| |_||_|___|  \___|_||_/_/ \_\____|____|___|_|\_|\___|___|
```

# The 1K Challenge: Fitting Chess into 1024 Bytes

---

## The Problem

Chess is a complex game. A full implementation typically needs:

| Component | Typical Size | Our Budget |
|---|---|---|
| Board representation | 64-128 bytes | 64 bytes |
| Piece move tables | 100-200 bytes | 16 bytes |
| Move generation | 500-2000 bytes | ~250 bytes |
| Move validation | 300-800 bytes | ~30 bytes |
| Evaluation function | 200-1000 bytes | ~40 bytes |
| Search algorithm | 300-2000 bytes | 0 bytes (1-ply) |
| Display/UI | 200-500 bytes | ~85 bytes |
| Input handling | 100-300 bytes | ~90 bytes |
| Opening book | 500-50000 bytes | 0 bytes |
| Endgame tables | 1000-1000000 bytes | 0 bytes |
| **Total (typical)** | **3000-60000+ bytes** | **672 bytes** |

We have 672 bytes. That's about 2% of a minimal chess implementation.

Something has to give. A lot of somethings, actually.

---

## The Memory Budget

The ZX81 with 1K RAM has exactly 1024 bytes from address $4000 to $43FF.

Here's how every single byte is allocated:

```
$4000 +---------------------------+
      | System Variables          |  125 bytes
      | (ERR_NR, FLAGS, D_FILE,  |  These are non-negotiable.
      | VARS, FRAMES, etc.)      |  The ZX81 OS needs them.
$407D +---------------------------+
      | BASIC Line 1 Header      |  5 bytes
      | (line num, length, REM)  |  The wrapper for our code.
$4082 +---------------------------+
      | BOARD DATA               |  64 bytes
      | (inside the REM content) |  Dual-purpose: it's both a
      |                          |  BASIC comment and our data!
$40C2 +---------------------------+
      | Variables (7 bytes)      |  cursor, move_from, move_to,
      |                          |  best_from, best_to, best_score,
      |                          |  side
$40C9 +---------------------------+
      | Lookup Tables            |  38 bytes
      | (piece chars, values,    |  Compressed to the minimum.
      | directions, init data)   |
$40EF +---------------------------+
      | MACHINE CODE             |  ~563 bytes
      | (the actual program)     |  Display, input, AI, the lot.
      |                          |
      |                          |
      |                          |
$4329 +---------------------------+
      | NEWLINE (end of REM)     |  1 byte ($76)
$432A +---------------------------+
      | BASIC Line 2             |  ~18 bytes
      | "RAND USR 16514"         |  The launch command.
$433C +---------------------------+
      | Display File             |  ~25 bytes (collapsed)
      | (NEWLINE characters)     |  Expands when board is drawn.
$4355 +---------------------------+
      | Stack Space              |  ~170 bytes
      | (grows downward from     |  For CALL/RET and PUSH/POP.
      |  $43FF)                  |  We need at least ~20 bytes.
$43FF +---------------------------+
```

Total: 125 + 5 + 672 + 1 + 18 + 25 + 170 = 1016 bytes. We have 8 bytes to spare. Eight.

---

## Design Decisions: What We Kept

### 1. A Full 8x8 Board

Some 1K games use a reduced board (6x6 chess, for instance). I wanted real chess on a real board. The 8x8 board costs 64 bytes, which is painful, but it's non-negotiable.

The board uses one byte per square with a simple encoding:
- Bits 0-2: piece type (0=empty, 1=Pawn, 2=Knight, 3=Bishop, 4=Rook, 5=Queen, 6=King)
- Bit 3: colour (0=White, 1=Black)

This gives piece codes $00-$06 for White and $08-$0E for Black. Testing colour is a single `BIT 3, A` instruction - very Z80-efficient.

### 2. All Six Piece Types

Every piece moves correctly. Pawns push forward, Knights jump in L-shapes, Bishops slide diagonally, Rooks slide in straight lines, Queens do both, and Kings move one step in any direction. No shortcuts, no simplified pieces.

### 3. A Computer Opponent

The computer plays Black. It evaluates every legal move, scores them by capture value, and picks the best one. This is the core of the program and where most of the bytes went.

### 4. Pawn Promotion

When a pawn reaches the far rank, it becomes a Queen. Automatically, no choice - but at least it promotes.

### 5. A Readable Display

The board is displayed with file letters (A-H), rank numbers (1-8), and standard piece abbreviations. White pieces are normal video, Black pieces are inverse video. You can follow a game without any ambiguity.

---

## Design Decisions: What We Cut

### 1. Castling (~40 bytes saved)

Castling requires:
- Tracking whether King and Rooks have moved (3 bits per side = 1 byte)
- Checking that squares between King and Rook are empty
- Checking that King doesn't castle through check
- Moving two pieces in one turn

That's at least 40 bytes we can't afford. Sorry, King. You walk everywhere.

### 2. En Passant (~30 bytes saved)

En passant requires:
- Tracking whether the last move was a double pawn push (1 byte + logic)
- Special capture logic for pawns

30 bytes. No thanks. Pawns capture normally or not at all.

### 3. Check and Checkmate Detection (~80 bytes saved)

This is the big one. Properly detecting check requires scanning all enemy pieces to see if any attack the King. Detecting checkmate requires verifying that no legal move can get out of check. This is easily 80+ bytes.

Instead: the game ends when a King is captured. This means:
- You can move into check (the program won't stop you)
- The computer might move into check (rare but possible)
- "Checkmate" happens the move AFTER it should, when the King is actually taken

It's crude, but it works, and it saved enough bytes to have a computer opponent at all.

### 4. Move Legality Checking (~60 bytes saved)

For the human player, we only check:
- Source square contains a White piece
- Destination square isn't occupied by a White piece

That's it. You can move a Bishop in a straight line, slide a King across the board, or jump a Rook over pieces. The game trusts you to follow the rules.

For the computer, move generation is legal (within the bounds of our other limitations), so its moves are always valid.

### 5. Stalemate Detection (~40 bytes saved)

If a player has no legal moves but isn't in check, it's stalemate - a draw. We don't detect this. If the computer can't find any moves (extremely rare with our loose move generation), it just... doesn't move. The game continues with the next player's turn.

### 6. Draw Detection (~30 bytes saved)

No 50-move rule, no threefold repetition, no insufficient material detection. Games end by King capture or by the human pressing BREAK.

### 7. Opening Book (~0 bytes, would have cost 100+)

The computer has no opening knowledge. It plays by evaluation from move 1. Surprisingly, this often produces recognisable openings because the evaluation naturally leads to developing pieces and controlling the centre.

### 8. Multi-Ply Search (~100 bytes saved)

A 2-ply search (looking two moves ahead) would make the computer significantly stronger, but the minimax loop with alpha-beta pruning would cost at least 100 bytes. More importantly, on a 3.25 MHz Z80, a 2-ply search over all legal moves would take minutes per move.

One ply is instant (about 2 seconds) and fits in our budget.

---

## The Byte-Saving Tricks

### Trick 1: The REM Statement Hack

The genius of 1K ZX81 programming is the REM hack. The two-line BASIC program:

```
1 REM [672 bytes of machine code]
2 RAND USR 16514
```

Line 1 stores the machine code inside a BASIC comment. The BASIC interpreter sees REM and skips to the next line. But `RAND USR 16514` jumps to address 16514 ($4082), which is the first byte after the REM token - our machine code entry point.

The board data (64 bytes) is stored at the very start of the REM content. When the program initialises, it writes piece codes into these bytes. To the ZX81's BASIC interpreter, the board looks like random garbage after a REM. To the Z80, it's a data structure.

### Trick 2: Signed Arithmetic with Unsigned Instructions

The Z80 ADD instruction doesn't care about signs - it just adds binary values. A direction offset of -8 (going south on the board) is stored as $F8 (248 in unsigned). When added to a square index with `ADD A, $F8`, the carry flag tells us if we went below zero (off the bottom of the board). For going above 63, we just check `CP 64`.

This means we don't need separate signed comparison routines. The unsigned `CP` instruction handles all our boundary checking.

### Trick 3: The Direction Bitmask

Bishop, Rook, and Queen all move in straight lines. The directions are:

```
Index:  0    1    2    3    4    5    6    7
Dir:    SW   S    SE   W    E    NW   N    NE
Offset: -9   -8   -7   -1   +1   +7   +8   +9
```

Bishop uses directions 0, 2, 5, 7 (diagonals). Rook uses 1, 3, 4, 6 (orthogonals). Queen uses all 8.

Instead of three separate move generation routines, we have one loop that iterates through all 8 directions, controlled by a bitmask:

```
Bishop: $A5 = 10100101  (bits 0, 2, 5, 7)
Rook:   $5A = 01011010  (bits 1, 3, 4, 6)
Queen:  $FF = 11111111  (all bits)
```

One bit per direction, one shift per iteration, one routine for three piece types. This saved about 30 bytes compared to having separate routines.

### Trick 4: Algorithmic Board Setup

The starting position has a lot of regularity:
- Rank 1 and Rank 8 have the same piece pattern (RNBQKBNR), just different colours
- Ranks 2 and 7 are all pawns
- Ranks 3-6 are empty

Instead of storing the full 64-byte initial position as data (64 bytes), we store just the 8-byte back rank pattern and generate the rest:

```asm
; Store white back rank (8 bytes data, ~16 bytes code)
; Store white pawns (0 bytes data, ~8 bytes code)
; Black pawns (0 bytes data, ~8 bytes code)
; Store black back rank (reuse same 8 bytes, ~16 bytes code)
; Clear empty squares (~8 bytes code)
```

Total: 8 bytes data + ~56 bytes code = 64 bytes. Same cost as raw data, but the code also handles the clearing, which we'd need anyway.

### Trick 5: The HALT Keyboard Loop

The ZX81's HALT instruction is extraordinary. It doesn't just pause the CPU - it tells the ULA (display chip) to generate one TV frame. Without HALTs, the display goes blank. This is why 1K games sometimes have a flickering display - the program is too busy computing to execute HALTs.

Our keyboard routine uses HALT as a timer: wait for one frame (1/50th of a second), check the keyboard, repeat. This means the display stays rock-solid while waiting for input, and we get 50 keyboard polls per second for free.

```asm
wait_key:
    halt                    ; Generate TV frame AND wait 20ms
    ld a, ($4025)           ; Check if a key was pressed
    cp $ff                  ; No key = $FF
    jr z, wait_key          ; Keep waiting
```

Five instructions. Handles both display refresh and keyboard input. The Z80 is elegant when you work with it.

### Trick 6: Register Reuse

The Z80 has a limited set of registers: A, B, C, D, E, H, L (plus the shadow set, but let's not get into that). In a 672-byte program, every register is precious.

We systematically reuse registers for different purposes at different points in the code. The `E` register holds the current square number throughout the move generation phase. The `C` register holds the target square. The `D` register switches between piece type and direction offset.

This kind of register planning was done entirely on paper, tracking which registers were "live" at each point in the code. Modern compilers do this automatically. In 1983, I did it with coloured pencils and a lot of crossing out.

---

## The AI Design: Making 250 Bytes Think

The computer's "brain" is about 250 bytes. Here's how those bytes create something that feels like it's playing chess:

### Scanning

The computer iterates through all 64 squares. For each square containing a Black piece, it generates all possible moves for that piece.

### Move Generation

Each piece type has a different movement pattern:

**Pawn** (special case): Forward one square, forward two from starting rank, diagonal capture. Three possible moves, each with specific conditions. About 50 bytes.

**Knight**: Eight possible L-shaped moves. Check each one: is it on the board? Is the target square not blocked by own piece? About 30 bytes.

**King**: Same as Knight but with different direction offsets (all 8 adjacent squares). Shares the same code structure. About 25 bytes.

**Sliding pieces** (Bishop, Rook, Queen): For each active direction, slide one square at a time. If empty, record move and continue sliding. If enemy piece, record capture and stop. If own piece or board edge, stop. About 80 bytes for all three piece types (using the bitmask trick).

### Evaluation

Each move is scored:
- Capture of Pawn: 1 point
- Capture of Knight or Bishop: 3 points
- Capture of Rook: 5 points
- Capture of Queen: 9 points
- Capture of King: 50 points (game over!)
- Non-capture move: 1 point

The scores use standard chess piece values (Pawns=1, Knights=3, Bishops=3, Rooks=5, Queen=9). The King's value of 50 ensures the computer will always capture an exposed King over anything else.

### Selection

The computer keeps track of the best move found so far. Whenever a new move scores higher than the current best, it becomes the new best. Ties are broken by keeping the first one found (which means queenside pieces have a slight advantage, since we scan a-h).

This creates a simple but effective priority:
1. Take the most valuable piece available
2. If no captures, make a non-capture move (first one found)

### Why It Works (Mostly)

The computer doesn't plan ahead, but it plays by one solid principle: **always take free material**. In beginner-level chess, hanging pieces are common, and a computer that never misses a free piece is surprisingly tough to beat.

The computer will:
- Always capture an undefended piece
- Prefer capturing higher-value pieces
- Develop pieces naturally (because moving pieces that can reach more squares is more likely to find captures)
- Trade pieces when it's advantageous

The computer won't:
- Set up forks, pins, or skewers (no look-ahead)
- Avoid traps (it doesn't know what a trap is)
- Play strategically (no concept of pawn structure, king safety, or positional advantage)
- See anything more than one move ahead

---

## Comparison: Other 1K Chess Programs

### David Horne's 1K ZX Chess (1983)

The gold standard. Published in *Your Computer* magazine, this was 672 bytes and featured a cursor-based interface, all piece types, and a computer opponent. It's widely regarded as one of the most impressive feats of 1K programming ever achieved.

Horne was a professional programmer and his code was more polished than mine - better move generation, smoother display, fewer edge cases. But the overall approach was remarkably similar: REM statement hack, 1-ply evaluation, no castling or en passant.

### Other Notable 1K Programs

The ZX81 1K programming scene produced remarkable programs:
- **1K Breakout**: A fully playable Breakout clone in under 1K
- **1K Tetris** (later): Block-dropping game
- **Maze generators**: Recursive algorithms in minimal space
- **Music programs**: Using the ZX81's tape port for crude audio

The common thread: creative use of every byte, the REM statement hack, and the willingness to sacrifice "nice to have" features for core functionality.

---

## Could We Do Better?

With modern Z80 optimisation knowledge, yes. Some ideas for a hypothetical v2:

- **Board compression**: Store 2 pieces per byte (4 bits each) to halve the board to 32 bytes. Costs some code for packing/unpacking but might save net bytes.

- **Huffman-coded initial position**: Since most squares are empty, the starting position could be stored in about 20 bytes instead of being generated by code.

- **Combined move/eval loop**: Currently, move generation and evaluation are somewhat separate. Interleaving them could save a few bytes of loop overhead.

- **2-ply search**: By sacrificing some display quality (smaller board, fewer labels), we might squeeze in a 2-ply minimax. This would dramatically improve play quality.

But these are all "what ifs". In 1983, with a pencil and a book, 672 bytes of working chess was plenty good enough.

---

```
  Bytes remaining: 8
  Bytes used: 1016
  Total available: 1024

  "If I had more time, I would
   have written a shorter program."
       - Apologies to Blaise Pascal
```
