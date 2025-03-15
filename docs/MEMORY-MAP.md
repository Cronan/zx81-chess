```
 __  __ ___ __  __  ___  _____   __  __  _ ___
|  \/  | __|  \/  |/ _ \| _ \ \ / / |  \/  | _ \
| |\/| | _|| |\/| | (_) |   /\ V /  | |\/| |  _/
|_|  |_|___|_|  |_|\___/|_|_\ |_|   |_|  |_|_|
```

# ZX81 1K Chess: Complete Memory Map

Every one of the 1024 bytes, accounted for.

---

## Overview

```
Address Range    Size    Content
--------------   ----    -------
$4000 - $407C    125     System Variables
$407D - $4081    5       BASIC Line 1 header
$4082 - $40C1    64      Board data (in REM)
$40C2 - $40C8    7       Working variables (in REM)
$40C9 - $40CF    7       Piece characters table
$40D0 - $40D6    7       Piece values table
$40D7 - $40DE    8       King/Queen direction table
$40DF - $40E6    8       Knight direction table
$40E7 - $40EE    8       Initial rank data
$40EF - $4325    567     Machine code (executable)
$4326 - $4329    4       Win/Lose message data
$4329            1       NEWLINE (end of REM)
$432A - $433B    18      BASIC Line 2 (RAND USR)
$433C - $4354    25      Display file (collapsed)
$4355 - $43FF    171     Stack space
                 ----
                 1024    TOTAL
```

---

## Detailed Layout

### System Variables ($4000 - $407C)

These 125 bytes are managed by the ZX81 operating system. We read some (D_FILE, LAST_K) but never write to them directly.

```
$4000  ERR_NR    DB  $FF        Error number - 1 ($FF = no error)
$4001  FLAGS     DB  %01000000  Bit flags (bit 6 usually set)
$4002  ERR_SP    DW  $xxxx      Error stack pointer
$4004  RAMTOP    DW  $43FF      Top of RAM (1K = $43FF)
$4006  MODE      DB  $00        Cursor mode
$4007  PPC       DW  $0000      Current BASIC line
$4009  VERSN     DB  $00        BASIC version
$400A  E_PPC     DW  $0000      Edit line number
$400C  D_FILE    DW  $433C      Address of display file <<<
$400E  DF_CC     DW  $433D      Print position
$4010  VARS      DW  $433C      Variables area address
$4012  DEST      DW  $0000      Variable destination
$4014  E_LINE    DW  $xxxx      Edit line address
$4016  CH_ADD    DW  $xxxx      Character address
$4018  X_PTR     DW  $0000      Syntax error pointer
$401A  STKBOT    DW  $xxxx      Stack bottom
$401C  STKEND    DW  $xxxx      Stack end
$401E  BERG      DB  $00        Calculator b register
$401F  MEM       DW  $405D      Calculator memory
$4021  not used  DB  $00
$4022  DF_SZ     DB  $02        Display file size (lines)
$4023  S_TOP     DW  $0002      Top program line
$4025  LAST_K    DW  $FFFF      Last key pressed <<<
$4027  DEBOUNCE  DB  $FF        Key debounce counter
$4028  MARGIN    DB  $37        TV margin (PAL = 55)
$4029  NXTLIN    DW  $xxxx      Next BASIC line to execute
$402B  OLDPPC    DW  $0000      Previous line (for CONT)
$402D  FLAGX     DB  $00        More flags
$402E  STRLEN    DW  $0000      String length
$4030  T_ADDR    DW  $xxxx      Tokeniser address
$4032  SEED      DW  $0000      Random seed
$4034  FRAMES    DW  $xxxx      Frame counter <<<
$4036  COORDS    DW  $0000      Plot coordinates
$4038  PR_CC     DB  $BC        Printer column
$4039  S_POSN    DW  $2121      Print position (col, row)
$403B  CDFLAG    DB  %01000000  Bit 6: SLOW mode active
$403C  PRBUF     33 bytes       Printer buffer
$405D  MEMBOT    30 bytes       Calculator memory
$407B  not used  DW  $0000
```

### BASIC Line 1 Header ($407D - $4081)

```
$407D  DW  $0001        Line number: 1 (stored big-endian!)
$407F  DW  $02A3        Line length: 675 (672 content + REM + NL)
$4081  DB  $EA          REM token
```

Note: Line numbers are stored **big-endian** (unusual for Z80!), so line 1 is stored as $00, $01. The line length includes the REM token byte and the trailing NEWLINE, so 672 + 1 + 2 = 675 bytes. Wait - actually the length field counts from after the length field to the NEWLINE inclusive, so it's 672 (content) + 1 (REM token) + 1 (NEWLINE) = 674 bytes. Let me correct that:

Actually, the ZX81 BASIC line format is:
```
Byte 0-1:  Line number (big-endian)
Byte 2-3:  Length of rest of line (little-endian)
Byte 4:    First token (REM = $EA)
Byte 5+:   Content
Last byte: NEWLINE ($76)
```

The length field = everything from byte 4 to end including NEWLINE = 1 + 672 + 1 = 674 = $02A2.

### Board Data ($4082 - $40C1)

```
$4082  Starting position (initialised by code at runtime):

       Index  Hex   Meaning
       -----  ---   -------
       0-7    04 02 03 05 06 03 02 04    White: R N B Q K B N R
       8-15   01 01 01 01 01 01 01 01    White: 8 pawns
       16-23  00 00 00 00 00 00 00 00    Empty rank 3
       24-31  00 00 00 00 00 00 00 00    Empty rank 4
       32-39  00 00 00 00 00 00 00 00    Empty rank 5
       40-47  00 00 00 00 00 00 00 00    Empty rank 6
       48-55  09 09 09 09 09 09 09 09    Black: 8 pawns
       56-63  0C 0A 0B 0D 0E 0B 0A 0C    Black: R N B Q K B N R
```

Visual representation:
```
  a    b    c    d    e    f    g    h
+----+----+----+----+----+----+----+----+
| 0C | 0A | 0B | 0D | 0E | 0B | 0A | 0C |  Rank 8 (idx 56-63)
| bR | bN | bB | bQ | bK | bB | bN | bR |
+----+----+----+----+----+----+----+----+
| 09 | 09 | 09 | 09 | 09 | 09 | 09 | 09 |  Rank 7 (idx 48-55)
| bp | bp | bp | bp | bp | bp | bp | bp |
+----+----+----+----+----+----+----+----+
| 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 |  Rank 6 (idx 40-47)
|    |    |    |    |    |    |    |    |
+----+----+----+----+----+----+----+----+
| 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 |  Rank 5 (idx 32-39)
|    |    |    |    |    |    |    |    |
+----+----+----+----+----+----+----+----+
| 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 |  Rank 4 (idx 24-31)
|    |    |    |    |    |    |    |    |
+----+----+----+----+----+----+----+----+
| 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 |  Rank 3 (idx 16-23)
|    |    |    |    |    |    |    |    |
+----+----+----+----+----+----+----+----+
| 01 | 01 | 01 | 01 | 01 | 01 | 01 | 01 |  Rank 2 (idx 8-15)
| wP | wP | wP | wP | wP | wP | wP | wP |
+----+----+----+----+----+----+----+----+
| 04 | 02 | 03 | 05 | 06 | 03 | 02 | 04 |  Rank 1 (idx 0-7)
| wR | wN | wB | wQ | wK | wB | wN | wR |
+----+----+----+----+----+----+----+----+
```

### Working Variables ($40C2 - $40C8)

```
$40C2  cursor      DB  0     Cursor position (0-63)
$40C3  move_from   DB  0     Player's source square
$40C4  move_to     DB  0     Player's destination square
$40C5  best_from   DB  0     Computer's best source
$40C6  best_to     DB  0     Computer's best destination
$40C7  best_score  DB  0     Computer's best score
$40C8  side        DB  0     Current side (0=White, 8=Black)
```

### Lookup Tables ($40C9 - $40EE)

```
Piece Characters ($40C9 - $40CF):
  $40C9  $00  (empty -> space)
  $40CA  $35  (Pawn  -> "P")
  $40CB  $33  (Knight -> "N")
  $40CC  $27  (Bishop -> "B")
  $40CD  $37  (Rook   -> "R")
  $40CE  $36  (Queen  -> "Q")
  $40CF  $30  (King   -> "K")

Piece Values ($40D0 - $40D6):
  $40D0  $00  (empty -> 0)
  $40D1  $01  (Pawn  -> 1)
  $40D2  $03  (Knight -> 3)
  $40D3  $03  (Bishop -> 3)
  $40D4  $05  (Rook   -> 5)
  $40D5  $09  (Queen  -> 9)
  $40D6  $32  (King   -> 50)

King/Queen Directions ($40D7 - $40DE):
  $40D7  $F7  (-9  = SW)
  $40D8  $F8  (-8  = S)
  $40D9  $F9  (-7  = SE)
  $40DA  $FF  (-1  = W)
  $40DB  $01  (+1  = E)
  $40DC  $07  (+7  = NW)
  $40DD  $08  (+8  = N)
  $40DE  $09  (+9  = NE)

Knight Directions ($40DF - $40E6):
  $40DF  $EF  (-17 = 2S+1W)
  $40E0  $F1  (-15 = 2S+1E)
  $40E1  $F6  (-10 = 2W+1S)
  $40E2  $FA  (-6  = 2E+1S)
  $40E3  $06  (+6  = 2W+1N)
  $40E4  $0A  (+10 = 2E+1N)
  $40E5  $0F  (+15 = 2N+1W)
  $40E6  $11  (+17 = 2N+1E)

Initial Rank ($40E7 - $40EE):
  $40E7  $04  (Rook)
  $40E8  $02  (Knight)
  $40E9  $03  (Bishop)
  $40EA  $05  (Queen)
  $40EB  $06  (King)
  $40EC  $03  (Bishop)
  $40ED  $02  (Knight)
  $40EE  $04  (Rook)
```

### Machine Code ($40EF - $4325)

567 bytes of executable Z80 machine code. See `chess.asm` for the full disassembly and `ANNOTATED.md` for the instruction-by-instruction walkthrough.

### Message Data ($4326 - $4329)

```
"YOU WIN":  $3E $34 $3A $00 $3C $2E $33 $FF
"I WIN":   $2E $00 $3C $2E $33 $FF
```

### End of REM / BASIC Line 2 ($4329 - $433B)

```
$4329  $76          NEWLINE (end of line 1 / REM statement)

$432A  $00 $02      Line number: 2
$432C  $0E $00      Length: 14 bytes
$432E  $F1          RAND token
$432F  $D4          USR token
$4330  ...          Number encoding for 16514
$433B  $76          NEWLINE (end of line 2)
```

Note: ZX81 BASIC stores numbers in a special format: the ASCII digits followed by a 5-byte floating-point representation. "16514" takes about 10 bytes in this encoding.

### Display File ($433C - $4354)

In collapsed (1K) mode, the display file starts as just 25 NEWLINE bytes:

```
$433C  $76          Line 0  (top of screen)
$433D  $76          Line 1
$433E  $76          Line 2
...
$4354  $76          Line 24 (bottom of screen)
```

When the program draws the chess board using RST $10 (print character), the display file automatically expands. Each character printed on a previously empty line causes the line to grow. The system variables D_FILE, VARS, E_LINE, etc., are adjusted automatically by the ROM print routine.

**During gameplay**, the display file grows to approximately 200 bytes (10 lines of board display at ~20 chars each). This is why we need the stack space below to shrink correspondingly.

### Stack Space ($4355 - $43FF)

```
$43FF  <-- Stack pointer starts here (top of RAM)
           Stack grows DOWNWARD
$4355  <-- Lowest safe stack address (approximate)
```

The stack is used for:
- CALL/RET pairs (2 bytes each)
- PUSH/POP (2 bytes each)
- Interrupt handling (2 bytes for the return address)

Our deepest calling chain is approximately:
```
game_loop
  -> think
    -> gen_slider
      -> gs_slide (inner loop)
        -> get_board_sq
          -> (5 levels deep = ~10 bytes of return addresses)
```

Plus any PUSH/POP within those routines (up to ~8 more bytes).

Total worst-case stack usage: ~20-30 bytes. We have 171 bytes of stack space, which is plenty. The extra space acts as a safety margin for when the display file expands during board rendering.

---

## Memory Usage by Category

```
Category               Bytes    Percentage
---------------------  -----    ----------
System variables       125      12.2%
BASIC overhead         24       2.3%
Board data             64       6.3%
Working variables      7        0.7%
Lookup tables          38       3.7%
Machine code           567      55.4%
Message data           14       1.4%
Display file           25       2.4%
Stack space            171      16.7%
TOTAL (incl. margin)   1024     100.0%  (actually ~1016 used)

Actually used:         ~1016    99.2%
Free:                  ~8       0.8%
```

Eight bytes free. In a 1K program, that's practically an ocean.

---

```
$4000 ========================= $43FF
|SYS|BAS| BOARD |V| TBL | CODE >>>>>>>>>>>>>>>>>>>|B|DISP|STACK|
|VAR|HDR| 64 B  | | 38B | 567 bytes of pure Z80   |2|FILE|grows|
|125| 5 |       |7|     | machine code brilliance  |18| 25 |<----|
================================================================
              1024 bytes. Not one wasted.
```
