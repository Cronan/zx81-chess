# ZX81 Chess Web Emulator - Debugging Prompt

## Problem Summary

A JavaScript ZX81 emulator running a 1K chess game works correctly in the Python test harness but fails in the web UI. Keys are delivered to the emulator, but moves don't get processed.

## Repository Structure

```
/home/user/zx81-chess/
├── play/
│   ├── index.html      # Web UI with touch keyboard
│   ├── z80.js          # Z80 CPU emulator
│   └── zx81.js         # ZX81 system emulation (display, keyboard)
├── test_harness.py     # Working Python implementation (reference)
├── chess.p             # The chess program binary
└── chess.bin           # Raw binary
```

## What Works

- All 16 tests pass using the Python test harness
- Board displays correctly in web UI
- Keys are buffered and delivered to LAST_K (0x4025)
- CPU reads the correct key values (confirmed via debugging)
- Characters are echoed on screen (typing "E2E4" shows "E2E4" after the "?")

## What Doesn't Work

- After entering a 4-character move (e.g., E2E4), the computer never "thinks"
- PC stays at 0x423D (wait_key loop), peak only reaches 0x424B
- Board never updates with the move
- The chess program accepts the input but doesn't process it as a valid move

## Key Technical Details

### Memory Map

| Address | Name | Description |
|---------|------|-------------|
| 0x4009 | Start of .P file | Where chess.p is loaded |
| 0x4025-0x4026 | LAST_K | Last key pressed (2 bytes) |
| 0x400C-0x400D | D_FILE | Display file pointer |
| 0x400E-0x400F | DF_CC | Display file cursor |
| 0x4082 | Board data | Chess piece data tables |
| 0x40EF | Entry point | Where code execution starts |
| 0x423C | HALT instruction | In wait_key loop |
| 0x423D | After HALT | PC value when waiting for input |

### Character Codes (ZX81)

```
Digits: '0'=0x1C, '1'=0x1D, '2'=0x1E, '3'=0x1F, '4'=0x20, '5'=0x21, '6'=0x22, '7'=0x23, '8'=0x24
Letters: 'A'=0x26, 'B'=0x27, 'C'=0x28, 'D'=0x29, 'E'=0x2A, 'F'=0x2B, 'G'=0x2C, 'H'=0x2D
NEWLINE: 0x76
```

For move E2E4: `[0x2A, 0x1E, 0x2A, 0x20]`

### LAST_K Handling in Test Harness (Working)

```python
# From test_harness.py lines 185-191
def handle_halt(self):
    """HALT - simulate frame + keyboard."""
    if self.key_queue:
        key = self.key_queue.pop(0)
        self.ww(0x4025, key)  # Write as WORD - key in low byte, 0 in high byte
    else:
        self.ww(0x4025, 0xFFFF)  # No key = 0xFFFF (both bytes)
```

### LAST_K Handling in Web UI (Current - v7)

```javascript
// From index.html runFrame()
if (result === 'halt') {
    const key = zx81.getKey();
    if (key !== 0xFF) {
        cpu.ww(0x4025, key);  // Write as WORD
    } else {
        cpu.ww(0x4025, 0xFFFF);  // No key
    }
    cpu.halted = false;
    hitHalt = true;
    break;
}
```

### Test Harness Execution Model (Key Difference!)

```python
# Test harness does NOT break on HALT - it continues in same loop
def run(self, start_pc, stop_on_halt_no_keys=False):
    while self.cycles < self.max_cycles:
        op = self.fetch()
        # ... handle instruction ...

        if op == 0x76:  # HALT opcode
            self.handle_halt()  # Writes key to LAST_K immediately
            # Execution continues - NO BREAK
            if not self.key_queue and self.rb(0x4025) == 0xFF:
                if stop_on_halt_no_keys:
                    return "halt_no_keys"
        # ... continues to next instruction ...
```

### Web UI Execution Model

```javascript
// Web UI BREAKS on HALT and resumes next frame
for (let i = 0; i < 100000 && running; i++) {
    const result = cpu.step();
    if (result === 'halt') {
        // Write key to LAST_K
        cpu.ww(0x4025, key);
        cpu.halted = false;
        hitHalt = true;
        break;  // <-- BREAKS OUT, resumes next setInterval tick
    }
}
```

## Debugging Observations

1. **Peak PC only reaches 0x424B** - just 9 bytes past wait_key at 0x4242
2. **Program flow**: read key → echo character → return to wait_key
3. **After 4 characters**: should validate move and enter thinking (many CPU cycles without HALT)
4. **This never happens** - program just waits for more input
5. **Keys are correctly read**: LastRead debug showed correct values (0x2A, 0x1E, etc.)

## Hypotheses

### 1. Execution Model Difference
The test harness doesn't break on HALT - it handles it inline and continues executing. The web UI breaks on HALT and resumes next frame (50ms later). This timing difference might matter.

### 2. Missing System Variable Initialization
The test harness may initialize system variables that we're missing. Check test_harness.py for any `wb` or `ww` calls during setup.

### 3. Frame Timing
The test harness runs continuously until completion. The web UI runs in 50ms chunks with setInterval. The chess program might have timing-sensitive code.

### 4. Instruction Count Per Frame
We run up to 100,000 instructions per frame before breaking on HALT. The test harness has no such limit within a run.

## Files to Examine

1. **test_harness.py** - Lines 185-210 (halt handling), lines 700-750 (test setup)
2. **play/index.html** - Lines 224-295 (runFrame function)
3. **play/z80.js** - HALT handling, step() function
4. **play/zx81.js** - Keyboard handling, system initialization

## Current Code State (v7)

### index.html - runFrame()
```javascript
function runFrame() {
    if (!running) return false;

    let hitHalt = false;
    let instructions = 0;
    let maxPc = 0, minPc = 0xFFFF;

    for (let i = 0; i < 100000 && running; i++) {
        if (cpu.pc === 0) { running = false; break; }
        if (cpu.pc > maxPc) maxPc = cpu.pc;
        if (cpu.pc < minPc) minPc = cpu.pc;
        const result = cpu.step();
        instructions++;

        if (result === 'halt') {
            const key = zx81.getKey();
            if (key !== 0xFF) {
                cpu.ww(0x4025, key);
            } else {
                cpu.ww(0x4025, 0xFFFF);
            }
            cpu.halted = false;
            hitHalt = true;
            break;
        }
        if (result === 'error') {
            running = false;
            statusMessage = 'Error at $' + cpu.pc.toString(16);
            break;
        }
    }

    // ... rest of frame handling (render, status update, etc.)
}
```

### index.html - start()
```javascript
function start() {
    // ... setup ...
    cpu.sp = 0x43FF;
    cpu.pc = 0x40EF;  // Entry point
    cpu.ww(0x4025, 0xFFFF);  // LAST_K = no key

    runFrame();
    frameInterval = setInterval(runFrame, 50);
}
```

### index.html - sendMoveToEmulator()
```javascript
function sendMoveToEmulator() {
    if (inputBuffer.length !== 4) return;

    let codes = [];
    for (const char of inputBuffer) {
        const code = zx81.keyMap[char];
        if (code !== undefined) {
            zx81.keyBuffer.push(code);
            codes.push(code.toString(16));
        }
    }
    lastSentCodes = `${inputBuffer}=[${codes.join(',')}]`;
    peakMaxPc = 0;

    inputBuffer = '';
    updateInputDisplay();
}
```

## Goal

Make the web UI process moves correctly so that after typing E2E4 and pressing SEND:

1. The move is validated by the chess program
2. Computer enters "thinking" mode (PC goes much higher, no HALTs for many cycles)
3. Computer makes a response move
4. Board redraws showing both moves

## Quick Test

1. Open the web UI
2. Click "Start Game" - board should display
3. Type E2E4 using touch keyboard or physical keyboard
4. Press SEND
5. Watch the debug line - peak should go much higher than 424b if move is processed
6. Status should show "Computer thinking..." if working correctly
