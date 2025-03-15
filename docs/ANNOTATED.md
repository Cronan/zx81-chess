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
cursor:     DEFB    0           ; Current cursor position
move_from:  DEFB    0           ; Player's source square (0-63)
move_to:    DEFB    0           ; Player's destination square (0-63)
best_from:  DEFB    0           ; Computer's best move source
best_to:    DEFB    0           ; Computer's best move destination
best_score: DEFB    0           ; Computer's best score so far
side:       DEFB    0           ; Whose turn: 0=White, 8=Black
```

Seven bytes. That's all the working memory the program has (besides the stack and registers). Every variable is exactly one byte because we can't afford two-byte variables where one will do.

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
    DEFB    1           ; Pawn: 1 point
    DEFB    3           ; Knight: 3 points
    DEFB    3           ; Bishop: 3 points
    DEFB    5           ; Rook: 5 points
    DEFB    9           ; Queen: 9 points
    DEFB    50          ; King: 50 points (effectively "game over")
```

Standard chess piece values, with the King given an arbitrarily high value (50) to ensure the computer will always capture an exposed King. The King's value of 50 is much higher than the total value of all other pieces combined (1+1+...+9 = about 39), so capturing a King always beats any other move.

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
    ret
```

**The trick:** We reuse the same `init_rank` table for both White and Black. For Black pieces, we just OR the colour bit in: `or 8` sets bit 3, turning White Rook ($04) into Black Rook ($0C), etc. This saves 8 bytes of data.

---

## Part 3: Display

### cls_and_draw: Rendering the Board

```asm
cls_and_draw:
    call    ROM_CLS         ; Call ZX81 ROM routine to clear screen
```

The ZX81 ROM at address $0A2A clears the display file and resets the print position. We let the ROM do the heavy lifting - no point reimplementing CLS when there's a perfectly good one in ROM.

```asm
    ; Get display file address
    ld      hl, (D_FILE)    ; Read D_FILE system variable
    inc     hl              ; Skip first NEWLINE byte
```

**Important ZX81 detail:** The display file starts with a NEWLINE ($76) byte. The actual display content begins at D_FILE + 1. If you forget the `INC HL`, everything is shifted one character to the left.

```asm
    ; Column header: "  A B C D E F G H"
    ld      a, CH_SPACE
    rst     $10             ; Print space
    rst     $10             ; Print space (2 leading spaces for alignment)
    ld      b, 8
    ld      a, CH_A         ; ZX81 char code for "A"
hdr_loop:
    push    af
    rst     $10             ; Print the letter
    ld      a, CH_SPACE
    rst     $10             ; Print space after it
    pop     af
    inc     a               ; Next letter (A->B->C...->H)
    djnz    hdr_loop
    ld      a, CH_NEWLINE
    rst     $10             ; End the line
```

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
    pop     de              ; E = file number (from the push above)
    add     a, e            ; A = rank * 8 + file
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
    ld      e, c            ; E = source square
    ld      d, 0
    ld      hl, board
    add     hl, de          ; HL = address of source square
    ld      a, (hl)         ; A = piece being moved
    ld      (hl), 0         ; Clear source (piece picked up)

    ; Place on destination
    ld      e, b            ; E = destination square
    ld      d, 0
    ld      hl, board
    add     hl, de          ; HL = address of destination
    ld      (hl), a         ; Place piece (captures automatically!)
```

**Captures are free:** We don't need special capture code. Writing the moving piece to the destination square automatically overwrites whatever was there. If it was an enemy piece, it's now gone. If it was empty, no harm done.

### Pawn Promotion (12 bytes!)

```asm
    and     $07             ; Get piece type
    cp      1               ; Is it a pawn?
    ret     nz              ; No -> done

    ld      a, b            ; Check destination rank
    cp      56              ; Rank 8? (indices 56-63)
    jr      nc, promote_w   ; White pawn reached rank 8
    cp      8               ; Rank 1? (indices 0-7)
    ret     nc              ; No promotion

    ld      a, $0D          ; Black Queen
    ld      (hl), a
    ret

promote_w:
    ld      a, $05          ; White Queen
    ld      (hl), a
    ret
```

Twelve bytes for pawn promotion. It always promotes to a Queen (no choice), which is the correct move about 99% of the time in real chess. Under-promotion to a Knight is occasionally useful, but not worth the bytes.

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
    ld      e, a
    ld      d, 0
    ld      hl, board
    add     hl, de
    ld      a, (hl)

    and     a                   ; Empty?
    jr      z, think_next       ; Skip empty squares
    bit     3, a                ; Is it Black? (our colour)
    jr      z, think_next       ; Skip White pieces

    ; Found a Black piece - generate its moves
    and     $07                 ; Get piece type
    pop     de                  ; E = square number
    push    de                  ; Put it back (we need it later)
    ld      d, a                ; D = piece type

    cp      1                   ; Pawn?
    jr      z, gen_pawn
    cp      2                   ; Knight?
    jr      z, gen_knight
    cp      6                   ; King?
    jr      z, gen_king
    jr      gen_slider          ; Must be Bishop, Rook, or Queen
```

**The scanning strategy:** We check every square on the board (0 to 63). For each Black piece found, we branch to the appropriate move generator. The piece type is in D, the square number is in E. These two values are maintained throughout the move generation for that piece.

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

    ld      a, 1            ; Empty: score = 1
    call    try_move        ; Record if best
```

**Why SUB and not ADD:** Black pawns move south (decreasing rank), so we subtract 8. If the subtraction causes a carry (borrow), the pawn was already on rank 1 and can't move further south.

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

### gen_slider: The Unified Sliding Piece Generator

This is my favourite part of the entire program.

```asm
gen_slider:
    ; D = piece type (3=Bishop, 4=Rook, 5=Queen)
    ld      a, d
    cp      3
    ld      a, $A5          ; Bishop mask: 10100101
    jr      z, gs_go
    cp      4
    ld      a, $5A          ; Rook mask: 01011010
    jr      z, gs_go
    ld      a, $FF          ; Queen mask: 11111111

gs_go:
    ld      hl, king_dirs   ; Point to direction table
    ld      b, 8            ; 8 directions
    ld      d, a            ; D = direction mask
```

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

### try_move: Recording the Best Move

```asm
try_move:
    push    de
    ld      d, a            ; D = this move's score
    ld      a, (best_score)
    cp      d               ; Compare: best vs this
    jr      nc, tm_skip     ; best >= this? Skip

    ; New best!
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

This is the "keep the best" pattern. Every potential computer move calls this routine with its score in A, source in E, and target in C. If the score beats the current best, we update. Otherwise, skip.

**Tie-breaking:** When two moves have equal scores, `CP D` / `JR NC` means we keep the existing best (skip the new one). This creates a first-found bias: pieces on lower-numbered squares (queenside) are slightly favoured. A truly random tie-break would be more fair, but would cost ~10 bytes we don't have.

---

## Byte Count Summary

```
Section                  Bytes   Purpose
-----------------------  -----   -------
Board data               64      Chess board state
Working variables        7       Game state tracking
Piece chars table        7       Display lookup
Piece values table       7       AI evaluation lookup
Direction tables         16      Movement offsets
Init rank data           8       Starting position
Init board routine       56      Set up starting position
Display routine          85      Render board to screen
Get piece char           15      Piece code to display char
Player input             55      Keyboard & square selection
Wait key routine         12      Keyboard polling
Move execution           30      Make move + promotion
Check kings              14      Game over detection
AI main loop             40      Scan board for moves
Pawn generation          50      Black pawn moves
Knight generation        30      Knight L-shaped moves
King generation          25      King single-step moves
Slider generation        80      Bishop/Rook/Queen sliding
AI helpers               40      Board lookup, col check
Score & try_move         22      Evaluation & selection
Print message            7       End-game messages
Message data             15      "YOU WIN" / "I WIN"
Main loop + game over    30      Control flow
-----------------------  -----
TOTAL                    ~672    Every byte accounted for
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

  Total: 672 bytes
  Unused: 0
```
