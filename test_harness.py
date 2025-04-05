#!/usr/bin/env python3
"""
ZX81 1K Chess - Z80 Test Harness

A minimal Z80 CPU emulator that runs the chess binary and verifies
the board initialisation, display output, and computer AI work.

This is NOT a full ZX81 emulator. It emulates just enough of the
Z80 instruction set and ZX81 ROM to test the chess program:
  - Z80 CPU core (subset of instructions used by the chess code)
  - RST $10 intercepted to capture display output
  - ROM CLS ($0A2A) intercepted
  - HALT intercepted (simulates keyboard input)
  - System variables at $4000-$407C

Usage: python3 test_harness.py [--play]
  Default: runs init + display, shows board, then plays one computer move
  --play: interactive mode (type moves like E2E4)
"""

import sys
import struct

# --- ZX81 Character Set Decoding ---
ZX81_CHARS = {
    0x00: ' ', 0x0B: '"', 0x0C: '£', 0x0D: '$', 0x0E: ':',
    0x0F: '?', 0x10: '(', 0x11: ')', 0x12: '>', 0x13: '<',
    0x14: '=', 0x15: '+', 0x16: '-', 0x17: '*', 0x18: '/',
    0x19: ';', 0x1A: ',', 0x1B: '.', 0x76: '\n',
}
# digits 0-9
for i in range(10):
    ZX81_CHARS[0x1C + i] = str(i)
# letters A-Z
for i in range(26):
    ZX81_CHARS[0x26 + i] = chr(65 + i)
# Inverse video: same but lowercase (visual distinction)
for code in range(0x00, 0x40):
    if code in ZX81_CHARS:
        ch = ZX81_CHARS[code]
        if ch.isalpha():
            ZX81_CHARS[code | 0x80] = ch.lower()  # inverse = lowercase
        else:
            ZX81_CHARS[code | 0x80] = ch

def zx81_char(code):
    return ZX81_CHARS.get(code & 0xFF, '?')

# --- Z80 CPU Emulator (minimal subset) ---
class Z80:
    def __init__(self):
        # Main registers
        self.a = self.f = 0
        self.b = self.c = self.d = self.e = self.h = self.l = 0
        self.sp = 0x43FF  # Stack at top of 1K RAM
        self.pc = 0
        self.ix = self.iy = 0
        # Memory: 64K address space
        self.mem = bytearray(65536)
        # State
        self.halted = False
        self.cycles = 0
        self.max_cycles = 50_000_000  # safety limit
        # Display capture
        self.display_output = []
        self.display_line = []
        # Keyboard input queue
        self.key_queue = []
        # Flags
        self.FLAG_C = 0x01
        self.FLAG_N = 0x02
        self.FLAG_PV = 0x04
        self.FLAG_H = 0x10
        self.FLAG_Z = 0x40
        self.FLAG_S = 0x80

    def load_binary(self, data, addr):
        for i, b in enumerate(data):
            self.mem[addr + i] = b

    def rb(self, addr):
        return self.mem[addr & 0xFFFF]

    def wb(self, addr, val):
        self.mem[addr & 0xFFFF] = val & 0xFF

    def rw(self, addr):
        return self.rb(addr) | (self.rb(addr + 1) << 8)

    def ww(self, addr, val):
        self.wb(addr, val & 0xFF)
        self.wb(addr + 1, (val >> 8) & 0xFF)

    def push(self, val):
        self.sp = (self.sp - 2) & 0xFFFF
        self.ww(self.sp, val)

    def pop(self):
        val = self.rw(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        return val

    def hl(self): return (self.h << 8) | self.l
    def set_hl(self, v): self.h = (v >> 8) & 0xFF; self.l = v & 0xFF
    def bc(self): return (self.b << 8) | self.c
    def set_bc(self, v): self.b = (v >> 8) & 0xFF; self.c = v & 0xFF
    def de(self): return (self.d << 8) | self.e
    def set_de(self, v): self.d = (v >> 8) & 0xFF; self.e = v & 0xFF

    def get_flag(self, flag):
        return bool(self.f & flag)

    def set_flags_sz(self, val):
        """Set Sign and Zero flags based on 8-bit value."""
        val &= 0xFF
        self.f &= ~(self.FLAG_S | self.FLAG_Z)
        if val == 0:
            self.f |= self.FLAG_Z
        if val & 0x80:
            self.f |= self.FLAG_S

    def set_flags_logic(self, val):
        """Set flags after AND/OR/XOR."""
        val &= 0xFF
        self.f = 0
        if val == 0:
            self.f |= self.FLAG_Z
        if val & 0x80:
            self.f |= self.FLAG_S
        # P/V = parity
        if bin(val).count('1') % 2 == 0:
            self.f |= self.FLAG_PV

    def set_flags_add(self, a, b, carry=0):
        """Set flags after addition."""
        result = a + b + carry
        val = result & 0xFF
        self.f = 0
        if val == 0:
            self.f |= self.FLAG_Z
        if val & 0x80:
            self.f |= self.FLAG_S
        if result > 0xFF:
            self.f |= self.FLAG_C
        if ((a ^ b ^ 0x80) & (a ^ result)) & 0x80:
            self.f |= self.FLAG_PV
        if (a & 0x0F) + (b & 0x0F) + carry > 0x0F:
            self.f |= self.FLAG_H
        return val

    def set_flags_sub(self, a, b, carry=0):
        """Set flags after subtraction."""
        result = a - b - carry
        val = result & 0xFF
        self.f = self.FLAG_N
        if val == 0:
            self.f |= self.FLAG_Z
        if val & 0x80:
            self.f |= self.FLAG_S
        if result < 0:
            self.f |= self.FLAG_C
        if ((a ^ b) & (a ^ result)) & 0x80:
            self.f |= self.FLAG_PV
        if (a & 0x0F) < (b & 0x0F) + carry:
            self.f |= self.FLAG_H
        return val

    def set_flags_cp(self, a, b):
        """Set flags for CP (compare) - same as SUB but don't store result."""
        self.set_flags_sub(a, b)

    def handle_rst10(self):
        """RST $10 - ZX81 print character. Capture to display."""
        ch = zx81_char(self.a)
        if ch == '\n':
            self.display_output.append(''.join(self.display_line))
            self.display_line = []
        else:
            self.display_line.append(ch)

    def handle_cls(self):
        """ROM CLS - clear display."""
        self.display_output = []
        self.display_line = []
        # Set D_FILE to point to a display file area
        self.ww(0x400C, 0x4800)  # D_FILE points to safe area
        self.ww(0x400E, 0x4801)  # DF_CC

    def handle_halt(self):
        """HALT - simulate frame + keyboard."""
        if self.key_queue:
            key = self.key_queue.pop(0)
            self.ww(0x4025, key)  # LAST_K
        else:
            self.ww(0x4025, 0xFFFF)  # No key

    def fetch(self):
        b = self.rb(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return b

    def fetch_word(self):
        lo = self.fetch()
        hi = self.fetch()
        return (hi << 8) | lo

    def signed_byte(self, b):
        return b if b < 128 else b - 256

    def run(self, start_pc, stop_on_halt_no_keys=False):
        """Execute from start_pc until RET to sentinel address, HALT with no keys, or cycle limit."""
        self.pc = start_pc
        initial_sp = self.sp

        while self.cycles < self.max_cycles:
            self.cycles += 1

            # Stop if we returned to sentinel address 0x0000
            if self.pc == 0x0000:
                return "returned"

            # Intercept known ROM addresses
            if self.pc == 0x0010:  # RST $10
                self.handle_rst10()
                ret_addr = self.pop()
                self.pc = ret_addr
                continue
            if self.pc == 0x0A2A:  # ROM CLS
                self.handle_cls()
                ret_addr = self.pop()
                self.pc = ret_addr
                continue

            op = self.fetch()

            # Trace output if enabled
            if getattr(self, '_trace', False) and getattr(self, '_trace_count', 0) < getattr(self, '_trace_limit', 500):
                self._trace_count += 1
                # Only trace interesting instructions (CP 64, BIT 3, and when A has black piece)
                pc_minus1 = (self.pc - 1) & 0xFFFF
                if op == 0xFE or (op == 0xA7 and self.a >= 0x08) or (op == 0xCB) or pc_minus1 < 0x42A0:
                    print(f"    ${pc_minus1:04X}: op={op:02X} A={self.a:02X} DE={self.d:02X}{self.e:02X} HL={self.h:02X}{self.l:02X} SP={self.sp:04X} F={self.f:02X}")

            # --- NOP ---
            if op == 0x00:
                pass

            # --- LD r, n (8-bit immediate) ---
            elif op == 0x3E: self.a = self.fetch()
            elif op == 0x06: self.b = self.fetch()
            elif op == 0x0E: self.c = self.fetch()
            elif op == 0x16: self.d = self.fetch()
            elif op == 0x1E: self.e = self.fetch()
            elif op == 0x26: self.h = self.fetch()
            elif op == 0x2E: self.l = self.fetch()

            # --- LD r, r ---
            elif op == 0x7F: pass  # LD A, A
            elif op == 0x78: self.a = self.b
            elif op == 0x79: self.a = self.c
            elif op == 0x7A: self.a = self.d
            elif op == 0x7B: self.a = self.e
            elif op == 0x7C: self.a = self.h
            elif op == 0x7D: self.a = self.l
            elif op == 0x47: self.b = self.a
            elif op == 0x40: pass  # LD B, B
            elif op == 0x41: self.b = self.c
            elif op == 0x42: self.b = self.d
            elif op == 0x43: self.b = self.e
            elif op == 0x44: self.b = self.h
            elif op == 0x45: self.b = self.l
            elif op == 0x4F: self.c = self.a
            elif op == 0x48: self.c = self.b
            elif op == 0x4A: self.c = self.d
            elif op == 0x4B: self.c = self.e
            elif op == 0x4C: self.c = self.h
            elif op == 0x4D: self.c = self.l
            elif op == 0x57: self.d = self.a
            elif op == 0x50: self.d = self.b
            elif op == 0x51: self.d = self.c
            elif op == 0x53: self.d = self.e
            elif op == 0x54: self.d = self.h
            elif op == 0x55: self.d = self.l
            elif op == 0x5F: self.e = self.a
            elif op == 0x58: self.e = self.b
            elif op == 0x59: self.e = self.c
            elif op == 0x5A: self.e = self.d
            elif op == 0x5C: self.e = self.h
            elif op == 0x5D: self.e = self.l
            elif op == 0x67: self.h = self.a
            elif op == 0x60: self.h = self.b
            elif op == 0x61: self.h = self.c
            elif op == 0x62: self.h = self.d
            elif op == 0x63: self.h = self.e
            elif op == 0x65: self.h = self.l
            elif op == 0x6F: self.l = self.a
            elif op == 0x68: self.l = self.b
            elif op == 0x69: self.l = self.c
            elif op == 0x6A: self.l = self.d
            elif op == 0x6B: self.l = self.e
            elif op == 0x6C: self.l = self.h

            # --- LD r, (HL) ---
            elif op == 0x7E: self.a = self.rb(self.hl())
            elif op == 0x46: self.b = self.rb(self.hl())
            elif op == 0x4E: self.c = self.rb(self.hl())
            elif op == 0x56: self.d = self.rb(self.hl())
            elif op == 0x5E: self.e = self.rb(self.hl())
            elif op == 0x66: self.h = self.rb(self.hl()); # careful: reads H from (HL) before H changes
            elif op == 0x6E: self.l = self.rb(self.hl())

            # --- LD (HL), r ---
            elif op == 0x77: self.wb(self.hl(), self.a)
            elif op == 0x70: self.wb(self.hl(), self.b)
            elif op == 0x71: self.wb(self.hl(), self.c)
            elif op == 0x72: self.wb(self.hl(), self.d)
            elif op == 0x73: self.wb(self.hl(), self.e)
            elif op == 0x74: self.wb(self.hl(), self.h)
            elif op == 0x75: self.wb(self.hl(), self.l)

            # --- LD (HL), n ---
            elif op == 0x36: self.wb(self.hl(), self.fetch())

            # --- LD A, (DE) ---
            elif op == 0x1A: self.a = self.rb(self.de())
            # --- LD A, (BC) ---
            elif op == 0x0A: self.a = self.rb(self.bc())
            # --- LD (DE), A ---
            elif op == 0x12: self.wb(self.de(), self.a)
            # --- LD A, (nn) ---
            elif op == 0x3A: self.a = self.rb(self.fetch_word())
            # --- LD (nn), A ---
            elif op == 0x32: self.wb(self.fetch_word(), self.a)

            # --- LD rr, nn (16-bit immediate) ---
            elif op == 0x01: v = self.fetch_word(); self.set_bc(v)
            elif op == 0x11: v = self.fetch_word(); self.set_de(v)
            elif op == 0x21: v = self.fetch_word(); self.set_hl(v)
            elif op == 0x31: self.sp = self.fetch_word()

            # --- LD HL, (nn) ---
            elif op == 0x2A: addr = self.fetch_word(); self.set_hl(self.rw(addr))
            # --- LD (nn), HL ---
            elif op == 0x22: addr = self.fetch_word(); self.ww(addr, self.hl())

            # --- LD SP, HL ---
            elif op == 0xF9: self.sp = self.hl()

            # --- PUSH/POP ---
            elif op == 0xC5: self.push(self.bc())
            elif op == 0xD5: self.push(self.de())
            elif op == 0xE5: self.push(self.hl())
            elif op == 0xF5: self.push((self.a << 8) | self.f)
            elif op == 0xC1: self.set_bc(self.pop())
            elif op == 0xD1: self.set_de(self.pop())
            elif op == 0xE1: self.set_hl(self.pop())
            elif op == 0xF1: v = self.pop(); self.a = (v >> 8) & 0xFF; self.f = v & 0xFF

            # --- EX DE, HL ---
            elif op == 0xEB:
                self.d, self.h = self.h, self.d
                self.e, self.l = self.l, self.e

            # --- ADD A, r ---
            elif op == 0x87: self.a = self.set_flags_add(self.a, self.a)
            elif op == 0x80: self.a = self.set_flags_add(self.a, self.b)
            elif op == 0x81: self.a = self.set_flags_add(self.a, self.c)
            elif op == 0x82: self.a = self.set_flags_add(self.a, self.d)
            elif op == 0x83: self.a = self.set_flags_add(self.a, self.e)
            elif op == 0x84: self.a = self.set_flags_add(self.a, self.h)
            elif op == 0x85: self.a = self.set_flags_add(self.a, self.l)
            elif op == 0x86: self.a = self.set_flags_add(self.a, self.rb(self.hl()))
            # --- ADD A, n ---
            elif op == 0xC6: self.a = self.set_flags_add(self.a, self.fetch())

            # --- ADD HL, rr ---
            elif op == 0x09:
                result = self.hl() + self.bc()
                self.f &= ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)
                if result > 0xFFFF: self.f |= self.FLAG_C
                self.set_hl(result & 0xFFFF)
            elif op == 0x19:
                result = self.hl() + self.de()
                self.f &= ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)
                if result > 0xFFFF: self.f |= self.FLAG_C
                self.set_hl(result & 0xFFFF)
            elif op == 0x29:
                result = self.hl() + self.hl()
                self.f &= ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)
                if result > 0xFFFF: self.f |= self.FLAG_C
                self.set_hl(result & 0xFFFF)
            elif op == 0x39:
                result = self.hl() + self.sp
                self.f &= ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)
                if result > 0xFFFF: self.f |= self.FLAG_C
                self.set_hl(result & 0xFFFF)

            # --- SUB r ---
            elif op == 0x97: self.a = self.set_flags_sub(self.a, self.a)
            elif op == 0x90: self.a = self.set_flags_sub(self.a, self.b)
            elif op == 0x91: self.a = self.set_flags_sub(self.a, self.c)
            elif op == 0x92: self.a = self.set_flags_sub(self.a, self.d)
            elif op == 0x93: self.a = self.set_flags_sub(self.a, self.e)
            elif op == 0x94: self.a = self.set_flags_sub(self.a, self.h)
            elif op == 0x95: self.a = self.set_flags_sub(self.a, self.l)
            elif op == 0x96: self.a = self.set_flags_sub(self.a, self.rb(self.hl()))
            # --- SUB n ---
            elif op == 0xD6: self.a = self.set_flags_sub(self.a, self.fetch())

            # --- AND r ---
            elif op == 0xA7: self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA0: self.a &= self.b; self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA1: self.a &= self.c; self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA2: self.a &= self.d; self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA3: self.a &= self.e; self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA4: self.a &= self.h; self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA5: self.a &= self.l; self.set_flags_logic(self.a); self.f |= self.FLAG_H
            elif op == 0xA6: self.a &= self.rb(self.hl()); self.set_flags_logic(self.a); self.f |= self.FLAG_H
            # --- AND n ---
            elif op == 0xE6: self.a &= self.fetch(); self.set_flags_logic(self.a); self.f |= self.FLAG_H

            # --- OR r ---
            elif op == 0xB7: self.set_flags_logic(self.a)
            elif op == 0xB0: self.a |= self.b; self.set_flags_logic(self.a)
            elif op == 0xB1: self.a |= self.c; self.set_flags_logic(self.a)
            elif op == 0xB2: self.a |= self.d; self.set_flags_logic(self.a)
            elif op == 0xB3: self.a |= self.e; self.set_flags_logic(self.a)
            elif op == 0xB4: self.a |= self.h; self.set_flags_logic(self.a)
            elif op == 0xB5: self.a |= self.l; self.set_flags_logic(self.a)
            elif op == 0xB6: self.a |= self.rb(self.hl()); self.set_flags_logic(self.a)
            # --- OR n ---
            elif op == 0xF6: self.a |= self.fetch(); self.set_flags_logic(self.a)

            # --- XOR r ---
            elif op == 0xAF: self.a = 0; self.set_flags_logic(0)  # XOR A = 0
            elif op == 0xA8: self.a ^= self.b; self.set_flags_logic(self.a)
            elif op == 0xA9: self.a ^= self.c; self.set_flags_logic(self.a)
            elif op == 0xAA: self.a ^= self.d; self.set_flags_logic(self.a)
            elif op == 0xAB: self.a ^= self.e; self.set_flags_logic(self.a)
            elif op == 0xAC: self.a ^= self.h; self.set_flags_logic(self.a)
            elif op == 0xAD: self.a ^= self.l; self.set_flags_logic(self.a)
            elif op == 0xAE: self.a ^= self.rb(self.hl()); self.set_flags_logic(self.a)
            # --- XOR n ---
            elif op == 0xEE: self.a ^= self.fetch(); self.set_flags_logic(self.a)

            # --- CP r ---
            elif op == 0xBF: self.set_flags_cp(self.a, self.a)
            elif op == 0xB8: self.set_flags_cp(self.a, self.b)
            elif op == 0xB9: self.set_flags_cp(self.a, self.c)
            elif op == 0xBA: self.set_flags_cp(self.a, self.d)
            elif op == 0xBB: self.set_flags_cp(self.a, self.e)
            elif op == 0xBC: self.set_flags_cp(self.a, self.h)
            elif op == 0xBD: self.set_flags_cp(self.a, self.l)
            elif op == 0xBE: self.set_flags_cp(self.a, self.rb(self.hl()))
            # --- CP n ---
            elif op == 0xFE: self.set_flags_cp(self.a, self.fetch())

            # --- INC r ---
            elif op == 0x3C: self.a = (self.a + 1) & 0xFF; self.set_flags_sz(self.a)
            elif op == 0x04: self.b = (self.b + 1) & 0xFF; self.set_flags_sz(self.b)
            elif op == 0x0C: self.c = (self.c + 1) & 0xFF; self.set_flags_sz(self.c)
            elif op == 0x14: self.d = (self.d + 1) & 0xFF; self.set_flags_sz(self.d)
            elif op == 0x1C: self.e = (self.e + 1) & 0xFF; self.set_flags_sz(self.e)
            elif op == 0x24: self.h = (self.h + 1) & 0xFF; self.set_flags_sz(self.h)
            elif op == 0x2C: self.l = (self.l + 1) & 0xFF; self.set_flags_sz(self.l)
            elif op == 0x34: v = (self.rb(self.hl()) + 1) & 0xFF; self.wb(self.hl(), v); self.set_flags_sz(v)

            # --- DEC r ---
            elif op == 0x3D: self.a = (self.a - 1) & 0xFF; self.set_flags_sz(self.a); self.f |= self.FLAG_N
            elif op == 0x05: self.b = (self.b - 1) & 0xFF; self.set_flags_sz(self.b); self.f |= self.FLAG_N
            elif op == 0x0D: self.c = (self.c - 1) & 0xFF; self.set_flags_sz(self.c); self.f |= self.FLAG_N
            elif op == 0x15: self.d = (self.d - 1) & 0xFF; self.set_flags_sz(self.d); self.f |= self.FLAG_N
            elif op == 0x1D: self.e = (self.e - 1) & 0xFF; self.set_flags_sz(self.e); self.f |= self.FLAG_N
            elif op == 0x25: self.h = (self.h - 1) & 0xFF; self.set_flags_sz(self.h); self.f |= self.FLAG_N
            elif op == 0x2D: self.l = (self.l - 1) & 0xFF; self.set_flags_sz(self.l); self.f |= self.FLAG_N
            elif op == 0x35: v = (self.rb(self.hl()) - 1) & 0xFF; self.wb(self.hl(), v); self.set_flags_sz(v); self.f |= self.FLAG_N

            # --- INC rr ---
            elif op == 0x03: self.set_bc((self.bc() + 1) & 0xFFFF)
            elif op == 0x13: self.set_de((self.de() + 1) & 0xFFFF)
            elif op == 0x23: self.set_hl((self.hl() + 1) & 0xFFFF)
            elif op == 0x33: self.sp = (self.sp + 1) & 0xFFFF

            # --- DEC rr ---
            elif op == 0x0B: self.set_bc((self.bc() - 1) & 0xFFFF)
            elif op == 0x1B: self.set_de((self.de() - 1) & 0xFFFF)
            elif op == 0x2B: self.set_hl((self.hl() - 1) & 0xFFFF)
            elif op == 0x3B: self.sp = (self.sp - 1) & 0xFFFF

            # --- RLCA ---
            elif op == 0x07:
                carry = (self.a >> 7) & 1
                self.a = ((self.a << 1) | carry) & 0xFF
                self.f = (self.f & ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)) | (carry * self.FLAG_C)

            # --- RRCA ---
            elif op == 0x0F:
                carry = self.a & 1
                self.a = ((self.a >> 1) | (carry << 7)) & 0xFF
                self.f = (self.f & ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)) | (carry * self.FLAG_C)

            # --- JP nn ---
            elif op == 0xC3: self.pc = self.fetch_word()
            elif op == 0xCA:  # JP Z
                addr = self.fetch_word()
                if self.get_flag(self.FLAG_Z): self.pc = addr
            elif op == 0xC2:  # JP NZ
                addr = self.fetch_word()
                if not self.get_flag(self.FLAG_Z): self.pc = addr
            elif op == 0xDA:  # JP C
                addr = self.fetch_word()
                if self.get_flag(self.FLAG_C): self.pc = addr
            elif op == 0xD2:  # JP NC
                addr = self.fetch_word()
                if not self.get_flag(self.FLAG_C): self.pc = addr

            # --- JR e ---
            elif op == 0x18:
                offset = self.signed_byte(self.fetch())
                self.pc = (self.pc + offset) & 0xFFFF
            elif op == 0x28:  # JR Z
                offset = self.signed_byte(self.fetch())
                if self.get_flag(self.FLAG_Z): self.pc = (self.pc + offset) & 0xFFFF
            elif op == 0x20:  # JR NZ
                offset = self.signed_byte(self.fetch())
                if not self.get_flag(self.FLAG_Z): self.pc = (self.pc + offset) & 0xFFFF
            elif op == 0x38:  # JR C
                offset = self.signed_byte(self.fetch())
                if self.get_flag(self.FLAG_C): self.pc = (self.pc + offset) & 0xFFFF
            elif op == 0x30:  # JR NC
                offset = self.signed_byte(self.fetch())
                if not self.get_flag(self.FLAG_C): self.pc = (self.pc + offset) & 0xFFFF

            # --- DJNZ ---
            elif op == 0x10:
                offset = self.signed_byte(self.fetch())
                self.b = (self.b - 1) & 0xFF
                if self.b != 0:
                    self.pc = (self.pc + offset) & 0xFFFF

            # --- CALL nn ---
            elif op == 0xCD:
                addr = self.fetch_word()
                self.push(self.pc)
                self.pc = addr
            elif op == 0xCC:  # CALL Z
                addr = self.fetch_word()
                if self.get_flag(self.FLAG_Z): self.push(self.pc); self.pc = addr
            elif op == 0xC4:  # CALL NZ
                addr = self.fetch_word()
                if not self.get_flag(self.FLAG_Z): self.push(self.pc); self.pc = addr
            elif op == 0xDC:  # CALL C
                addr = self.fetch_word()
                if self.get_flag(self.FLAG_C): self.push(self.pc); self.pc = addr
            elif op == 0xD4:  # CALL NC
                addr = self.fetch_word()
                if not self.get_flag(self.FLAG_C): self.push(self.pc); self.pc = addr

            # --- RET ---
            elif op == 0xC9: self.pc = self.pop()
            elif op == 0xC8:  # RET Z
                if self.get_flag(self.FLAG_Z): self.pc = self.pop()
            elif op == 0xC0:  # RET NZ
                if not self.get_flag(self.FLAG_Z): self.pc = self.pop()
            elif op == 0xD8:  # RET C
                if self.get_flag(self.FLAG_C): self.pc = self.pop()
            elif op == 0xD0:  # RET NC
                if not self.get_flag(self.FLAG_C): self.pc = self.pop()

            # --- RST ---
            elif op == 0xC7: self.push(self.pc); self.pc = 0x00
            elif op == 0xCF: self.push(self.pc); self.pc = 0x08
            elif op == 0xD7: self.push(self.pc); self.pc = 0x10  # RST $10
            elif op == 0xDF: self.push(self.pc); self.pc = 0x18
            elif op == 0xE7: self.push(self.pc); self.pc = 0x20
            elif op == 0xEF: self.push(self.pc); self.pc = 0x28
            elif op == 0xF7: self.push(self.pc); self.pc = 0x30
            elif op == 0xFF: self.push(self.pc); self.pc = 0x38

            # --- HALT ---
            elif op == 0x76:
                self.handle_halt()
                if not self.key_queue and self.rb(0x4025) == 0xFF:
                    if stop_on_halt_no_keys:
                        return "halt_no_keys"

            # --- CB prefix (bit operations) ---
            elif op == 0xCB:
                cb_op = self.fetch()
                # BIT b, r
                if cb_op & 0xC0 == 0x40:
                    bit_num = (cb_op >> 3) & 7
                    reg_idx = cb_op & 7
                    val = [self.b, self.c, self.d, self.e, self.h, self.l, self.rb(self.hl()), self.a][reg_idx]
                    self.f = (self.f & self.FLAG_C) | self.FLAG_H
                    if not (val & (1 << bit_num)):
                        self.f |= self.FLAG_Z
                # SET b, r
                elif cb_op & 0xC0 == 0xC0:
                    bit_num = (cb_op >> 3) & 7
                    reg_idx = cb_op & 7
                    regs = [self.b, self.c, self.d, self.e, self.h, self.l, self.rb(self.hl()), self.a]
                    val = regs[reg_idx] | (1 << bit_num)
                    if reg_idx == 0: self.b = val
                    elif reg_idx == 1: self.c = val
                    elif reg_idx == 2: self.d = val
                    elif reg_idx == 3: self.e = val
                    elif reg_idx == 4: self.h = val
                    elif reg_idx == 5: self.l = val
                    elif reg_idx == 6: self.wb(self.hl(), val)
                    elif reg_idx == 7: self.a = val
                # RES b, r
                elif cb_op & 0xC0 == 0x80:
                    bit_num = (cb_op >> 3) & 7
                    reg_idx = cb_op & 7
                    regs = [self.b, self.c, self.d, self.e, self.h, self.l, self.rb(self.hl()), self.a]
                    val = regs[reg_idx] & ~(1 << bit_num)
                    if reg_idx == 0: self.b = val
                    elif reg_idx == 1: self.c = val
                    elif reg_idx == 2: self.d = val
                    elif reg_idx == 3: self.e = val
                    elif reg_idx == 4: self.h = val
                    elif reg_idx == 5: self.l = val
                    elif reg_idx == 6: self.wb(self.hl(), val)
                    elif reg_idx == 7: self.a = val
                # SRL r
                elif cb_op & 0xF8 == 0x38:
                    reg_idx = cb_op & 7
                    regs = [self.b, self.c, self.d, self.e, self.h, self.l, self.rb(self.hl()), self.a]
                    val = regs[reg_idx]
                    carry = val & 1
                    val = (val >> 1) & 0xFF
                    self.f = (carry * self.FLAG_C)
                    if val == 0: self.f |= self.FLAG_Z
                    if reg_idx == 0: self.b = val
                    elif reg_idx == 1: self.c = val
                    elif reg_idx == 2: self.d = val
                    elif reg_idx == 3: self.e = val
                    elif reg_idx == 4: self.h = val
                    elif reg_idx == 5: self.l = val
                    elif reg_idx == 6: self.wb(self.hl(), val)
                    elif reg_idx == 7: self.a = val
                else:
                    print(f"Unimplemented CB instruction: CB {cb_op:02X} at PC=${self.pc-2:04X}")
                    return "error"

            # --- ED prefix ---
            elif op == 0xED:
                ed_op = self.fetch()
                if ed_op == 0x44:  # NEG
                    old_a = self.a
                    self.a = self.set_flags_sub(0, old_a)
                elif ed_op == 0x4B:  # LD BC, (nn)
                    addr = self.fetch_word()
                    self.set_bc(self.rw(addr))
                elif ed_op == 0x5B:  # LD DE, (nn)
                    addr = self.fetch_word()
                    self.set_de(self.rw(addr))
                elif ed_op == 0x73:  # LD (nn), SP
                    addr = self.fetch_word()
                    self.ww(addr, self.sp)
                elif ed_op == 0x7B:  # LD SP, (nn)
                    addr = self.fetch_word()
                    self.sp = self.rw(addr)
                else:
                    print(f"Unimplemented ED instruction: ED {ed_op:02X} at PC=${self.pc-2:04X}")
                    return "error"

            # --- DD prefix (IX) ---
            elif op == 0xDD:
                dd_op = self.fetch()
                if dd_op == 0x21:  # LD IX, nn
                    self.ix = self.fetch_word()
                elif dd_op == 0xE5:  # PUSH IX
                    self.push(self.ix)
                elif dd_op == 0xE1:  # POP IX
                    self.ix = self.pop()
                elif dd_op == 0x7E:  # LD A, (IX+d)
                    d = self.signed_byte(self.fetch())
                    self.a = self.rb((self.ix + d) & 0xFFFF)
                elif dd_op == 0x46:  # LD B, (IX+d)
                    d = self.signed_byte(self.fetch())
                    self.b = self.rb((self.ix + d) & 0xFFFF)
                elif dd_op == 0x4E:  # LD C, (IX+d)
                    d = self.signed_byte(self.fetch())
                    self.c = self.rb((self.ix + d) & 0xFFFF)
                elif dd_op == 0x56:  # LD D, (IX+d)
                    d = self.signed_byte(self.fetch())
                    self.d = self.rb((self.ix + d) & 0xFFFF)
                elif dd_op == 0x5E:  # LD E, (IX+d)
                    d = self.signed_byte(self.fetch())
                    self.e = self.rb((self.ix + d) & 0xFFFF)
                elif dd_op == 0x19:  # ADD IX, DE
                    result = self.ix + self.de()
                    self.f &= ~(self.FLAG_C | self.FLAG_N | self.FLAG_H)
                    if result > 0xFFFF: self.f |= self.FLAG_C
                    self.ix = result & 0xFFFF
                else:
                    print(f"Unimplemented DD instruction: DD {dd_op:02X} at PC=${self.pc-2:04X}")
                    return "error"

            # --- SCF (Set Carry Flag) ---
            elif op == 0x37:
                self.f = (self.f & (self.FLAG_S | self.FLAG_Z | self.FLAG_PV)) | self.FLAG_C

            # --- CCF (Complement Carry Flag) ---
            elif op == 0x3F:
                self.f ^= self.FLAG_C
                self.f &= ~self.FLAG_N

            # --- CPL (Complement A) ---
            elif op == 0x2F:
                self.a = (~self.a) & 0xFF
                self.f |= self.FLAG_N | self.FLAG_H

            else:
                print(f"Unimplemented instruction: {op:02X} at PC=${self.pc-1:04X}")
                return "error"

        return "cycle_limit"


def setup_zx81_memory(cpu):
    """Initialize ZX81 system variables."""
    cpu.wb(0x4000, 0xFF)       # ERR_NR = no error
    cpu.wb(0x4001, 0x40)       # FLAGS
    cpu.ww(0x4004, 0x43FF)     # RAMTOP
    cpu.ww(0x400C, 0x4800)     # D_FILE (point to safe area)
    cpu.ww(0x400E, 0x4801)     # DF_CC
    cpu.ww(0x4025, 0xFFFF)     # LAST_K = no key
    cpu.wb(0x403B, 0x40)       # CDFLAG = slow mode


def print_board_from_memory(cpu, base=0x4082):
    """Read the chess board directly from memory and display it."""
    piece_chars = {0: '.', 1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}
    print("\n  Board state in memory:")
    print("  +-+-+-+-+-+-+-+-+")
    for rank in range(7, -1, -1):
        row = f" {rank+1}|"
        for file in range(8):
            idx = rank * 8 + file
            piece = cpu.rb(base + idx)
            ptype = piece & 0x07
            is_black = bool(piece & 0x08)
            ch = piece_chars.get(ptype, '?')
            if is_black:
                ch = ch.lower()
            row += ch + '|'
        print(row)
        print("  +-+-+-+-+-+-+-+-+")
    print("   A B C D E F G H")


def encode_key(ch):
    """Convert ASCII character to ZX81 key code."""
    if 'A' <= ch <= 'Z':
        return 0x26 + (ord(ch) - ord('A'))
    if 'a' <= ch <= 'z':
        return 0x26 + (ord(ch) - ord('a'))
    if '1' <= ch <= '8':
        return 0x1D + (ord(ch) - ord('1'))
    return 0xFF


def main():
    interactive = '--play' in sys.argv

    # Load the binary
    try:
        with open('chess.bin', 'rb') as f:
            code = f.read()
    except FileNotFoundError:
        print("ERROR: chess.bin not found. Run: pasmo src/chess.asm chess.bin")
        sys.exit(1)

    print(f"Loaded chess.bin: {len(code)} bytes")

    cpu = Z80()
    setup_zx81_memory(cpu)
    cpu.load_binary(code, 0x4082)

    # The entry point is 'start' label - need to find it.
    # In the binary, board(64) + vars(7) + tables(38) = 109 bytes of data
    # So code starts at 0x4082 + 109 = 0x40EF
    # But the actual entry point calls init_board first.
    # Let's find the start label by looking at the assembled code.
    # The start routine calls init_board then cls_and_draw then enters game_loop.

    # Find the start label: it's the first CALL instruction after the data tables
    # Data: 64 (board) + 7 (vars) + 7 (piece_chars) + 7 (piece_vals) +
    #       8 (king_dirs) + 8 (knight_dirs) + 8 (init_rank) = 109
    start_addr = 0x4082 + 109  # Should be the 'start' label

    # Verify: first bytes at start should be CD xx xx (CALL init_board)
    b0 = cpu.rb(start_addr)
    if b0 != 0xCD:
        print(f"WARNING: Expected CALL (CD) at start_addr ${start_addr:04X}, got ${b0:02X}")
        # Try to find it
        for offset in range(100, 200):
            addr = 0x4082 + offset
            if cpu.rb(addr) == 0xCD:
                print(f"  Found CALL at offset {offset} (${addr:04X})")
                start_addr = addr
                break

    print(f"Entry point: ${start_addr:04X}")

    # --- TEST 1: Run init_board ---
    print("\n=== TEST 1: Board Initialisation ===")

    # Find init_board address from the CALL at start
    init_addr = cpu.rb(start_addr + 1) | (cpu.rb(start_addr + 2) << 8)
    print(f"init_board at: ${init_addr:04X}")

    cpu.push(0x0000)  # Dummy return address (we'll catch RET)
    result = cpu.run(init_addr)

    print_board_from_memory(cpu)

    # Verify board is correct
    expected_rank1 = [4, 2, 3, 5, 6, 3, 2, 4]  # White: RNBQKBNR
    expected_rank2 = [1] * 8                      # White pawns
    expected_rank7 = [9] * 8                      # Black pawns
    expected_rank8 = [12, 10, 11, 13, 14, 11, 10, 12]  # Black: RNBQKBNR

    board_ok = True
    for i in range(8):
        if cpu.rb(0x4082 + i) != expected_rank1[i]:
            print(f"  ERROR: rank 1 file {i}: expected {expected_rank1[i]}, got {cpu.rb(0x4082+i)}")
            board_ok = False
        if cpu.rb(0x4082 + 8 + i) != expected_rank2[i]:
            print(f"  ERROR: rank 2 file {i}: expected {expected_rank2[i]}, got {cpu.rb(0x408A+i)}")
            board_ok = False
        if cpu.rb(0x4082 + 48 + i) != expected_rank7[i]:
            print(f"  ERROR: rank 7 file {i}: expected {expected_rank7[i]}, got {cpu.rb(0x40B2+i)}")
            board_ok = False
        if cpu.rb(0x4082 + 56 + i) != expected_rank8[i]:
            print(f"  ERROR: rank 8 file {i}: expected {expected_rank8[i]}, got {cpu.rb(0x40BA+i)}")
            board_ok = False
    # Check empty squares
    for i in range(16, 48):
        if cpu.rb(0x4082 + i) != 0:
            print(f"  ERROR: square {i} should be empty, got {cpu.rb(0x4082+i)}")
            board_ok = False

    if board_ok:
        print("  PASS: Board initialised correctly!")
    else:
        print("  FAIL: Board has errors")

    # --- TEST 2: Run cls_and_draw ---
    print("\n=== TEST 2: Display Routine ===")

    # Find cls_and_draw address from the second CALL at start+3
    draw_addr = cpu.rb(start_addr + 4) | (cpu.rb(start_addr + 5) << 8)
    print(f"cls_and_draw at: ${draw_addr:04X}")

    cpu.sp = 0x43FF
    cpu.display_output = []
    cpu.display_line = []
    cpu.push(0x0000)
    result = cpu.run(draw_addr)

    if cpu.display_line:
        cpu.display_output.append(''.join(cpu.display_line))

    print("  Display output:")
    for line in cpu.display_output:
        print(f"  |{line}|")

    if any('R' in line and 'K' in line for line in cpu.display_output):
        print("  PASS: Board display contains pieces!")
    else:
        print("  FAIL: No pieces visible in display output")

    # --- TEST 3: Computer AI (think routine) ---
    print("\n=== TEST 3: Computer AI ===")

    # Set side to Black (8)
    cpu.wb(0x40C8, 8)  # side = Black

    # Find the think routine - it's called from the game loop
    # Search for it in the code by looking for the pattern
    # Think is typically called after setting side=8
    # Let's find it by scanning for the address used in the game loop
    # The game loop does: LD A, 8 / LD (side), A / CALL think
    # That's: 3E 08 / 32 C8 40 / CD xx xx
    think_addr = None
    for addr in range(start_addr, start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    if think_addr:
        print(f"think routine at: ${think_addr:04X}")
        cpu.sp = 0x43FF
        cpu.push(0x0000)

        # Check board state before think
        black_pieces = 0
        for sq in range(64):
            p = cpu.rb(0x4082 + sq)
            if p & 0x08:
                black_pieces += 1
        print(f"  DEBUG: Black pieces on board: {black_pieces}")

        # Enable tracing for first N instructions
        cpu.cycles = 0
        cpu._trace = True
        cpu._trace_count = 0
        cpu._trace_limit = 500
        result = cpu.run(think_addr)
        cpu._trace = False
        print(f"  DEBUG: run() returned: {result}, cycles: {cpu.cycles}")

        best_from = cpu.rb(0x40C5)
        best_to = cpu.rb(0x40C6)
        best_score = cpu.rb(0x40C7)

        if best_from < 64 and best_to < 64:
            from_file = chr(ord('a') + (best_from & 7))
            from_rank = (best_from >> 3) + 1
            to_file = chr(ord('a') + (best_to & 7))
            to_rank = (best_to >> 3) + 1
            print(f"  Computer's move: {from_file}{from_rank} -> {to_file}{to_rank} (score: {best_score})")
            print(f"  PASS: Computer found a move!")

            # Execute the move
            piece = cpu.rb(0x4082 + best_from)
            cpu.wb(0x4082 + best_from, 0)
            cpu.wb(0x4082 + best_to, piece)
            print("\n  Board after computer's move:")
            print_board_from_memory(cpu)
        else:
            print(f"  FAIL: No valid move found (from={best_from}, to={best_to})")
    else:
        print("  SKIP: Could not locate think routine")

    # --- Summary ---
    print(f"\n=== Summary ===")
    print(f"Binary size: {len(code)} bytes")
    print(f"Z80 cycles executed: {cpu.cycles:,}")
    print(f"Tests complete.")

    if interactive:
        print("\n=== Interactive Mode ===")
        print("Type moves as file+rank pairs, e.g.: e2e4")
        print("Type 'quit' to exit, 'board' to show board")

        while True:
            print_board_from_memory(cpu)
            try:
                move = input("\nYour move: ").strip().lower()
            except EOFError:
                break
            if move == 'quit':
                break
            if move == 'board':
                continue
            if len(move) != 4:
                print("Enter 4 characters: file rank file rank (e.g. e2e4)")
                continue

            # Parse move
            try:
                ff = ord(move[0]) - ord('a')
                fr = int(move[1]) - 1
                tf = ord(move[2]) - ord('a')
                tr = int(move[3]) - 1
                if not (0 <= ff < 8 and 0 <= fr < 8 and 0 <= tf < 8 and 0 <= tr < 8):
                    raise ValueError
            except (ValueError, IndexError):
                print("Invalid move format")
                continue

            from_sq = fr * 8 + ff
            to_sq = tr * 8 + tf

            # Execute player move
            piece = cpu.rb(0x4082 + from_sq)
            if piece == 0 or (piece & 0x08):
                print("No white piece there!")
                continue
            cpu.wb(0x4082 + from_sq, 0)
            cpu.wb(0x4082 + to_sq, piece)

            print(f"Moved {move[0]}{move[1]} -> {move[2]}{move[3]}")

            # Computer thinks
            if think_addr:
                cpu.wb(0x40C8, 8)  # side = Black
                cpu.sp = 0x43FF
                cpu.push(0x0000)
                cpu.cycles = 0
                cpu.run(think_addr)

                best_from = cpu.rb(0x40C5)
                best_to = cpu.rb(0x40C6)
                if best_from < 64 and best_to < 64:
                    bf = chr(ord('a') + (best_from & 7))
                    br = (best_from >> 3) + 1
                    bt = chr(ord('a') + (best_to & 7))
                    btr = (best_to >> 3) + 1
                    piece = cpu.rb(0x4082 + best_from)
                    cpu.wb(0x4082 + best_from, 0)
                    cpu.wb(0x4082 + best_to, piece)
                    print(f"Computer plays: {bf}{br} -> {bt}{btr}")
                else:
                    print("Computer has no moves!")


if __name__ == '__main__':
    main()
