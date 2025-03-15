```
 _____ _  _ ___    ______  _____ _
|_   _| || | __|  |__  / |/ ( _ ) / |
  | | | __ | _|     / /|   // _ \/| |
  |_| |_||_|___|   /___|_|\_\___/ |_|
```

# The ZX81: A Technical Reference and Love Letter

---

## The Machine

Released in March 1981 by Sinclair Research Ltd (Cambridge, UK), the ZX81 was designed by one of computing history's great mavericks: **Sir Clive Sinclair**. It was designed to be the cheapest possible home computer, and it succeeded spectacularly.

```
  ________________________________________
 |  _____________________________________/
 | |
 | |  S I N C L A I R    Z X 8 1
 | |
 | |  ___ ___ ___ ___ ___ ___ ___ ___ ___ ___
 | | | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 |
 | | |___|___|___|___|___|___|___|___|___|___|
 | |  ___ ___ ___ ___ ___ ___ ___ ___ ___ ___
 | | | Q | W | E | R | T | Y | U | I | O | P |
 | | |___|___|___|___|___|___|___|___|___|___|
 | |   ___ ___ ___ ___ ___ ___ ___ ___ ___ ________
 | |  | A | S | D | F | G | H | J | K | L |NEWLINE |
 | |  |___|___|___|___|___|___|___|___|___|________|
 | | _______ ___ ___ ___ ___ ___ ___ ___ ___ _____
 | ||SHIFT  | Z | X | C | V | B | N | M | . |SPACE|
 | ||_______|___|___|___|___|___|___|___|___|_____|
 | |________________________________________
 |__________________________________________|
```

### Specifications

| Feature | Detail |
|---|---|
| **CPU** | Zilog Z80A @ 3.25 MHz |
| **RAM** | 1K (expandable to 16K or 64K) |
| **ROM** | 8K (containing BASIC interpreter and OS) |
| **Display** | 32 x 24 characters, black and white |
| **Resolution** | 256 x 192 pixels (with tricks) |
| **Keyboard** | 40-key membrane keyboard |
| **Storage** | Cassette tape (300 baud) |
| **TV Output** | UHF Channel 36 (PAL) |
| **Power** | 9V DC, 700mA |
| **Price** | £49.95 (kit) / £69.95 (built) |
| **Weight** | 350g |
| **Dimensions** | 167mm x 175mm x 40mm |

---

## The Z80A Processor

The heart of the ZX81. The Zilog Z80A is an 8-bit processor that was the workhorse of early home computing, also found in the ZX Spectrum, MSX computers, Amstrad CPC, and the original Game Boy.

### Registers

```
Main registers:          Alternate registers:
  A  F  (Accumulator      A' F'
         + Flags)
  B  C                    B' C'
  D  E                    D' E'
  H  L                    H' L'

Special registers:
  IX     (Index X, 16-bit)
  IY     (Index Y, 16-bit - used by ZX81 ROM, don't touch!)
  SP     (Stack Pointer, 16-bit)
  PC     (Program Counter, 16-bit)
  I      (Interrupt vector - used by ZX81 display system)
  R      (Memory refresh counter)
```

**A warning about IY:** On the ZX81, the IY register is used by the ROM's display routine. If you change IY and then execute a HALT (which triggers the display interrupt), the ZX81 will crash spectacularly. Many novice machine coders learned this the hard way.

### Key Instructions Used in This Program

```
Instruction  Bytes  T-states  What it does
-----------  -----  --------  ------------
LD A, n      2      7         Load A with immediate byte
LD A, (HL)   1      7         Load A from memory at HL
LD (HL), A   1      7         Store A to memory at HL
LD HL, nn    3      10        Load HL with 16-bit value
ADD A, n     2      7         A = A + n
SUB n        2      7         A = A - n
AND n        2      7         A = A AND n
OR n         2      7         A = A OR n
XOR A        1      4         A = 0 (fastest way to zero A)
CP n         2      7         Compare A with n (sets flags)
BIT b, r     2      8         Test bit b of register r
JR cc, e     2      7/12      Relative jump (if condition met)
JP nn        3      10        Absolute jump
CALL nn      3      17        Call subroutine
RET          1      10        Return from subroutine
PUSH rr      1      11        Push register pair onto stack
POP rr       1      10        Pop register pair from stack
RST n        1      11        Call to fixed address (fast!)
HALT         1      4+        Wait for interrupt
DJNZ e       2      8/13      Decrement B, jump if not zero
INC r        1      4         r = r + 1
DEC r        1      4         r = r - 1
RLCA         1      4         Rotate A left (x2)
NEG          2      8         A = 0 - A (negate)
SRL r        2      8         Shift r right logical (/2)
```

### The Flag Register

The F register holds condition flags that are set by arithmetic and logic operations:

```
Bit  Flag  Name       Set when...
---  ----  ----       -----------
7    S     Sign       Result is negative (bit 7 set)
6    Z     Zero       Result is zero
5    -     (unused)
4    H     Half-carry Carry from bit 3 to bit 4
3    -     (unused)
2    P/V   Parity/    Even parity (logic) or overflow (arith)
           Overflow
1    N     Subtract   Last operation was subtraction
0    C     Carry      Result overflowed 8 bits
```

The flags we care about most:
- **Z (Zero):** Set when a comparison matches, or a result is zero
- **C (Carry):** Set when an addition overflows or subtraction underflows
- **NZ, NC:** The opposite conditions

---

## The ZX81's Memory Map

```
$0000 +---------------------------+ 0
      |                           |
      | ROM (8K)                  |
      | Contains:                 |
      |  - Z80 restart vectors    |
      |  - Character set          |
      |  - BASIC interpreter      |
      |  - Floating point maths   |
      |  - Display generation     |
      |  - Keyboard scanning      |
      |  - Tape I/O               |
      |  - CLS, PRINT, etc.       |
      |                           |
$2000 +---------------------------+ 8192
      |                           |
      | (Unused / Echo of ROM)    |
      |                           |
$4000 +---------------------------+ 16384
      |                           |
      | RAM (1K or 16K)           |
      |                           |
      | $4000: System variables   |
      | $407D: BASIC program      |
      | D_FILE: Display file      |
      | VARS: BASIC variables     |
      | E_LINE: Edit line         |
      | ...                       |
      | Stack (grows down)        |
      |                           |
$4400 +---------------------------+ 17408  (1K boundary)
  or
$8000 +---------------------------+ 32768  (16K boundary)
```

### System Variables (The Important Ones)

```
Address  Name      Bytes  Purpose
-------  ----      -----  -------
$4000    ERR_NR    1      Error code minus 1 (0 = OK)
$4001    FLAGS     1      Various flags:
                           Bit 0: Suppresses leading space
                           Bit 1: Set during print
                           Bit 2: Set for L mode (letters)
                           Bit 3: Set for C mode
                           Bit 5: Set if key pressed
                           Bit 7: Set for syntax checking
$4002    ERR_SP    2      Stack pointer for errors
$4004    RAMTOP    2      Top of available RAM
$4006    MODE      1      Current cursor mode
$4007    PPC       2      Current BASIC line number
$400C    D_FILE    2      Address of display file
$400E    DF_CC     2      Current print position in display
$4010    VARS      2      Address of BASIC variables area
$4014    E_LINE    2      Address of line being edited
$4025    LAST_K    2      Last key pressed (see below)
$4027    DEBOUNCE  1      Keyboard debounce counter
$4028    MARGIN    1      Lines before/after display (PAL=55)
$4029    NXTLIN    2      Address of next BASIC line
$4034    FRAMES    2      Frame counter (counts down)
$403B    CDFLAG    1      Display flags:
                           Bit 6: 0=FAST, 1=SLOW mode
                           Bit 7: Set during display
```

### The Display File

The display file is a sequence of bytes representing the screen content. In the ZX81's "slow" mode, this is maintained by the display interrupt routine.

**Full display file (16K mode):** 793 bytes
- 25 NEWLINE bytes (one per line, including final)
- 768 character bytes (24 lines x 32 characters)

**Collapsed display file (1K mode):** Variable, typically 25-200 bytes
- Lines with no content are stored as just a NEWLINE byte
- Lines with content store only the characters up to the last non-space
- This saves enormous amounts of RAM in 1K mode

**NEWLINE character:** $76 (decimal 118). This is actually the Z80 HALT instruction! When the display routine encounters a HALT in the display file, it stops outputting characters for that line and generates the horizontal sync signal. Elegant dual-purpose design.

### The Character Set

The ZX81 does NOT use ASCII. It has its own character encoding:

```
Code  Char    Code  Char    Code  Char    Code  Char
----  ----    ----  ----    ----  ----    ----  ----
$00   space   $10   (       $20   [gfx]  $30   K
$01   [gfx]   $11   )       $21   [gfx]  $31   L
$02   [gfx]   $12   >       $22   [gfx]  $32   M
$03   [gfx]   $13   <       $23   [gfx]  $33   N
$04   [gfx]   $14   =       $24   [gfx]  $34   O
$05   [gfx]   $15   +       $25   [gfx]  $35   P
$06   [gfx]   $16   -       $26   A      $36   Q
$07   [gfx]   $17   *       $27   B      $37   R
$08   [gfx]   $18   /       $28   C      $38   S
$09   [gfx]   $19   ;       $29   D      $39   T
$0A   [gfx]   $1A   ,       $2A   E      $3A   U
$0B   "       $1B   .       $2B   F      $3B   V
$0C   pound   $1C   0       $2C   G      $3C   W
$0D   $       $1D   1       $2D   H      $3D   X
$0E   :       $1E   2       $2E   I      $3E   Y
$0F   ?       $1F   3       $2F   J      $3F   Z
                $20   4
                $21   5
                $22   6       Codes $80-$BF are the
                $23   7       INVERSE VIDEO versions
                $24   8       of codes $00-$3F.
                $25   9       (Same character, but
                              white-on-black instead
                              of black-on-white.)
```

Note: Codes $01-$0A are graphics block characters, useful for drawing simple graphics. Each represents a 2x2 grid of filled/empty quadrants, giving 10 unique patterns.

---

## ROM Routines: Free Code

The ZX81's 8K ROM contains routines that machine code programs can call for free. These are the most useful:

### RST $10 - Print a Character

```
Entry:  A = character code to print
Exit:   Character printed at current DF_CC position
        DF_CC advanced to next position
Alters: Many registers (save what you need!)
Cost:   1 byte (RST instructions are single-byte CALLs)
```

This is the workhorse display routine. Every character on screen is printed through RST $10. It handles line wrapping, scrolling, and display file management automatically.

The RST (restart) instruction is a one-byte CALL to a fixed address. RST $10 calls address $0010, where the ROM's print routine lives. Using RST instead of `CALL $0010` saves 2 bytes every time.

### ROM_CLS ($0A2A) - Clear Screen

```
Entry:  (none)
Exit:   Display file cleared, DF_CC reset
Alters: Many registers
Cost:   3 bytes (CALL instruction)
```

Clears the entire screen and resets the print position to the top-left corner. Also rebuilds the display file, which is important in 1K mode where the display file is collapsed.

### Other Useful ROM Routines

```
$028E  KEYBOARD    - Scan keyboard matrix
$0F46  BREAK_KEY   - Check if BREAK pressed
$0802  PRINT_FP    - Print floating-point number
$1A1B  SLOW_FAST   - Toggle slow/fast mode
$0207  PRINT_A     - Print character with scroll check
```

---

## The Keyboard

The ZX81 keyboard is a membrane keyboard - flat, with no moving parts. Each key has up to five functions depending on the current mode. The keys are arranged in a standard QWERTY layout.

### Keyboard Matrix

The keyboard is organised as a matrix of 8 rows x 5 columns, read via I/O ports:

```
Port Address   Keys
(Active low)
$FEFE         SHIFT, Z, X, C, V
$FDFE         A, S, D, F, G
$FBFE         Q, W, E, R, T
$F7FE         1, 2, 3, 4, 5
$EFFE         0, 9, 8, 7, 6
$DFFE         P, O, I, U, Y
$BFFE         NEWLINE, L, K, J, H
$7FFE         SPACE, ., M, N, B
```

To scan the keyboard in machine code:
1. Load the port address high byte into the A register
2. Read port $FE: `IN A, ($FE)`
3. The bottom 5 bits indicate which keys are pressed (0 = pressed)

For example, to check if 'A' is pressed:
```asm
    ld      a, $fd          ; Row containing A, S, D, F, G
    in      a, ($fe)        ; Read the port
    bit     0, a            ; Test bit 0 (A key)
    jr      z, a_pressed    ; 0 = pressed!
```

However, in this chess program we use the simpler approach of checking the LAST_K system variable, which is updated by the interrupt-driven keyboard scanner.

---

## Tips for ZX81 Machine Code Programming

### Do's

1. **Use RST $10 for printing.** It's one byte instead of three.

2. **Use XOR A to zero the accumulator.** It's one byte vs. two for `LD A, 0`.

3. **Use DJNZ for counted loops.** It's 2 bytes vs. 4 for `DEC B / JR NZ`.

4. **Use JR instead of JP where possible.** JR is 2 bytes, JP is 3. JR has a range of -128 to +127 bytes, which is enough for most jumps.

5. **Keep data tables small.** Every byte of data is a byte less for code.

6. **Use the ROM!** The 8K ROM is full of useful routines. Every routine you call from ROM is code you don't have to write.

7. **Test with small programs first.** Write the display routine, test it. Write the input routine, test it. Then combine. Don't try to type in 672 bytes and hope for the best.

### Don'ts

1. **Don't touch IY.** The ZX81 ROM display routine uses IY as a base pointer. Changing it will crash the display. (The Spectrum has the same issue.)

2. **Don't modify system variables carelessly.** Many are interdependent. Changing D_FILE without updating VARS and E_LINE will corrupt memory.

3. **Don't forget HALT.** In slow mode, the display is generated by the NMI interrupt routine. HALT triggers this. If your program runs for too long without a HALT, the display goes blank (the "fast mode" effect).

4. **Don't use IM 2.** The ZX81 uses interrupt mode 1 (IM 1). Switching to IM 2 will crash the system unless you've set up a proper interrupt vector table.

5. **Don't trust the stack.** In 1K mode, the stack is perilously close to the end of RAM. Deep nesting of CALL instructions can overflow the stack and corrupt the display file or BASIC program.

6. **Don't use IX for casual storage.** IX is slow (all IX instructions take extra T-states because they have a $DD prefix byte). Use HL where possible.

---

## The 1K Limitation: A Deeper Look

In 1K mode, the ZX81 has RAM from $4000 to $43FF. Here's what competes for those 1024 bytes:

**Fixed overhead (non-negotiable):**
- System variables: 125 bytes
- BASIC program minimum: ~6 bytes (one line)
- Display file minimum: ~25 bytes (all collapsed lines)
- End markers: ~5 bytes (VARS, E_LINE markers)

**Total fixed overhead: ~161 bytes**

**Available for your program: ~863 bytes**

But that 863 bytes must also include:
- Stack space (every CALL uses 2 bytes, every PUSH uses 2 bytes)
- The display file grows when content is displayed (each non-blank line adds up to 33 bytes)

In practice, a 1K program that displays a full chess board (which expands ~10 display lines) might have only 600-700 bytes for actual code and data.

This is why the BASIC program is kept to exactly 2 lines, the display is rebuilt from scratch using CLS + RST $10 (letting the ROM manage the display file), and the stack is used carefully.

---

## Resources and Links

### Books (Original 1980s Publications)

- **"Mastering Machine Code on Your ZX81"** by Toni Baker (1983)
  - THE book for ZX81 machine code. Clear, progressive, brilliant.
  - Available second-hand on eBay and AbeBooks

- **"Understanding Your ZX81 ROM"** by Dr. Ian Logan (1982)
  - Complete disassembly and annotation of the 8K ROM
  - Essential reference for ROM calling conventions

- **"The ZX81 Companion"** by Bob Sheraga (1982)
  - Good beginner's guide to ZX81 programming

- **"ZX81 Machine Code Made Easy"** by Beam Software (1982)
  - Another solid introduction to Z80 on the ZX81

### Websites

- **Planet Sinclair** - https://www.nvg.ntnu.no/sinclair/
  - Encyclopaedic resource on all things Sinclair

- **Sinclair ZX World** - https://www.sinclairzxworld.com/
  - Active community, forums, software archive

- **ZX81 Stuff** - https://www.zx81stuff.org.uk/
  - Software library, technical docs, emulators

- **World of Spectrum (Forums)** - https://worldofspectrum.net/
  - Spectrum-focused but with active ZX81 discussion

- **Retro Computing Roundtable** - https://retrocomputingroundtable.com/
  - General retro computing community

### Software Archives

- **ZX81 Program Archive** - https://www.zx81stuff.org.uk/zx81/archive.html
  - Hundreds of original ZX81 programs

- **Internet Archive ZX81 Collection** - https://archive.org/details/zx81_library
  - Playable in-browser

### Z80 References

- **Z80 CPU User Manual** - http://www.z80.info/z80-documented.htm
  - Complete instruction set reference

- **Z80 Instruction Set Table** - http://clrhome.org/table/
  - Quick visual reference card

- **Z80 Heaven** - http://z80-heaven.wikidot.com/
  - Tutorials, tips, and tricks

### Emulators

- **EightyOne** - https://sourceforge.net/projects/eightyone-sinclair-emulator/
- **sz81** - http://sz81.sourceforge.net/
- **ZXSP** - https://k1.spdns.de/Develop/Projects/zxsp/Distributions/
- **Fuse** - http://fuse-emulator.sourceforge.net/

### Tools

- **z80asm** (Z80 cross-assembler) - https://www.nongnu.org/z80asm/
- **pasmo** (Z80 assembler) - https://pasmo.speccy.org/
- **zmac** (Z80 macro assembler) - http://48k.ca/zmac.html
- **ZX81 BASIC to .P converter** - various GitHub repos

---

```
  "The Sinclair ZX81 proved that you
   didn't need expensive hardware to
   change someone's life. You just
   needed curiosity, persistence,
   and 1024 bytes."
```
