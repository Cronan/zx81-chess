#!/usr/bin/env python3
"""
ZX81 .P file generator

Creates a ZX81 tape file (.P) containing the chess program.
The .P file format is a memory dump from $4009 to the end of the
BASIC program area.

Usage: python3 make_p_file.py chess.bin chess.p
"""

import sys
import struct

def make_p_file(bin_path, p_path):
    """Create a .P file containing the chess binary in a REM statement."""

    # Read the binary
    with open(bin_path, 'rb') as f:
        machine_code = f.read()

    mc_len = len(machine_code)
    print(f"Machine code: {mc_len} bytes")

    # BASIC program structure:
    # Line 1: REM + machine code
    # Line 2: RAND USR 16514
    #
    # BASIC line format:
    #   2 bytes: line number (big-endian)
    #   2 bytes: line length (little-endian, includes NEWLINE)
    #   ...line content...
    #   1 byte: NEWLINE ($76)

    # Line 1: REM statement containing machine code
    # REM token = $EA
    # The REM content starts at $4082 (16514 decimal)
    line1_num = 1
    line1_content = bytes([0xEA]) + machine_code  # REM + code
    line1_len = len(line1_content) + 1  # +1 for NEWLINE

    # Line 2: RAND USR 16514
    # RAND token = $F9
    # USR token = $D4
    # "16514" as ZX81 number encoding (actually stored as ASCII digits)
    # In ZX81 BASIC, numbers are stored as their ASCII digits
    # followed by a hidden 5-byte floating point number
    # But for simplicity, let's use the minimal form
    line2_num = 2
    # RAND USR 16514 - digits 1,6,5,1,4 in ZX81 char codes
    # ZX81 digits: 0=$1C, 1=$1D, 2=$1E, etc.
    line2_content = bytes([
        0xF9,              # RAND
        0xD4,              # USR
        0x1D, 0x22, 0x21, 0x1D, 0x20,  # "16514" in ZX81 codes: 1=1D, 6=22, 5=21, 1=1D, 4=20
        0x7E,              # Number marker
        0x00, 0x00,        # Exponent and mantissa (5 bytes)
        0x00, 0x40,        # = 16514 as ZX81 float
        0x82,
    ])
    line2_len = len(line2_content) + 1

    # Build the BASIC program
    basic_program = bytearray()

    # Line 1 header
    basic_program.extend(struct.pack('>H', line1_num))  # Line number (big-endian)
    basic_program.extend(struct.pack('<H', line1_len))  # Length (little-endian)
    basic_program.extend(line1_content)
    basic_program.append(0x76)  # NEWLINE

    # Line 2 header
    basic_program.extend(struct.pack('>H', line2_num))
    basic_program.extend(struct.pack('<H', line2_len))
    basic_program.extend(line2_content)
    basic_program.append(0x76)  # NEWLINE

    # Calculate addresses
    # BASIC program starts at $407D (right after system variables)
    basic_start = 0x407D
    basic_end = basic_start + len(basic_program)

    # D_FILE (display file) - minimal collapsed display file
    # For a .P file, we put a minimal display file after the program
    d_file_addr = basic_end

    # Minimal display file: 24 NEWLINEs (collapsed mode)
    display_file = bytes([0x76] * 25)  # 25 newlines for 24 lines + terminator

    # VARS area starts after display file
    vars_addr = d_file_addr + len(display_file)

    # Variables area - empty, just the terminator
    vars_area = bytes([0x80])  # End marker

    # E_LINE (edit line) comes after VARS
    e_line_addr = vars_addr + len(vars_area)

    # Now build the system variables
    # The .P file starts at $4009
    # We need system vars from $4009 to $407C (116 bytes)

    sysvars = bytearray(116)  # $4009 to $407C inclusive = 116 bytes

    # Key system variables (offsets from $4009):
    # $4009 (0): VERSN = 0
    sysvars[0] = 0x00

    # $400A-$400B (1-2): E_PPC = current line being executed (0 initially)
    sysvars[1:3] = struct.pack('<H', 0)

    # $400C-$400D (3-4): D_FILE = display file address
    sysvars[3:5] = struct.pack('<H', d_file_addr)

    # $400E-$400F (5-6): DF_CC = print position (start of D_FILE + 1)
    sysvars[5:7] = struct.pack('<H', d_file_addr + 1)

    # $4010-$4011 (7-8): VARS = variables area
    sysvars[7:9] = struct.pack('<H', vars_addr)

    # $4012-$4013 (9-10): DEST = destination for assignment
    sysvars[9:11] = struct.pack('<H', 0)

    # $4014-$4015 (11-12): E_LINE = edit line
    sysvars[11:13] = struct.pack('<H', e_line_addr)

    # $4016-$4017 (13-14): CH_ADD = address of next char to interpret
    sysvars[13:15] = struct.pack('<H', basic_start)

    # $4018-$4019 (15-16): X_PTR = address of syntax error
    sysvars[15:17] = struct.pack('<H', 0)

    # $401A-$401B (17-18): STKBOT = stack bottom
    sysvars[17:19] = struct.pack('<H', e_line_addr + 1)

    # $401C-$401D (19-20): STKEND = stack end
    sysvars[19:21] = struct.pack('<H', e_line_addr + 1)

    # $401E (21): BERG = calculator's b register
    sysvars[21] = 0

    # $401F-$4020 (22-23): MEM = calculator's memory area
    sysvars[22:24] = struct.pack('<H', 0x405D)  # Point to MEMBOT

    # $4021 (24): not used
    sysvars[24] = 0

    # $4022 (25): DF_SZ = display file size (lines)
    sysvars[25] = 2  # 2 lines for input

    # $4023-$4024 (26-27): S_TOP = line number of top screen line
    sysvars[26:28] = struct.pack('<H', 0)

    # $4025-$4026 (28-29): LAST_K = last key pressed
    sysvars[28:30] = struct.pack('<H', 0xFFFF)  # No key

    # $4027 (30): DEBOUNCE = key debounce
    sysvars[30] = 0xFF

    # $4028 (31): MARGIN = margin (PAL=55, NTSC=31)
    sysvars[31] = 55  # PAL

    # $4029-$402A (32-33): NXTLIN = next line address
    sysvars[32:34] = struct.pack('<H', basic_start)

    # $402B-$402C (34-35): OLDPPC = line number for CONT
    sysvars[34:36] = struct.pack('<H', 0)

    # $402D (36): FLAGX = flags
    sysvars[36] = 0

    # $402E-$402F (37-38): STRLEN = string length
    sysvars[37:39] = struct.pack('<H', 0)

    # $4030-$4031 (39-40): T_ADDR = address of next item in syntax table
    sysvars[39:41] = struct.pack('<H', 0x0C8D)  # ROM address

    # $4032-$4033 (41-42): SEED = random seed
    sysvars[41:43] = struct.pack('<H', 0)

    # $4034-$4035 (43-44): FRAMES = frame counter
    sysvars[43:45] = struct.pack('<H', 0xFFFF)

    # $4036-$4037 (45-46): COORDS = plot coords
    sysvars[45:47] = struct.pack('<H', 0)

    # $4038 (47): PR_CC = print column counter
    sysvars[47] = 0xBC

    # $4039 (48): S_POSN_col = column for PRINT AT
    sysvars[48] = 33

    # $403A (49): S_POSN_line = line for PRINT AT
    sysvars[49] = 24

    # $403B (50): CDFLAG = flags for fast/slow
    sysvars[50] = 0x40  # Slow mode

    # $403C-$407B (51-114): PRBUFF and MEMBOT - printer buffer and calculator memory
    # Leave as zeros

    # $407C (115): not used / padding
    sysvars[115] = 0

    # Build the complete .P file
    # Format: system vars + BASIC program + display file + vars
    p_file = bytearray()
    p_file.extend(sysvars)
    p_file.extend(basic_program)
    p_file.extend(display_file)
    p_file.extend(vars_area)

    # Write the .P file
    with open(p_path, 'wb') as f:
        f.write(p_file)

    print(f"Created {p_path}: {len(p_file)} bytes")
    print(f"  System vars: {len(sysvars)} bytes ($4009-$407C)")
    print(f"  BASIC program: {len(basic_program)} bytes (starts at ${basic_start:04X})")
    print(f"  Display file: {len(display_file)} bytes (at ${d_file_addr:04X})")
    print(f"  Variables: {len(vars_area)} bytes (at ${vars_addr:04X})")
    print(f"  E_LINE: ${e_line_addr:04X}")
    print(f"  Machine code entry: $4082 (16514)")

    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.bin> <output.p>")
        sys.exit(1)

    make_p_file(sys.argv[1], sys.argv[2])
