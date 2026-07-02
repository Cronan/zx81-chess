#!/usr/bin/env python3
"""Cross-emulator opcode coverage check.

Every opcode chess.bin uses must be implemented by BOTH emulators
(test_harness.py and play/z80.js). Each new opcode the assembly picks
up has to be hand-added to two separate interpreters, and history shows
that's where divergence creeps in - so this walks the code region of
the binary, collects every distinct instruction, and probes each one
through both emulators. A probe that returns 'error' (unimplemented)
fails the run and names the instruction.

Data regions (the board/tables before `start`, the win/lose messages)
are skipped using chess.sym boundaries.
"""

import json
import io
import os
import subprocess
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_harness import Z80, setup_zx81_memory, load_symbols

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORG = 0x4082


def instr_length(code, i):
    """Length in bytes of the instruction at code[i] (standard Z80 sizes)."""
    op = code[i]

    if op == 0xCB:
        return 2
    if op == 0xED:
        sub = code[i + 1]
        # LD (nn),rr / LD rr,(nn) carry a 16-bit address
        return 4 if sub in (0x43, 0x4B, 0x53, 0x5B, 0x63, 0x6B, 0x73, 0x7B) else 2
    if op in (0xDD, 0xFD):
        sub = code[i + 1]
        if sub == 0xCB:
            return 4  # DD CB d op
        base = instr_length(code, i + 1)
        # Ops that address (HL) gain a displacement byte under DD/FD
        uses_hl = (
            sub in (0x34, 0x35, 0x36, 0x86, 0x8E, 0x96, 0x9E, 0xA6, 0xAE, 0xB6, 0xBE)
            or (0x46 <= sub <= 0x7E and (sub & 7) == 6 and sub != 0x76)
            or (0x70 <= sub <= 0x77)
        )
        return 1 + base + (1 if uses_hl else 0)

    # Unprefixed
    if op in (0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x36, 0x3E,   # LD r,n
              0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE,   # ALU n
              0x10, 0x18, 0x20, 0x28, 0x30, 0x38,               # DJNZ/JR
              0xD3, 0xDB):                                      # OUT/IN
        return 2
    if op in (0x01, 0x11, 0x21, 0x31,                           # LD rr,nn
              0x22, 0x2A, 0x32, 0x3A,                           # LD (nn) forms
              0xC3, 0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA,  # JP
              0xCD, 0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC):  # CALL
        return 3
    return 1


def collect_instructions(code, symbols):
    """Walk the code region and return {key: bytes} of distinct instructions."""
    end = len(code)
    # Data regions, as [start, end) offsets into the binary
    data = [(0, symbols['start'] - ORG),                          # board/vars/tables
            (symbols['msg_win'] - ORG, symbols['init_board'] - ORG)]  # messages

    found = {}
    boundaries = set()
    i = symbols['start'] - ORG
    while i < end:
        skipped = False
        for lo, hi in data:
            if lo <= i < hi:
                i = hi
                skipped = True
                break
        if skipped:
            continue
        boundaries.add(i + ORG)
        n = instr_length(code, i)
        raw = bytes(code[i:i + n])
        op = raw[0]
        if op in (0xCB, 0xED):
            key = f"{op:02X} {raw[1]:02X}"
        elif op in (0xDD, 0xFD):
            key = f"{op:02X} {raw[1]:02X}" if raw[1] != 0xCB else f"{op:02X} CB .. {raw[3]:02X}"
        else:
            key = f"{op:02X}"
        found.setdefault(key, raw)
        i += n

    # Self-check: a misaligned walk would decode garbage. Every code
    # symbol must land on an instruction boundary.
    misaligned = [
        name for name, a in symbols.items()
        if symbols['start'] <= a < ORG + end
        and not (symbols['msg_win'] <= a < symbols['init_board'])
        and a not in boundaries
    ]
    if misaligned:
        raise RuntimeError(f"disassembly walk out of sync at: {misaligned}")

    return found


def probe_python(instructions):
    """Run each instruction once through the Python emulator; return failures."""
    failures = []
    for key, raw in sorted(instructions.items()):
        cpu = Z80()
        setup_zx81_memory(cpu)
        addr = 0x5000
        for j, b in enumerate(raw):
            cpu.wb(addr + j, b)
        cpu.sp = 0x7000
        cpu.max_cycles = 1
        with redirect_stdout(io.StringIO()):
            result = cpu.run(addr)
        if result == "error":
            failures.append(key)
    return failures


def probe_js(instructions):
    """Probe the JS emulator via node; return failures."""
    payload = json.dumps([list(raw) for _, raw in sorted(instructions.items())])
    result = subprocess.run(
        ['node', os.path.join(ROOT, 'tools', 'opcode_check.js')],
        input=payload, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        print(result.stderr)
        raise RuntimeError("JS opcode probe crashed")
    bad_indexes = json.loads(result.stdout)
    keys = sorted(instructions.keys())
    return [keys[i] for i in bad_indexes]


def main():
    with open(os.path.join(ROOT, 'chess.bin'), 'rb') as f:
        code = f.read()
    symbols = load_symbols(os.path.join(ROOT, 'chess.sym'))

    instructions = collect_instructions(code, symbols)
    print(f"chess.bin uses {len(instructions)} distinct instructions")

    ok = True
    for name, failures in (("Python", probe_python(instructions)),
                           ("JS", probe_js(instructions))):
        if failures:
            ok = False
            print(f"FAIL: {name} emulator lacks: {', '.join(failures)}")
        else:
            print(f"PASS: {name} emulator implements all of them")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
