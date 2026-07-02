```
    _   _  _ _  _  ___ _____ _ _____ ___ ___
   /_\ | \| | \| |/ _ \_   _/_\_   _| __| \
  / _ \| .` | .` | (_) || |/ _ \| | | _|| |) |
 /_/ \_\_|\_|_|\_|\___/ |_/_/ \_\_| |___|___/

  C O D E   W A L K T H R O U G H
```

# Annotated Code Walkthrough

A deep, instruction-by-instruction guide to the ZX81 1K Chess machine code. Every trick explained, every byte justified.

---

## Preface: How to Read Z80 Assembly

If you've never read Z80 assembly before, here's a quick survival guide:

```
Registers:  A         - The accumulator (main working register)
            B, C      - General purpose (BC = 16-bit pair)
            D, E      - General purpose (DE = 16-bit pair)
            H, L      - General purpose (HL = 16-bit pair, often memory pointer)
            IX, IY    - Index registers (16-bit)
            SP        - Stack pointer
            PC        - Program counter (where we are in the code)
            F         - Flags (Z=zero, C=carry, N=subtract, etc.)

Key instructions:
  LD A, 42      - Load A with the value 42
  LD A, (HL)    - Load A from memory address pointed to by HL
  LD (HL), A    - Store A to memory address pointed to by HL
  ADD A, B      - A = A + B
  SUB 10        - A = A - 10
  AND $07       - A = A AND 00000111 (mask bits)
  OR $80        - A = A OR 10000000 (set bits)
  BIT 3, A      - Test bit 3 of A (sets Z flag)
  CP 64         - Compare A with 64 (sets flags, doesn't change A)
  JR Z, label   - Jump if zero flag set (relative jump, -128 to +127)
  JR NZ, label  - Jump if zero flag NOT set
  JR NC, label  - Jump if carry flag NOT set
  JR C, label   - Jump if carry flag set
  JP label      - Absolute jump (3 bytes vs 2 for JR)
  CALL label    - Call subroutine (pushes return address, jumps)
  RET           - Return from subroutine (pops return address)
  PUSH AF       - Push A and Flags onto stack
  POP AF        - Pop A and Flags from stack
  RST $10       - Special fast call to address $0010 (ZX81 print routine)
  HALT          - Stop CPU until next interrupt (= next TV frame on ZX81)
  DJNZ label    - Decrement B, jump if not zero (compact loop)
  XOR A         - A = A XOR A = 0 (1-byte way to zero A)
  INC HL        - HL = HL + 1
  DEC C         - C = C - 1
  NEG           - A = 0 - A (negate, two's complement)
  RLCA          - Rotate A left (multiply by 2)
  SRL D         - Shift D right logical (divide by 2)
```

**Addressing modes:**
- `LD A, 42` - Immediate: the value IS the number 42
- `LD A, (HL)` - Indirect: read from the memory address in HL
- `LD A, ($4025)` - Direct: read from a specific memory address
- `LD (IX+5), A` - Indexed: memory at (IX register + offset)

**Memory is little-endian:** the 16-bit value $4082 is stored as $82, $40 (low byte first).

---

## Part 1: Data Structures

### The Board (64 bytes at $4082)

```asm
board:      DEFS    64          ; $4082 - $40C1
```

This reserves 64 bytes inside the REM statement. Each byte represents one square:

```
Index:  0  1  2  3  4  5  6  7     <- Rank 1 (a1 to h1)
        8  9  10 11 12 13 14 15    <- Rank 2
        16 17 18 19 20 21 22 23    <- Rank 3
        24 25 26 27 28 29 30 31    <- Rank 4
        32 33 34 35 36 37 38 39    <- Rank 5
        40 41 42 43 44 45 46 47    <- Rank 6
        48 49 50 51 52 53 54 55    <- Rank 7
        56 57 58 59 60 61 62 63    <- Rank 8 (a8 to h8)
```

To get the row (rank) from an index: `row = index >> 3` (shift right 3 = divide by 8)
To get the column (file) from an index: `col = index AND 7` (mask lowest 3 bits)

Starting position:
```
Index 0-7:   04 02 03 05 06 03 02 04  (White: R N B Q K B N R)
Index 8-15:  01 01 01 01 01 01 01 01  (White pawns)
Index 16-47: 00 00 00 ... 00 00 00    (Empty)
Index 48-55: 09 09 09 09 09 09 09 09  (Black pawns)
Index 56-63: 0C 0A 0B 0D 0E 0B 0A 0C  (Black: R N B Q K B N R)
```

### Working Variables (7 bytes at $40C2)

```asm
ep_square:  DEFB    $FF         ; En passant target square ($FF = none)
move_from:  DEFB    0           ; Player's source square (0-63)
move_to:    DEFB    0           ; Player's destination square (0-63)
best_from:  DEFB    0           ; Computer's best move source
best_to:    DEFB    0           ; Computer's best move destination
best_score: DEFB    0           ; Computer's best score so far
side:       DEFB    0           ; Whose turn: 0=White, 8=Black
```

Seven bytes. That's all the working memory the program has (besides the stack and registers). Every variable is exactly one byte because we can't afford two-byte variables where one will do.

`ep_square` reuses the byte that was originally reserved for a cursor feature that never happened. It holds the square a double-pushed pawn skipped over - the square where it can be captured en passant - and is valid for exactly one ply (see do_move).

### Piece Characters Table (7 bytes)

```asm
piece_chars:
    DEFB    $00         ; Type 0: Empty -> Space
    DEFB    $35         ; Type 1: Pawn  -> "P" (ZX81 char code)
    DEFB    $33         ; Type 2: Knight -> "N"
    DEFB    $27         ; Type 3: Bishop -> "B"
    DEFB    $37         ; Type 4: Rook   -> "R"
    DEFB    $36         ; Type 5: Queen  -> "Q"
    DEFB    $30         ; Type 6: King   -> "K"
```

This table maps piece type (0-6) to the ZX81 character code for display. Note these are NOT ASCII codes - the ZX81 has its own character encoding. In ZX81 world, "A" is 38 ($26), not 65 ($41).

### Piece Values Table (7 bytes)

```asm
piece_vals:
    DEFB    0           ; Empty: 0 points
    DEFB    3           ; Pawn
    DEFB    8           ; Knight
    DEFB    8           ; Bishop
    DEFB    12          ; Rook
    DEFB    20          ; Queen
    DEFB    50          ; King (effectively "game over")
```

These keep the classic relative ordering but are scaled so the **smallest capture (a pawn, 3) beats the biggest non-capture score** (a quiet move's 1 plus the centre bonus's 1). With the classic 1/3/3/5/9 values, a quiet move to a centre file scored 2 while winning a free pawn scored 1, and the engine politely declined material. The King's 50 is still higher than anything else on offer, so capturing an exposed King always wins the auction.

### Direction Tables (16 bytes)

```asm
king_dirs:  DEFB    -9, -8, -7, -1, 1, 7, 8, 9
knight_dirs: DEFB   -17, -15, -10, -6, 6, 10, 15, 17
```

These encode movement offsets on the 8x8 board. Since the board is stored as a linear array, moving "north" one square means adding 8 to the index, moving "east" means adding 1, etc.

**King/Queen directions:**
```
  NW(+7) N(+8)  NE(+9)
  W(-1)  [SQ]   E(+1)
  SW(-9) S(-8)  SE(-7)
```

Note: these are stored as signed bytes. In the Z80's world, -9 is stored as $F7 (247 in unsigned). This works because the ADD instruction treats the bytes the same way regardless.

**Knight directions (L-shaped jumps):**
```
      +15  +17
  +6         +10
       [SQ]
  -10        -6
      -17  -15
```

For example, +17 means "two ranks north (+16) and one file east (+1)" = 16 + 1 = 17.

### Initial Rank Data (8 bytes)

```asm
init_rank:  DEFB    4, 2, 3, 5, 6, 3, 2, 4
```

The piece types for the back rank: Rook(4), Knight(2), Bishop(3), Queen(5), King(6), Bishop(3), Knight(2), Rook(4). Used for both White (rank 1) and Black (rank 8, with colour bit ORed in).

---

## Part 2: Initialisation

### init_board: Setting Up the Starting Position

```asm
init_board:
    ld      hl, board       ; HL points to start of board
    ld      b, 64           ; 64 squares to clear
    xor     a               ; A = 0
ib_clear:
    ld      (hl), a         ; Write 0 to current square
    inc     hl              ; Next square
    djnz    ib_clear        ; Repeat 64 times
```

**What's happening:** Fill all 64 board squares with 0 (empty). `DJNZ` is the Z80's "decrement B and jump if not zero" - a compact loop instruction. The entire 64-byte clear is just 7 bytes of code.

**Cycle count:** Each iteration is 7+6+4+13 = 30 T-states, x64 = 1920 T-states. At 3.25 MHz, that's about 0.6 milliseconds. Lightning fast.

```asm
    ; White back rank
    ld      hl, board       ; Reset to a1
    ld      de, init_rank   ; Point to RNBQKBNR data
    ld      b, 8
ib_wr:
    ld      a, (de)         ; Get piece type from table
    ld      (hl), a         ; Write to board
    inc     hl
    inc     de
    djnz    ib_wr           ; 8 pieces
```

**Note:** We use `LD A, (DE)` / `LD (HL), A` instead of the block move instruction `LDI` or `LDIR` because the loop with DJNZ is actually shorter for 8 bytes (LDIR requires setting BC which adds instructions).

```asm
    ; White pawns (rank 2)
    ld      b, 8
    ld      a, 1            ; White Pawn = $01
ib_wp:
    ld      (hl), a
    inc     hl
    djnz    ib_wp
```

HL is already pointing at a2 (index 8) because we just finished writing the back rank. No need to reload it - **sequential memory access saves bytes**.

```asm
    ; Black pawns (rank 7) - must set HL explicitly
    ld      hl, board + 48  ; a7 = index 48
    ld      b, 8
    ld      a, 9            ; Black Pawn = $01 OR $08 = $09
ib_bp:
    ld      (hl), a
    inc     hl
    djnz    ib_bp
```

We skip ranks 3-6 (they're already zero from the clear loop). HL jumps to rank 7 to place Black's pawns.

```asm
    ; Black back rank (rank 8)
    ld      de, init_rank   ; Same RNBQKBNR table!
    ld      b, 8
ib_br:
    ld      a, (de)
    or      8               ; Set bit 3 = Black
    ld      (hl), a
    inc     hl
    inc     de
    djnz    ib_br

    ; HL now points just past the board = ep_square
    ld      (hl), $FF       ; No en passant right
    ret
```

**The trick:** We reuse the same `init_rank` table for both White and Black. For Black pieces, we just OR the colour bit in: `or 8` sets bit 3, turning White Rook ($04) into Black Rook ($0C), etc. This saves 8 bytes of data.

**A second trick hides in the ending:** after the back-rank loop, HL has walked off the end of the board - which is exactly where `ep_square` lives ($40C2 = board + 64). So resetting the en passant state costs just 2 bytes (`LD (HL), $FF`) instead of the 5 a `LD A`/`LD (nn), A` pair would need.

---

## Part 3: Display

### cls_and_draw: Rendering the Board

```asm
cls_and_draw:
    call    ROM_CLS         ; Call ZX81 ROM routine to clear screen
```

The ZX81 ROM at address $0A2A clears the display file and resets the print position. We let the ROM do the heavy lifting - no point reimplementing CLS when there's a perfectly good one in ROM.

```asm
    ; Column header: "  A B C D E F G H"
    call    print_files     ; Shared with the footer (see below)
    ld      a, CH_NEWLINE
    rst     $10             ; End the line
```

The file-letters line appears twice on screen - above and below the board - so it's one subroutine:

```asm
print_files:
    ld      a, CH_SPACE
    rst     $10             ; Print space
    rst     $10             ; Print space (2 leading spaces for alignment)
    ld      b, 8
    ld      a, CH_A         ; ZX81 char code for "A"
pf_loop:
    push    af
    rst     $10             ; Print the letter
    ld      a, CH_SPACE
    rst     $10             ; Print space after it
    pop     af
    inc     a               ; Next letter (A->B->C...->H)
    djnz    pf_loop
    ret
```

The header CALLs it; the footer doesn't even pay for a CALL - `print_files` sits directly after the row loop, so the footer is reached by **falling through**, and `print_files`'s RET ends `cls_and_draw` too. (RST $10 prints via the DF_CC system variable, so no display-file pointer is needed in HL.)

`RST $10` is a **restart instruction** - a one-byte CALL to a fixed ROM address. RST $10 calls the ZX81's character print routine, which prints the character in the A register at the current print position and advances the cursor. It's the machine code equivalent of BASIC's `PRINT CHR$(A)`.

Using RST instead of CALL saves 2 bytes per invocation (1 byte vs 3 bytes). We call it dozens of times, so this adds up to significant savings.

```asm
    ; 8 rows of the board
    ld      c, 8            ; Row counter
    ld      ix, board + 56  ; Start at rank 8 (display top-down)
```

We use the IX index register to track our position in the board array. IX is a 16-bit register, so it can point anywhere in memory. We start at board + 56 (rank 8, which is displayed at the top of the screen) and work backwards.

```asm
row_loop:
    ; Print rank number ("8", "7", ... "1")
    ld      a, CH_0
    add     a, c            ; '0' + row number
    rst     $10
    ld      a, CH_SPACE
    rst     $10

    ; Print 8 squares
    ld      b, 8
    push    ix
    pop     de              ; DE = current position in board array

col_loop:
    ld      a, (de)         ; Read piece from board
    push    bc
    push    de
    call    get_piece_char  ; Convert to display character
    rst     $10             ; Print it
    ld      a, CH_SPACE
    rst     $10             ; Space between pieces
    pop     de
    pop     bc
    inc     de
    djnz    col_loop
```

**Register pressure:** We need B for the column counter (DJNZ), BC/DE for the inner loop, but PUSH/POP only works with register pairs. So we save BC and DE on the stack around the `call get_piece_char` which might trash them.

```asm
    ; Move to previous rank
    push    ix
    pop     hl
    ld      de, -8          ; Go back 8 squares (previous rank)
    add     hl, de
    push    hl
    pop     ix

    dec     c
    jr      nz, row_loop
```

After printing rank 8 (board indices 56-63), we need to print rank 7 (indices 48-55). IX = IX - 8 gets us there. The `PUSH IX / POP HL / ... / PUSH HL / POP IX` dance is needed because you can't do `ADD IX, DE` directly on the Z80 (there's no such instruction).

### get_piece_char: Piece to Character Conversion

```asm
get_piece_char:
    and     a               ; Test A against itself (sets Z if zero)
    jr      nz, gpc_piece
    ld      a, CH_DOT       ; Empty square -> "."
    ret

gpc_piece:
    push    af              ; Save original piece code
    and     $07             ; Mask to piece type (bits 0-2)
    ld      e, a            ; Index into lookup table
    ld      d, 0
    ld      hl, piece_chars
    add     hl, de          ; HL = address of character
    ld      a, (hl)         ; A = display character

    pop     de              ; Recover original piece code (into E)
    bit     3, e            ; Test colour bit
    ret     z               ; White -> return character as-is
    or      CH_INV          ; Black -> set bit 7 for inverse video
    ret
```

**The inverse video trick:** The ZX81 displays character codes 0-63 in normal video (black on white) and 128-191 in inverse video (white on black). To switch between them, you just set or clear bit 7. So `OR $80` turns normal "K" ($30) into inverse "K" ($B0). This is how we show Black pieces differently from White pieces without any graphics programming.

---

## Part 4: Player Input

### get_square: Reading a Square from the Keyboard

```asm
get_square:
    call    wait_key        ; Wait for file letter (A-H)
    sub     CH_A            ; Convert ZX81 char to 0-7
    and     $07             ; Safety mask (in case of wrong key)
    push    af              ; Save file number

    add     a, CH_A         ; Convert back for echo
    rst     $10             ; Echo the letter to screen

    call    wait_key        ; Wait for rank digit (1-8)
    sub     CH_1            ; Convert to 0-7
    and     $07             ; Safety mask
    push    af
    add     a, CH_1
    rst     $10             ; Echo the digit
    pop     af

    ; Calculate board index = rank * 8 + file
    rlca                    ; A = rank * 2
    rlca                    ; A = rank * 4
    rlca                    ; A = rank * 8
    pop     de              ; D = file number (PUSH AF puts A in the
                            ; high byte, which POP DE lands in D)
    add     a, d            ; A = rank * 8 + file
    ret
```

**RLCA is multiplication:** The Z80 has no multiply instruction. To multiply by 8, we rotate left 3 times. Each RLCA doubles the value:
- After 1st RLCA: rank * 2
- After 2nd RLCA: rank * 4
- After 3rd RLCA: rank * 8

This is a classic Z80 trick that every machine code programmer learns on day one.

### wait_key: The Keyboard Polling Loop

```asm
wait_key:
    halt                    ; Wait for next TV frame
    ld      a, ($4025)      ; Read LAST_K system variable
    cp      $FF             ; No key = $FF
    jr      z, wait_key     ; Loop if no key
    push    af
    ld      a, $FF
    ld      ($4025), a      ; Clear key buffer
    pop     af
    ret
```

**Why HALT is essential:** On the ZX81, the display is generated by software (the "slow mode" display routine). The HALT instruction triggers the NMI (Non-Maskable Interrupt) which runs the display routine. Without HALT, the screen goes blank.

By using HALT as our timing source, we get:
1. Display refresh (screen stays visible)
2. Keyboard scanning (the interrupt updates LAST_K)
3. A natural 20ms delay between polls (50 Hz TV frame rate)

Three functions for the price of one instruction. The ZX81's design was brilliant in its economy.

---

## Part 5: Move Execution

### do_move: Making a Move on the Board

```asm
do_move:
    ; Pick up piece from source
    ld      a, c            ; A = source square
    call    board_addr      ; HL -> source, A = piece being moved
    ld      (hl), 0         ; Clear source (piece picked up)

    ; Place on destination
    ld      e, b            ; E = destination square
    ld      d, 0
    ld      hl, board
    add     hl, de          ; HL = address of destination
    ld      (hl), a         ; Place piece (captures automatically!)
```

**Captures are free:** We don't need special capture code. Writing the moving piece to the destination square automatically overwrites whatever was there. If it was an enemy piece, it's now gone. If it was empty, no harm done.

(`board_addr` is the shared board-indexing helper - see Part 7.)

### Pawn Specials: En Passant and Promotion

After the move executes, pawns get special treatment. Everything below keys off one test:

```asm
    and     $07             ; Get piece type
    cp      1               ; Is it a pawn?
    jr      z, dm_pawn

    ; Non-pawn move: the en passant right expires
    ld      a, $FF
    ld      (ep_square), a
    ret
```

An en passant right lasts exactly one ply, so **every** move that isn't a double push must clear it - even a rook shuffle.

```asm
dm_pawn:
    ; En passant capture?
    ld      a, (ep_square)
    cp      b               ; Landed on the ep square?
    jr      nz, dm_rearm
    ld      a, c
    and     $38             ; Source rank...
    ld      d, a
    ld      a, b
    and     $07             ; ...destination file
    or      d
    push    hl
    call    board_addr
    ld      (hl), 0         ; Remove the captured pawn
    pop     hl
```

**The bypassed pawn's address:** it sits on the *source* rank (the capturing pawn moves diagonally off that rank) in the *destination* file. `(C AND $38) OR (B AND $07)` computes that square in one expression that works for both colours - no branching on side.

A pawn can only arrive on the ep square diagonally while the right is live: the square was vacated mid-double-push, and a straight push onto it is blocked by the double-pusher itself. So there's no occupancy test - if a pawn lands there, it's the en passant capture.

```asm
dm_rearm:
    ; The old right is spent; a double push grants a fresh one
    ld      a, $FF
    ld      (ep_square), a
    ld      a, c
    sub     b               ; from - to
    jr      nc, dm_abs
    neg                     ; Make positive
dm_abs:
    cp      16              ; Moved two ranks?
    jr      nz, dm_promo
    ld      a, c
    add     a, b            ; from + to < 128, so RRA
    rra                     ; halves it: the skipped square
    ld      (ep_square), a
    ret                     ; A double push can't promote
```

**The midpoint trick:** the skipped square is exactly halfway between source and destination. Their sum never exceeds 127, so the carry is clear and `RRA` is a one-byte divide-by-two.

```asm
dm_promo:
    ld      a, b            ; Check destination rank
    cp      56              ; Rank 8: White promotes
    jr      nc, dm_crown
    cp      8               ; Ranks 2-7: nothing to do
    ret     nc
dm_crown:
    ld      a, (side)
    or      5               ; Queen of the moving side
    ld      (hl), a
    ret
```

Promotion always crowns a Queen (no choice - correct ~99% of the time in real chess), and `5 OR side` produces the right colour for whoever moved: side=0 gives the White Queen ($05), side=8 the Black Queen ($0D). One code path, both colours.

---

## Part 6: The Computer AI

This is where it gets interesting. About 250 bytes to make the computer play chess.

### think: The Main AI Loop

```asm
think:
    xor     a
    ld      (best_score), a     ; Reset best score to 0
    ld      a, $FF
    ld      (best_from), a      ; $FF = no move found

    xor     a                   ; Start scanning from square 0
think_scan:
    push    af                  ; Save current square number

    ; Look up what's on this square
    call    board_addr          ; A = piece (shared helper, Part 7)

    and     a                   ; Empty?
    jr      z, think_next       ; Skip empty squares
    bit     3, a                ; Is it Black? (our colour)
    jr      z, think_next       ; Skip White pieces

    ; Found a Black piece - generate its moves
    and     $07                 ; Get piece type
    ld      d, a                ; D = piece type
    pop     af                  ; A = square number
    push    af                  ; Put it back (think_next pops it)
    ld      e, a                ; E = square number
    ld      a, d                ; A = piece type for the compares

    cp      1                   ; Pawn?
    jp      z, gen_pawn
    cp      2                   ; Knight?
    jp      z, gen_knight
    cp      6                   ; King?
    jp      z, gen_king
    jp      gen_slider          ; Must be Bishop, Rook, or Queen
```

**The scanning strategy:** We check every square on the board (0 to 63). For each Black piece found, we branch to the appropriate move generator. The piece type is in D, the square number is in E. These two values are maintained throughout the move generation for that piece.

**The $FF sentinel matters:** if the scan finds no move at all (a boxed-in lone king), `best_from` keeps its $FF. `ai_make_move` checks for it with a 3-byte `INC A / RET Z / DEC A` and skips the turn - without that guard, `do_move` would index `board + $FF`, which lands inside the machine code and corrupts it.

### gen_pawn: Black Pawn Moves

```asm
gen_pawn:
    ; Try forward move: square - 8
    ld      a, e
    sub     8               ; One square south
    jr      c, think_next   ; Below row 0? Off the board!
    ld      c, a            ; C = target square
    call    get_board_sq    ; A = what's on the target
    and     a               ; Empty?
    jr      nz, gp_cap      ; Blocked - try captures

    ; A push to the last rank becomes a queen - score it as one
    ld      a, c            ; Target square
    cp      8               ; Below rank 2 = Black promotes
    ld      a, 1            ; Quiet score (LD keeps the flags)
    jr      nc, gp_score
    ld      a, (piece_vals + 5) ; Promotion = a queen's worth
gp_score:
    call    try_move        ; Record if best
```

**Why SUB and not ADD:** Black pawns move south (decreasing rank), so we subtract 8. If the subtraction causes a carry (borrow), the pawn was already on rank 1 and can't move further south.

**The promotion-aware push** is a favourite byte trick: `LD` doesn't touch the flags, so `LD A, 1` can sit *between* the `CP 8` and the `JR NC` that consumes its result - the quiet score is loaded optimistically and overwritten only on the promotion rank. Without this, the evaluation saw a promoting push as just another 1-point move and the AI would grab any pawn rather than queen.

```asm
    ; Double move from starting rank?
    ld      a, e            ; Get source square
    and     $38             ; Isolate rank bits (row * 8)
    cp      $30             ; Row 6? ($30 = 48 = 6*8)
    jr      nz, gp_cap     ; Not starting rank

    ld      a, e
    sub     16              ; Two squares forward
    ld      c, a
    call    get_board_sq
    and     a
    jr      nz, gp_cap     ; Blocked
    ld      a, 1
    call    try_move
```

**The rank check trick:** `AND $38` isolates bits 3-5, which represent the rank (0-7). For rank 6 (Black's pawn starting rank), bits 3-5 = 110, so `AND $38` = $30. This is cheaper than dividing by 8 and comparing with 6.

### check_pawn_cap: Validating Pawn Captures (Including En Passant)

The two diagonal capture candidates (-7 and -9) both funnel through one validator:

```asm
check_pawn_cap:
    ; Column must change by exactly 1 (diagonal, no edge wrap)
    call    check_col_delta ; A = |col(C) - col(E)|
    dec     a
    jr      nz, cpc_bad     ; 0 = not diagonal, >=2 = wrapped

    ; Capturing onto the en passant square is valid even though
    ; the square is empty - and it captures a real pawn, so it is
    ; priced as one
    ld      a, (ep_square)
    cp      c
    jr      nz, cpc_notep
    ld      a, (piece_vals + 1)  ; The captured pawn's value
    jr      cpc_try

cpc_notep:
    ; Otherwise the target must hold a White piece
    call    get_board_sq
    and     a
    jr      z, cpc_bad      ; Empty - pawns can't "move" diagonally
    bit     3, a
    jr      nz, cpc_bad     ; Own piece - can't capture

    call    score_move
cpc_try:
    call    try_move
cpc_bad:
    ret
```

**Two things to notice.** First, the diagonal test is just `check_col_delta` (the shared edge-wrap helper) followed by `DEC A / JR NZ` - delta must be exactly 1. Second, the en passant capture is priced **explicitly** from `piece_vals`: an earlier version let `score_move` see the empty ep square and return its non-capture score of 1, which happened to equal a pawn's value - correct by accident, and a trap the moment the value table changed (which it since has).

### gen_knight / gen_king: One Body, Two Doors

The knight and king generators used to be twin 44-byte routines, identical except for the direction table and one immediate in the column-delta check. They are now two tiny prologues falling into a shared single-step body:

```asm
gen_knight:
    ld      hl, knight_dirs
    ld      d, 3            ; Column delta must be < 3
    jr      gen_step
gen_king:
    ld      hl, king_dirs
    ld      d, 2            ; Column delta must be < 2

gen_step:
    ld      b, 8            ; 8 possible moves
    ...                     ; bounds check per direction, then:
    cp      d               ; Column delta against this piece's limit
```

D is free to carry the limit because the piece type it held is dead after the dispatch, and every helper the body calls (`check_col_delta`, `get_board_sq`, `score_move`, `try_move`) preserves it. `CP D` is also a byte shorter than `CP n`. The merge freed 36 bytes - the budget that paid for the no-move guard, honest en passant pricing, and promotion-aware scoring.

### gen_slider: The Unified Sliding Piece Generator

This is my favourite part of the entire program.

```asm
gen_slider:
    ; D = piece type (3=Bishop, 4=Rook, 5=Queen)
    ld      a, d
    cp      5
    ld      a, $FF          ; Queen mask: 11111111
    jr      nc, gs_go       ; type >= 5: Queen
    ld      a, $5A          ; Rook mask: 01011010
    bit     0, d            ; Bishop=3 (odd), Rook=4 (even)
    jr      z, gs_go
    ld      a, $A5          ; Bishop mask: 10100101

gs_go:
    ld      hl, king_dirs   ; Point to direction table
    ld      b, 8            ; 8 directions
    ld      d, a            ; D = direction mask
```

The selection logic loads each candidate mask *before* testing, because `LD A, n` doesn't touch the flags - the `CP`/`BIT` results survive the load. Bishop and Rook are told apart by their low bit (3 is odd, 4 is even).

The bitmask approach: the `king_dirs` table has 8 direction offsets. For a Bishop, we only want the diagonal ones (indices 0, 2, 5, 7). The mask $A5 = 10100101 has bits set exactly at those positions.

```asm
gs_dir:
    push    bc
    push    hl
    push    de

    ld      a, d            ; Get mask
    and     $01             ; Test lowest bit
    jr      z, gs_skipdir   ; This direction not active

    ld      a, (hl)         ; Get direction offset
    ld      d, a            ; D = direction (now reused!)

    ld      a, e            ; Current position
gs_slide:
    add     a, d            ; Move one step
    cp      64
    jr      nc, gs_stopdir  ; Off the board

    ld      c, a            ; C = target square
    ; ... check column, check occupant, record move ...
    ; If empty: record non-capture, continue sliding
    ; If enemy: record capture, stop sliding
    ; If own piece: stop sliding
```

**Inside the slide loop:** For each step along the direction, we check:
1. Is the square on the board? (index 0-63)
2. Did the column wrap around? (e.g., moving east from h-file to a-file)
3. What's on the target square?

If empty: score 1, record as potential move, continue sliding.
If enemy piece: score by piece value, record as potential move, STOP (can't slide past a capture).
If own piece: STOP (blocked).

```asm
gs_skipdir:
    pop     de
    srl     d               ; Shift mask right for next direction
    pop     hl
    pop     bc
    inc     hl              ; Next direction offset
    djnz    gs_dir          ; Repeat for all 8 directions
    jp      think_next      ; Continue scanning board
```

After processing each direction, `SRL D` shifts the mask right by one bit. The next iteration tests the new bit 0. This way, we cycle through all 8 directions, checking the mask for each one.

---

## Part 7: Utility Routines

### check_col_delta: Edge Detection

```asm
check_col_delta:
    push    de
    ld      a, e            ; Source square
    and     $07             ; Source column (0-7)
    ld      d, a
    ld      a, c            ; Target square
    and     $07             ; Target column (0-7)
    sub     d               ; Difference
    jr      nc, ccd_pos
    neg                     ; Absolute value
ccd_pos:
    pop     de
    ret                     ; A = |source_col - target_col|
```

**Why we need this:** On a linear board array, moving "east" from h1 (index 7) wraps around to a2 (index 8). The direction offset +1 produces a valid index, but it's wrong - we jumped to the next rank. By checking that the column change matches the expected delta (0 or 1 for most pieces, 0-2 for knights), we catch these wrap-arounds.

### board_addr / get_board_sq: The Board Indexing Helpers

```asm
board_addr:
    ld      e, a            ; E = square number
    ld      d, 0
    ld      hl, board
    add     hl, de          ; HL -> that square
    ld      a, (hl)         ; A = piece there
    ret

get_board_sq:
    push    hl
    push    de
    ld      a, c
    call    board_addr
    pop     de
    pop     hl
    ret
```

"Index the board by a square number" is the single most repeated idiom in the program - input validation, move execution, the AI scan all need it. `board_addr` (square in A, clobbers DE) is the raw 9-byte helper; `get_board_sq` wraps it for callers inside register-sensitive loops (square in C, everything but A preserved). Factoring this out of five inlined copies paid for a good chunk of the en passant feature.

### try_move: Recording the Best Move

```asm
try_move:
    push    de
    ld      d, a            ; D = this move's score

    ; Centre column bonus: +1 for columns d,e
    ld      a, c            ; Target square
    and     $07             ; Column 0-7
    sub     3               ; Columns d,e become 0,1
    cp      2
    jr      nc, tm_no_bonus
    inc     d               ; +1 for centre column
tm_no_bonus:
    ld      a, (best_score)
    cp      d               ; Compare: best vs this
    jr      c, tm_new       ; best < this: new best
    jr      nz, tm_skip     ; best > this: skip

    ; Tied: coin flip using FRAMES counter
    ld      a, (FRAMES)     ; Pseudo-random from TV timing
    rra                     ; Bit 0 into carry
    jr      nc, tm_skip     ; 50% keep old

tm_new:
    ld      a, d
    ld      (best_score), a
    ld      a, e
    ld      (best_from), a
    ld      a, c
    ld      (best_to), a

tm_skip:
    pop     de
    ret
```

This is the "keep the best" pattern. Every potential computer move calls this routine with its score in A, source in E, and target in C - plus two refinements:

**Centre bonus:** moves targeting the d or e files score one extra point. `(col - 3)` maps columns d,e to 0,1, so a single unsigned `CP 2` catches both. This nudges the engine toward central development.

**Tie-breaking:** when a move ties with the current best, bit 0 of the FRAMES counter (a system variable the ZX81 decrements every TV frame) decides whether to keep the old move or take the new one. Without it, the a-to-h scan order made the engine relentlessly queenside-biased. (The test harnesses pin FRAMES to a fixed value so tests stay deterministic.)

---

## Byte Count Summary

Derived from the assembler's symbol table for the current build:

```
Section                  Bytes   Purpose
-----------------------  -----   -------
Board data               64      Chess board state
Working variables        7       ep_square + game state tracking
Piece chars table        7       Display lookup
Piece values table       7       AI evaluation lookup
Direction tables         16      Movement offsets
Init rank data           8       Starting position
Main loop + game over    60      Control flow, win/lose
Message data             14      "YOU WIN" / "I WIN"
Init board routine       59      Set up starting position
Display routine          58      Render board to screen
Print files line         18      Header/footer letters (shared)
Get piece char           24      Piece code to display char
Get move                 41      Move input & validation
Get square               29      Square input & echo
Wait key routine         16      Keyboard polling
Move execution           105     Moves, ep, promotion, no-move guard
Check kings              22      Game over detection
AI main loop             53      Scan board for moves
Pawn gen + capture check 101     Black pawn moves, ep, promo scoring
Knight/King generation   52      One shared single-step body
Slider generation        95      Bishop/Rook/Queen sliding
board_addr/get_board_sq  18      Board indexing helpers
check_col_delta          15      Edge-wrap detection
score_move               24      Capture evaluation
try_move                 40      Best move + bonus + tie-break
Print message            8       End-game messages
-----------------------  -----
TOTAL                    961     Every byte accounted for
                                 (hard ceiling: 984, 23 free)
```

---

## Instruction Frequency Analysis

Out of curiosity, here are the most-used Z80 instructions in this program:

```
LD A, (HL)      - 15 times  (reading memory is our #1 activity)
RST $10         - 14 times  (printing characters to screen)
JR Z / JR NZ    - 22 times  (conditional branches everywhere)
AND             - 12 times  (bit masking is fundamental)
INC HL          - 8 times   (sequential memory access)
PUSH / POP      - 18 times  (register saving/restoring)
CALL            - 12 times  (subroutine calls)
RET             - 10 times  (subroutine returns)
DJNZ            - 8 times   (compact loops)
CP              - 10 times  (comparisons)
```

The dominance of LD, AND, and JR tells the story: this program spends most of its time reading memory, testing bits, and branching. That's what a chess engine does - it looks at the board, asks questions about what it sees, and decides what to do.

---

```
 "Every instruction was chosen.
  Every byte was earned.
  Nothing is wasted."

  Total: 961 bytes
  Unused: 23 (the ceiling is 984)
```
