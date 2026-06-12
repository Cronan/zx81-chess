```
 __  __ ___ __  __  ___  _____   __  __  _ ___
|  \/  | __|  \/  |/ _ \| _ \ \ / / |  \/  | _ \
| |\/| | _|| |\/| | (_) |   /\ V /  | |\/| |  _/
|_|  |_|___|_|  |_|\___/|_|_\ |_|   |_|  |_|_|
```

# ZX81 1K Chess: Complete Memory Map

Every byte, accounted for.

> **Honesty note:** the program has outgrown the true 1K boundary. The
> REM statement now ends at $4459, past the unexpanded machine's RAM
> top of $43FF, and the emulators run the stack at $7FFF. The original
> 1983 version fitted in 1K; this rewrite traded that purity for
> features (win messages, centre bonus, random tie-breaking, en
> passant). The Makefile enforces a hard 984-byte binary ceiling so it
> can't creep further.

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
$40EF - $4458    874     Machine code + message data (executable)
$4459            1       NEWLINE (end of REM)
$445A - $446B    18      BASIC Line 2 (RAND USR)
$446C - $4485    26      Display file (collapsed)
$4486+                   E_LINE / free RAM / stack
```

The binary (`chess.bin`) is the REM content: board + variables +
tables + code = 64 + 7 + 38 + 874 = **983 bytes** (ceiling: 984).

---

## Detailed Layout

### System Variables ($4000 - $407C)

These 125 bytes are managed by the ZX81 operating system. We read some (D_FILE, LAST_K) but never write to them directly.

```
$4000  ERR_NR    DB  $FF        Error number - 1 ($FF = no error)
$4001  FLAGS     DB  %01000000  Bit flags (bit 6 usually set)
$4002  ERR_SP    DW  $xxxx      Error stack pointer
$4004  RAMTOP    DW  $xxxx      Top of RAM ($43FF on 1K hardware)
$4006  MODE      DB  $00        Cursor mode
$4007  PPC       DW  $0000      Current BASIC line
$4009  VERSN     DB  $00        BASIC version
$400A  E_PPC     DW  $0000      Edit line number
$400C  D_FILE    DW  $446C      Address of display file <<<
$400E  DF_CC     DW  $446D      Print position
$4010  VARS      DW  $4485      Variables area address
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
$407F  DW  $03D9        Line length: 985 (REM + 983 content + NL)
$4081  DB  $EA          REM token
```

Note: Line numbers are stored **big-endian** (unusual for Z80!), so line 1 is stored as $00, $01.

The ZX81 BASIC line format is:
```
Byte 0-1:  Line number (big-endian)
Byte 2-3:  Length of rest of line (little-endian)
Byte 4:    First token (REM = $EA)
Byte 5+:   Content
Last byte: NEWLINE ($76)
```

The length field = everything from byte 4 to end including NEWLINE = 1 + 983 + 1 = 985 = $03D9.

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
$40C2  ep_square   DB  $FF   En passant target square ($FF = none)
$40C3  move_from   DB  0     Player's source square
$40C4  move_to     DB  0     Player's destination square
$40C5  best_from   DB  0     Computer's best source
$40C6  best_to     DB  0     Computer's best destination
$40C7  best_score  DB  0     Computer's best score
$40C8  side        DB  0     Current side (0=White, 8=Black)
```

`ep_square` reuses the byte originally reserved for a cursor feature
that never happened. It holds the square a double-pushed pawn skipped
over, for exactly one ply: `do_move` sets it on any double pawn push
and resets it to $FF on every other move.

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

### Machine Code ($40EF - $4458)

874 bytes of executable Z80 machine code (including 14 bytes of
message data at $412B - $4138). Routine entry points in the current
build:

```
$40EF  start            $4294  check_kings
$40F5  game_loop        $42AA  think
$412B  msg_win/msg_lose $42DF  gen_pawn
$4139  init_board       $431C  check_pawn_cap
$4174  cls_and_draw     $4339  gen_knight
$41AE  print_files      $4365  gen_king
$41C0  get_piece_char   $4391  gen_slider
$41D8  get_move         $43F0  board_addr
$4201  get_square       $43F9  get_board_sq
$421E  wait_key         $4402  check_col_delta
$422E  make_move        $4411  score_move
$4238  ai_make_move     $4429  try_move
$4240  do_move          $4451  print_msg
```

See `chess.asm` for the full source and `ANNOTATED.md` for the
instruction-by-instruction walkthrough.

### Message Data ($412B - $4138)

```
"YOU WIN":  $3E $34 $3A $00 $3C $2E $33 $FF
"I WIN":   $2E $00 $3C $2E $33 $FF
```

### End of REM / BASIC Line 2 ($4459 - $446B)

```
$4459  $76          NEWLINE (end of line 1 / REM statement)

$445A  $00 $02      Line number: 2
$445C  $0E $00      Length: 14 bytes
$445E  $F1          RAND token
$445F  $D4          USR token
$4460  ...          Number encoding for 16514
$446B  $76          NEWLINE (end of line 2)
```

Note: ZX81 BASIC stores numbers in a special format: the ASCII digits followed by a 5-byte floating-point representation. "16514" takes about 10 bytes in this encoding.

### Display File ($446C - $4485)

In collapsed mode, the display file starts as just 25 NEWLINE bytes:

```
$446C  $76          Line 0  (top of screen)
$446D  $76          Line 1
$446E  $76          Line 2
...
$4485  $76          Line 24 (bottom of screen)
```

When the program draws the chess board using RST $10 (print character), the display file automatically expands. Each character printed on a previously empty line causes the line to grow. The system variables D_FILE, VARS, E_LINE, etc., are adjusted automatically by the ROM print routine.

**During gameplay**, the display file grows to approximately 200 bytes (10 lines of board display at ~20 chars each). This is why we need the stack space below to shrink correspondingly.

### Stack Space

On the original 1K plan the stack lived between the display file and
RAMTOP at $43FF. The program no longer fits under $43FF, so both
emulators (Python harness and JS browser emulator) set **SP = $7FFF**
- comfortably above everything. On real hardware with a RAM pack, the
ROM sets SP from RAMTOP as usual.

```
$7FFF  <-- Stack pointer starts here (in the emulators)
           Stack grows DOWNWARD
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

Total worst-case stack usage: ~20-30 bytes.

---

## Memory Usage by Category

```
Category               Bytes
---------------------  -----
System variables       125
BASIC overhead         24      (line 1 header + line 2 + NEWLINEs)
Board data             64
Working variables      7
Lookup tables          38
Machine code           860
Message data           14
Display file           26
                       ----
Through display file:  1158    ($4000 - $4485)
```

The binary itself: 983 of a hard 984-byte ceiling. One byte free.
In this program, that's practically an ocean.

---

```
$4000 ============================== $4485
|SYS|BAS| BOARD |V| TBL | CODE >>>>>>>>>>>>>>>>>>>>>>>|B|DISP|
|VAR|HDR| 64 B  | | 38B | 874 bytes of pure Z80       |2|FILE|
|125| 5 |       |7|     | machine code brilliance      |18| 26 |
==============================================================
        983 binary bytes. Not one wasted. (Ceiling: 984.)
```
