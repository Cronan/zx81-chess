```
 ___ __  __ _   _ _      _ _____ ___  ___  ___
| __|  \/  | | | | |    /_\_   _/ _ \| _ \/ __|
| _|| |\/| | |_| | |__ / _ \| || (_) |   /\__ \
|___|_|  |_|\___/|____/_/ \_\_| \___/|_|_\|___/
```

# Running ZX81 1K Chess on Modern Hardware

You don't need a real ZX81 to play this game (though if you have one: respect). Several excellent emulators can run ZX81 software on modern computers.

---

## Recommended Emulators

### EightyOne (Windows) - Top Recommendation

The most accurate ZX81 emulator available. Emulates the ZX81 hardware down to the ULA level, including the famous "flicker" of 1K programs.

- **Website:** https://sourceforge.net/projects/eightyone-sinclair-emulator/
- **Platform:** Windows (runs under Wine on Linux/Mac)
- **Features:**
  - Cycle-accurate Z80 emulation
  - 1K and 16K RAM configurations
  - Tape loading (.P files)
  - Full keyboard emulation
  - Debugger with memory viewer (great for poking around!)

**Setup for 1K Chess:**
1. Download and install EightyOne
2. Go to `Hardware > ZX81` to select the ZX81 model
3. Go to `Hardware > Memory` and select **1K** (important!)
4. Load the `.P` file: `File > Open Tape` then `File > Load`
5. Or type in the program manually (the authentic experience)

### sz81 (Linux / macOS)

A lightweight, open-source ZX81 emulator.

- **Website:** http://sz81.sourceforge.net/
- **Platform:** Linux, macOS (requires SDL)
- **Features:**
  - Clean, simple interface
  - 1K/16K modes
  - .P file loading
  - Source code available

**Install on Linux:**
```bash
# Debian/Ubuntu
sudo apt-get install sz81

# Or build from source
git clone https://git.code.sf.net/p/sz81/code sz81
cd sz81
make
./sz81
```

### ZX81 Online Emulators (No Install Required)

For instant gratification, try a browser-based emulator:

- **JtyOne Online** - https://www.zx81stuff.org.uk/zx81/jtyone.html
  - Java-based ZX81 emulator that runs in your browser
  - Supports .P file loading
  - Set to 1K mode for authentic experience

- **ZX81 on Internet Archive** - https://archive.org/details/zx81_library
  - Large collection of ZX81 software playable in the browser
  - Uses the JSMESS emulator

### ZXSP (macOS)

A polished ZX Spectrum/ZX81 emulator for Mac.

- **Website:** https://k1.spdns.de/Develop/Projects/zxsp/Distributions/
- **Platform:** macOS
- **Features:**
  - Native macOS application
  - Beautiful retro display rendering
  - ZX81 mode with 1K support

### Fuse (Multi-platform)

Primarily a ZX Spectrum emulator, but some versions support ZX81 mode.

- **Website:** http://fuse-emulator.sourceforge.net/
- **Platform:** Linux, macOS, Windows
- **Note:** ZX81 support varies by version

---

## Loading the Game

### Method 1: Load a .P File (Easiest)

If you have a `.P` file (the ZX81's native tape format):

1. Open the emulator
2. Set RAM to 1K
3. Load the .P file using the emulator's tape loading function
4. The program should auto-run, or type `RUN` and press NEWLINE

### Method 2: Type It In (Authentic!)

For the true 1983 experience, type the program in from scratch:

1. Open the emulator, set to 1K RAM
2. You'll see the `K` cursor (the ZX81 is in keyword mode)
3. Type line 1:
   - Press `E` for REM (in keyword mode, E = REM)
   - Press NEWLINE
   - Now type 672 space characters after the REM
   - (Or use a shorter REM and POKE the rest - see loader.bas)

4. Type line 2:
   - Type `2` (line number)
   - Press `T` for RAND (in keyword mode, T = RAND)
   - Press `SHIFT+L` for USR
   - Type `16514`
   - Press NEWLINE

5. Now POKE in the machine code:
   - Type each POKE command from the listing
   - Example: `POKE 16585,0` then NEWLINE
   - Repeat for all 672 bytes...
   - (This is why God invented tape recorders)

6. When done:
   - Type `RAND USR 16514` and press NEWLINE
   - The chess board should appear!

### Method 3: Hex Editor (Modern Shortcut)

If you're comfortable with hex editors:

1. Create a .P file from the hex dump (see `hexdump.txt`)
2. The .P file format is simply a memory dump from D_FILE onwards
3. Load it in your emulator

---

## ZX81 Keyboard Reference

The ZX81 keyboard is... unique. Every key has multiple functions depending on the current mode (K for keyword, L for letter, etc.). The mode is shown by the cursor character.

For playing chess, you mainly need letters (A-H) and numbers (1-8):

```
 ___________________________________
|                                   |
| 1  2  3  4  5  6  7  8  9  0     |
|  Q  W  E  R  T  Y  U  I  O  P   |
|   A  S  D  F  G  H  J  K  L     |
|SHIFT Z  X  C  V  B  N  M  .  SP |
|___________________________________|
```

**Important:**
- The ZX81 starts in K (keyword) mode - press SHIFT to enter L (letter) mode
- In L mode, pressing A-H gives you the letters
- Numbers 1-8 work in any mode
- NEWLINE = Enter
- BREAK = SHIFT + SPACE (stops the program)

**In the emulator:**
- Your computer keyboard maps to the ZX81 keyboard
- Usually the mapping is straightforward (A=A, 1=1, etc.)
- SHIFT on ZX81 = SHIFT on your keyboard
- NEWLINE = ENTER
- Check your emulator's documentation for exact mappings

---

## Troubleshooting

### "The screen is blank / flickering"

This is normal for 1K mode! The ZX81 generates its display using software, and in 1K mode there isn't enough RAM for a full display file. The game should still work - the display will appear when the board is drawn.

If using EightyOne, try `Display > Artifacts > None` for a cleaner display.

### "The program crashes when I type RUN"

1. Make sure you're in 1K mode (some emulators default to 16K)
2. Check that the REM statement has enough bytes
3. Verify the POKE values are correct (one wrong byte = crash)
4. Try saving and reloading - sometimes the display file gets corrupted

### "The keyboard doesn't respond during the game"

The game uses HALT-based keyboard polling. If the emulator's timing isn't accurate, keys might be missed. Try:
- Pressing keys firmly (hold for at least 1/10th second)
- Adjusting emulator speed to normal (not turbo)
- Checking that the emulator is sending keyboard interrupts

### "Memory full" error

You're probably in 16K mode trying to type a long program. Switch to 1K mode and enter just lines 1 and 2 (the minimal version).

Or if you're trying to run the loader (which needs 16K), make sure the emulator is set to 16K RAM.

### "Invalid character" or strange display

Remember that the ZX81 uses its own character set, not ASCII. If you're seeing strange characters, the piece encoding or display routine may have an error. Check the POKE values against the listing.

---

## Creating a .P File

The ZX81 .P file format is a raw memory dump. The file contains:

```
Offset  Content
------  -------
0       System variables (from $4009 to end of sysvars)
116+    BASIC program
???     Display file
???     Variables
```

Several tools can create .P files:

- **zx81-tools** (Python): https://github.com/jameswolfden/zx81-tools
- **zmakebas** (C): Creates BASIC programs as .P files
- **bin2p** (various): Converts raw binary to .P format

For a manual approach, you can use a hex editor to construct the .P file byte by byte, following the ZX81 memory layout documented in `MEMORY-MAP.md`.

---

## Recording a Session

Want to capture your game for posterity?

- **EightyOne** can save screenshots (BMP format)
- **sz81** supports screen capture
- Most emulators let you save the machine state at any point
- Screen recording software works too (OBS, etc.)

---

## Recommended Settings for Authentic Experience

For the full 1983 nostalgia:

1. Set RAM to **1K** (not 16K)
2. Set display to **PAL** (50 Hz, UK standard)
3. Enable **display artifacts** if your emulator supports it
4. Set CPU speed to **3.25 MHz** (normal, not turbo)
5. If possible, apply a **CRT shader** for that warm cathode-ray glow
6. Make yourself a cup of tea
7. Sit too close to the telly
8. Remember that each keypress is an adventure

```
  _________________________________
 |  _____________________________  |
 | |                             | |
 | |  +-+-+-+-+-+-+-+-+          | |
 | | 8|r|n|b|q|k|b|n|r|         | |
 | |  +-+-+-+-+-+-+-+-+          | |
 | | 7|p|p|p|p|p|p|p|p|         | |
 | |  +-+-+-+-+-+-+-+-+          | |
 | | 6|.|.|.|.|.|.|.|.|         | |
 | |  +-+-+-+-+-+-+-+-+          | |
 | |                             | |
 | |     YOUR MOVE? _            | |
 | |_____________________________| |
 |_________________________________|
 |                                 |
 |  (  A 1983 TELEVISION SET  )   |
 |_________________________________|

```
