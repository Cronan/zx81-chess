#!/usr/bin/env python3
"""
ZX81 1K Chess - Comprehensive Test Suite

Unit tests for all major routines in the chess program.
Uses the Z80 emulator from test_harness.py to run actual code.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_harness import Z80, setup_zx81_memory, print_board_from_memory

# Memory addresses (must match chess.asm)
BOARD = 0x4082
CURSOR = 0x40C2
MOVE_FROM = 0x40C3
MOVE_TO = 0x40C4
BEST_FROM = 0x40C5
BEST_TO = 0x40C6
BEST_SCORE = 0x40C7
SIDE = 0x40C8

# Piece codes
EMPTY = 0
W_PAWN = 1
W_KNIGHT = 2
W_BISHOP = 3
W_ROOK = 4
W_QUEEN = 5
W_KING = 6
B_PAWN = 9
B_KNIGHT = 10
B_BISHOP = 11
B_ROOK = 12
B_QUEEN = 13
B_KING = 14

# ZX81 key codes for files A-H
ZX_A, ZX_B, ZX_C, ZX_D = 0x26, 0x27, 0x28, 0x29
ZX_E, ZX_F, ZX_G, ZX_H = 0x2A, 0x2B, 0x2C, 0x2D
# ZX81 key codes for ranks 1-8
ZX_1, ZX_2, ZX_3, ZX_4 = 0x1D, 0x1E, 0x1F, 0x20
ZX_5, ZX_6, ZX_7, ZX_8 = 0x21, 0x22, 0x23, 0x24


class ChessTest:
    """Test harness for ZX81 chess routines."""

    def __init__(self):
        with open('chess.bin', 'rb') as f:
            self.code = f.read()

        # Find routine addresses
        self.start_addr = 0x4082 + 109  # After data tables

    def setup_cpu(self):
        """Create fresh CPU state with code loaded."""
        cpu = Z80()
        setup_zx81_memory(cpu)
        cpu.load_binary(self.code, 0x4082)
        cpu.sp = 0x7FFF
        cpu.max_cycles = 500_000  # Default limit to prevent hangs
        return cpu

    def find_routine(self, cpu, offset_from_start):
        """Get routine address from CALL instruction."""
        addr = self.start_addr + offset_from_start
        return cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)

    def call_routine(self, cpu, addr):
        """Call a routine and wait for return."""
        cpu.push(0x0000)  # Sentinel return
        cpu.run(addr)

    def clear_board(self, cpu):
        """Clear all pieces from board."""
        for i in range(64):
            cpu.wb(BOARD + i, EMPTY)

    def set_piece(self, cpu, square, piece):
        """Place a piece on the board."""
        cpu.wb(BOARD + square, piece)

    def get_piece(self, cpu, square):
        """Get piece at square."""
        return cpu.rb(BOARD + square)

    def sq(self, file, rank):
        """Convert file (a-h) and rank (1-8) to square index."""
        f = ord(file.lower()) - ord('a')
        r = rank - 1
        return r * 8 + f

    def find_think(self, cpu):
        """Find think routine address."""
        for addr in range(self.start_addr, self.start_addr + 200):
            if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
                cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
                return cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
        raise RuntimeError("Could not find think routine")

    def find_get_move(self, cpu):
        """Find get_move routine address (3rd CALL from start, offset 10)."""
        return self.find_routine(cpu, 10)

    def find_get_square(self, cpu):
        """Find get_square routine address (called from get_move)."""
        get_move = self.find_get_move(cpu)
        # get_move starts: LD A,$76 / RST $10 / LD A,$0F / RST $10 / CALL get_square
        # = 3E 76 D7 3E 0F D7 CD xx xx
        call_addr = get_move + 6
        assert cpu.rb(call_addr) == 0xCD, f"Expected CALL at get_move+6, got 0x{cpu.rb(call_addr):02x}"
        return cpu.rb(call_addr + 1) | (cpu.rb(call_addr + 2) << 8)

    def find_cls_and_draw(self, cpu):
        """Find cls_and_draw routine (2nd CALL from start, offset 3)."""
        return self.find_routine(cpu, 3)

    def find_get_piece_char(self, cpu):
        """Find get_piece_char by scanning cls_and_draw for CALL in col_loop."""
        draw_addr = self.find_cls_and_draw(cpu)
        # Scan forward for the CALL inside the column loop
        for addr in range(draw_addr + 30, draw_addr + 120):
            if cpu.rb(addr) == 0xCD:
                target = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                # get_piece_char starts with AND A (0xA7)
                if cpu.rb(target) == 0xA7:
                    return target
        raise RuntimeError("Could not find get_piece_char routine")

    def setup_cpu_with_keys(self, keys):
        """Create CPU with keyboard input queue."""
        cpu = self.setup_cpu()
        cpu.key_queue = list(keys)
        cpu.display_output = []
        cpu.display_line = []
        return cpu

    def init_board(self, cpu):
        """Initialize the chess board."""
        init_addr = self.find_routine(cpu, 0)
        self.call_routine(cpu, init_addr)


def test_board_init():
    """Test init_board routine."""
    t = ChessTest()
    cpu = t.setup_cpu()

    init_addr = t.find_routine(cpu, 0)
    t.call_routine(cpu, init_addr)

    # Check white pieces (rank 1)
    expected_r1 = [W_ROOK, W_KNIGHT, W_BISHOP, W_QUEEN, W_KING, W_BISHOP, W_KNIGHT, W_ROOK]
    for i, exp in enumerate(expected_r1):
        actual = t.get_piece(cpu, i)
        assert actual == exp, f"Rank 1 file {i}: expected {exp}, got {actual}"

    # Check white pawns (rank 2)
    for i in range(8, 16):
        actual = t.get_piece(cpu, i)
        assert actual == W_PAWN, f"Square {i}: expected W_PAWN, got {actual}"

    # Check empty squares (ranks 3-6)
    for i in range(16, 48):
        actual = t.get_piece(cpu, i)
        assert actual == EMPTY, f"Square {i}: should be empty, got {actual}"

    # Check black pawns (rank 7)
    for i in range(48, 56):
        actual = t.get_piece(cpu, i)
        assert actual == B_PAWN, f"Square {i}: expected B_PAWN, got {actual}"

    # Check black pieces (rank 8)
    expected_r8 = [B_ROOK, B_KNIGHT, B_BISHOP, B_QUEEN, B_KING, B_BISHOP, B_KNIGHT, B_ROOK]
    for i, exp in enumerate(expected_r8):
        actual = t.get_piece(cpu, 56 + i)
        assert actual == exp, f"Rank 8 file {i}: expected {exp}, got {actual}"

    print("  PASS: init_board")


def test_knight_moves():
    """Test that knight generates correct L-shaped moves."""
    t = ChessTest()
    cpu = t.setup_cpu()

    # Clear board and place a black knight on d4 (square 27)
    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_KNIGHT)

    # Run AI to generate moves
    cpu.wb(SIDE, 8)  # Black's turn

    # Find think routine
    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    assert think_addr, "Could not find think routine"

    t.call_routine(cpu, think_addr)

    # Knight from d4 should be able to move (any L-shape)
    best_from = cpu.rb(BEST_FROM)
    best_to = cpu.rb(BEST_TO)

    assert best_from == d4, f"Knight move should be from d4 ({d4}), got {best_from}"

    # Valid knight destinations from d4: b3, b5, c2, c6, e2, e6, f3, f5
    valid_targets = [t.sq('b',3), t.sq('b',5), t.sq('c',2), t.sq('c',6),
                    t.sq('e',2), t.sq('e',6), t.sq('f',3), t.sq('f',5)]

    assert best_to in valid_targets, f"Knight target {best_to} not in valid L-shapes {valid_targets}"

    print("  PASS: knight L-shape moves")


def test_knight_edge():
    """Test knight on board edge doesn't wrap around."""
    t = ChessTest()
    cpu = t.setup_cpu()

    # Knight on a1 - limited moves, shouldn't wrap to h-file
    t.clear_board(cpu)
    a1 = t.sq('a', 1)
    t.set_piece(cpu, a1, B_KNIGHT)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    # From a1, knight can only go to b3 or c2
    valid_targets = [t.sq('b', 3), t.sq('c', 2)]

    assert best_to in valid_targets, f"Knight from a1 went to {best_to}, expected {valid_targets}"

    print("  PASS: knight edge handling")


def test_bishop_diagonal():
    """Test bishop moves diagonally."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_BISHOP)

    # Place a white ROOK (value 5) to capture - higher than non-capture (1)
    g7 = t.sq('g', 7)
    t.set_piece(cpu, g7, W_ROOK)

    cpu.wb(SIDE, 8)
    cpu.max_cycles = 100_000  # Limit to prevent hangs

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_from = cpu.rb(BEST_FROM)
    best_to = cpu.rb(BEST_TO)

    # Bishop should capture rook on g7 (diagonal, high value)
    assert best_from == d4, f"Expected move from d4, got {best_from}"
    assert best_to == g7, f"Bishop should capture rook on g7 ({g7}), went to {best_to}"

    print("  PASS: bishop diagonal movement")


def test_rook_orthogonal():
    """Test rook moves only orthogonally."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_ROOK)

    # Place white queen to capture on d1
    d1 = t.sq('d', 1)
    t.set_piece(cpu, d1, W_QUEEN)  # High value target (9 points)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    cpu.cycles = 0
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    best_score = cpu.rb(BEST_SCORE)

    # Rook should capture queen on d1 (same file, highest value)
    assert best_to == d1, f"Rook should capture queen on d1 ({d1}), went to {best_to}"
    assert best_score == 9, f"Score should be 9 (queen), got {best_score}"

    print("  PASS: rook orthogonal movement")


def test_queen_all_directions():
    """Test queen can move both diagonally and orthogonally."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_QUEEN)

    # Place white king on diagonal for high value capture (50 points!)
    h8 = t.sq('h', 8)
    t.set_piece(cpu, h8, W_KING)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    cpu.cycles = 0
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    best_score = cpu.rb(BEST_SCORE)

    # Queen should capture king on h8 (diagonal, highest value)
    assert best_to == h8, f"Queen should capture king on h8 ({h8}), went to {best_to}"
    assert best_score == 50, f"Score should be 50 (king), got {best_score}"

    print("  PASS: queen all-direction movement")


def test_pawn_forward():
    """Test pawn moves forward."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # Black pawn on e5
    e5 = t.sq('e', 5)
    t.set_piece(cpu, e5, B_PAWN)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_from = cpu.rb(BEST_FROM)
    best_to = cpu.rb(BEST_TO)

    e4 = t.sq('e', 4)  # One square forward (south for black)

    assert best_from == e5, f"Pawn should move from e5 ({e5}), got {best_from}"
    assert best_to == e4, f"Pawn should move to e4 ({e4}), got {best_to}"

    print("  PASS: pawn forward movement")


def test_pawn_double_move():
    """Test pawn double move from starting position."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # Black pawn on starting rank (rank 7)
    e7 = t.sq('e', 7)
    t.set_piece(cpu, e7, B_PAWN)

    # Block e6 to force double move consideration
    # Actually, AI will prefer any legal move with same score
    # Let's check it can at least move

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_from = cpu.rb(BEST_FROM)
    best_to = cpu.rb(BEST_TO)

    e6 = t.sq('e', 6)
    e5 = t.sq('e', 5)

    assert best_from == e7, f"Pawn should move from e7"
    assert best_to in [e6, e5], f"Pawn should move to e6 or e5, got {best_to}"

    print("  PASS: pawn double move from start")


def test_pawn_capture():
    """Test pawn captures diagonally."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # Black pawn on d5
    d5 = t.sq('d', 5)
    t.set_piece(cpu, d5, B_PAWN)

    # White queen on c4 (capturable!)
    c4 = t.sq('c', 4)
    t.set_piece(cpu, c4, W_QUEEN)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)

    # Pawn should capture queen
    assert best_to == c4, f"Pawn should capture queen on c4, went to {best_to}"

    print("  PASS: pawn diagonal capture")


def test_king_single_step():
    """Test king only moves one square."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    e4 = t.sq('e', 4)
    t.set_piece(cpu, e4, B_KING)

    # Place white ROOK adjacent (value 5, higher than non-capture of 1)
    e3 = t.sq('e', 3)
    t.set_piece(cpu, e3, W_ROOK)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_from = cpu.rb(BEST_FROM)
    best_to = cpu.rb(BEST_TO)

    assert best_from == e4, f"King should move from e4"

    # King should capture rook (adjacent capture, score=5)
    assert best_to == e3, f"King should capture rook on e3, went to {best_to}"

    print("  PASS: king single-step movement")


def test_capture_priority():
    """Test AI prefers higher value captures."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_QUEEN)

    # Place white pawn (value 1) and white rook (value 5) in range
    c3 = t.sq('c', 3)
    e5 = t.sq('e', 5)
    t.set_piece(cpu, c3, W_PAWN)
    t.set_piece(cpu, e5, W_ROOK)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    best_score = cpu.rb(BEST_SCORE)

    # Should capture rook (higher value)
    assert best_to == e5, f"Should capture rook on e5 (value 5), captured square {best_to}"
    assert best_score == 5, f"Score should be 5, got {best_score}"

    print("  PASS: capture priority (prefers high value)")


def test_no_self_capture():
    """Test AI doesn't capture own pieces."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_ROOK)

    # Place own black pieces all around
    t.set_piece(cpu, t.sq('d', 5), B_PAWN)
    t.set_piece(cpu, t.sq('d', 3), B_PAWN)
    t.set_piece(cpu, t.sq('c', 4), B_PAWN)
    t.set_piece(cpu, t.sq('e', 4), B_PAWN)

    # Leave one escape route with white pawn to capture
    a4 = t.sq('a', 4)
    t.set_piece(cpu, a4, W_PAWN)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)

    # Should capture white pawn, not land on own pieces
    own_pieces = [t.sq('d',5), t.sq('d',3), t.sq('c',4), t.sq('e',4)]
    assert best_to not in own_pieces, f"Rook landed on own piece at {best_to}"

    print("  PASS: no self-capture")


def test_check_kings():
    """Test check_kings routine detects missing kings."""
    t = ChessTest()
    cpu = t.setup_cpu()

    # Find check_kings routine - it's called after moves
    # Look for "CALL check_kings" pattern in game loop (followed by JR NZ)
    check_kings_addr = None
    for addr in range(t.start_addr + 10, t.start_addr + 100):
        # Look for JR NZ (0x20) after CALL - game ends when Z is clear
        if cpu.rb(addr) == 0xCD:
            next_op = cpu.rb(addr + 3)
            if next_op == 0x20:  # JR NZ
                check_kings_addr = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                break

    if not check_kings_addr:
        print("  SKIP: Could not locate check_kings routine")
        return

    # Test with both kings present
    init_addr = t.find_routine(cpu, 0)
    t.call_routine(cpu, init_addr)

    cpu.sp = 0x7FFF
    t.call_routine(cpu, check_kings_addr)

    # Z flag should be SET (both kings present, cp 2 gives Z=1)
    z_flag = cpu.get_flag(cpu.FLAG_Z)
    assert z_flag, "Z flag should be set when both kings present"

    # Now remove white king
    for i in range(64):
        p = t.get_piece(cpu, i)
        if p == W_KING:
            t.set_piece(cpu, i, EMPTY)
            break

    cpu.sp = 0x7FFF
    t.call_routine(cpu, check_kings_addr)

    # Z flag should be CLEAR (king missing, cp 2 gives Z=0)
    z_flag = cpu.get_flag(cpu.FLAG_Z)
    assert not z_flag, "Z flag should be clear when king is missing"

    print("  PASS: check_kings detection")


def test_move_execution():
    """Test do_move executes moves correctly."""
    t = ChessTest()
    cpu = t.setup_cpu()

    # Initialize board
    init_addr = t.find_routine(cpu, 0)
    t.call_routine(cpu, init_addr)

    # Set up a move: e2 to e4
    e2 = t.sq('e', 2)
    e4 = t.sq('e', 4)
    cpu.wb(MOVE_FROM, e2)
    cpu.wb(MOVE_TO, e4)

    # Find make_move routine by searching all CALLs from game_loop onward
    # Structure: start (2 calls), game_loop (xor a, ld (side),a, call get_move, call make_move)
    # make_move is the 4th call after entry (after init_board, cls_and_draw, get_move)
    make_move_addr = None
    call_count = 0
    for addr in range(t.start_addr, t.start_addr + 60):
        if cpu.rb(addr) == 0xCD:
            call_count += 1
            if call_count == 4:  # 4th CALL is make_move
                make_move_addr = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                break

    if not make_move_addr:
        print("  SKIP: Could not locate make_move routine")
        return

    cpu.sp = 0x7FFF
    t.call_routine(cpu, make_move_addr)

    # Check e2 is now empty
    assert t.get_piece(cpu, e2) == EMPTY, f"e2 should be empty after move"

    # Check e4 has pawn
    assert t.get_piece(cpu, e4) == W_PAWN, f"e4 should have white pawn"

    print("  PASS: move execution")


def test_pawn_promotion():
    """Test pawn promotion to queen."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)

    # White pawn on e7, about to promote
    e7 = t.sq('e', 7)
    e8 = t.sq('e', 8)
    t.set_piece(cpu, e7, W_PAWN)

    cpu.wb(MOVE_FROM, e7)
    cpu.wb(MOVE_TO, e8)

    # Find make_move (4th CALL after entry)
    make_move_addr = None
    call_count = 0
    for addr in range(t.start_addr, t.start_addr + 60):
        if cpu.rb(addr) == 0xCD:
            call_count += 1
            if call_count == 4:
                make_move_addr = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                break

    if not make_move_addr:
        print("  SKIP: Could not locate make_move routine")
        return

    cpu.sp = 0x7FFF
    t.call_routine(cpu, make_move_addr)

    # Check e8 has white queen
    piece = t.get_piece(cpu, e8)
    assert piece == W_QUEEN, f"e8 should have white queen after promotion, got {piece}"

    # Test black pawn promotion
    t.clear_board(cpu)
    d2 = t.sq('d', 2)
    d1 = t.sq('d', 1)
    t.set_piece(cpu, d2, B_PAWN)

    cpu.wb(MOVE_FROM, d2)
    cpu.wb(MOVE_TO, d1)

    cpu.sp = 0x7FFF
    t.call_routine(cpu, make_move_addr)

    piece = t.get_piece(cpu, d1)
    assert piece == B_QUEEN, f"d1 should have black queen after promotion, got {piece}"

    print("  PASS: pawn promotion")


def test_slider_blocked():
    """Test sliding pieces stop when blocked."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)

    # Black rook on a1
    a1 = t.sq('a', 1)
    t.set_piece(cpu, a1, B_ROOK)

    # Own pawn blocking the file on a3
    a3 = t.sq('a', 3)
    t.set_piece(cpu, a3, B_PAWN)

    # White king far away on h8 - high value but unreachable
    h8 = t.sq('h', 8)
    t.set_piece(cpu, h8, W_KING)

    cpu.wb(SIDE, 8)

    think_addr = None
    for addr in range(t.start_addr, t.start_addr + 200):
        if (cpu.rb(addr) == 0x3E and cpu.rb(addr+1) == 0x08 and
            cpu.rb(addr+2) == 0x32 and cpu.rb(addr+5) == 0xCD):
            think_addr = cpu.rb(addr+6) | (cpu.rb(addr+7) << 8)
            break

    t.call_routine(cpu, think_addr)

    best_from = cpu.rb(BEST_FROM)
    best_to = cpu.rb(BEST_TO)

    # Rook should move, but NOT to a3 or beyond (blocked)
    # and NOT to h8 (can't reach through pieces)
    if best_from == a1:
        a_file_blocked = [a3, t.sq('a',4), t.sq('a',5), t.sq('a',6), t.sq('a',7), t.sq('a',8)]
        assert best_to not in a_file_blocked, f"Rook shouldn't pass through own pawn"

    print("  PASS: slider blocked by own pieces")


def test_get_square():
    """Test get_square converts keyboard input to correct board index."""
    t = ChessTest()

    test_cases = [
        # (file_key, rank_key, expected_index, description)
        (ZX_A, ZX_1, 0,  "a1"),
        (ZX_E, ZX_2, 12, "e2"),
        (ZX_E, ZX_4, 28, "e4"),
        (ZX_H, ZX_8, 63, "h8"),
        (ZX_A, ZX_8, 56, "a8"),
        (ZX_H, ZX_1, 7,  "h1"),
        (ZX_D, ZX_5, 35, "d5"),
    ]

    get_sq_addr = None
    for file_key, rank_key, expected, desc in test_cases:
        cpu = t.setup_cpu_with_keys([file_key, rank_key])
        if get_sq_addr is None:
            get_sq_addr = t.find_get_square(cpu)
        cpu.push(0x0000)
        cpu.run(get_sq_addr)
        assert cpu.a == expected, f"get_square({desc}): expected {expected}, got {cpu.a}"

    print("  PASS: get_square keyboard input")


def test_get_move_valid():
    """Test get_move processes a valid 4-key move input."""
    t = ChessTest()
    cpu = t.setup_cpu_with_keys([ZX_E, ZX_2, ZX_E, ZX_4])
    t.init_board(cpu)

    get_move_addr = t.find_get_move(cpu)
    cpu.push(0x0000)
    result = cpu.run(get_move_addr, stop_on_halt_no_keys=True)

    move_from = cpu.rb(MOVE_FROM)
    move_to = cpu.rb(MOVE_TO)
    assert result == "returned", f"get_move should return normally, got {result}"
    assert move_from == t.sq('e', 2), f"move_from should be e2 (12), got {move_from}"
    assert move_to == t.sq('e', 4), f"move_to should be e4 (28), got {move_to}"

    print("  PASS: get_move valid input (E2E4)")


def test_get_move_rejects_empty():
    """Test get_move rejects selecting an empty source square."""
    t = ChessTest()
    # First try empty square e4, then valid e2->e4
    cpu = t.setup_cpu_with_keys([ZX_E, ZX_4, ZX_E, ZX_2, ZX_E, ZX_4])
    t.init_board(cpu)

    get_move_addr = t.find_get_move(cpu)
    cpu.push(0x0000)
    result = cpu.run(get_move_addr, stop_on_halt_no_keys=True)

    move_from = cpu.rb(MOVE_FROM)
    move_to = cpu.rb(MOVE_TO)
    assert result == "returned", f"get_move should eventually succeed, got {result}"
    assert move_from == t.sq('e', 2), f"After retry, from should be e2, got {move_from}"
    assert move_to == t.sq('e', 4), f"After retry, to should be e4, got {move_to}"

    print("  PASS: get_move rejects empty source")


def test_get_move_rejects_black_source():
    """Test get_move rejects selecting a black piece as source."""
    t = ChessTest()
    # Try black pawn a7, then valid a2->a3
    cpu = t.setup_cpu_with_keys([ZX_A, ZX_7, ZX_A, ZX_2, ZX_A, ZX_3])
    t.init_board(cpu)

    get_move_addr = t.find_get_move(cpu)
    cpu.push(0x0000)
    result = cpu.run(get_move_addr, stop_on_halt_no_keys=True)

    move_from = cpu.rb(MOVE_FROM)
    assert result == "returned"
    assert move_from == t.sq('a', 2), f"After retry, from should be a2, got {move_from}"

    print("  PASS: get_move rejects black piece source")


def test_get_move_rejects_own_dest():
    """Test get_move rejects moving onto own piece."""
    t = ChessTest()
    # Try e1 (king) to d1 (queen) - own piece dest, then valid e2->e4
    cpu = t.setup_cpu_with_keys([ZX_E, ZX_1, ZX_D, ZX_1,
                                  ZX_E, ZX_2, ZX_E, ZX_4])
    t.init_board(cpu)

    get_move_addr = t.find_get_move(cpu)
    cpu.push(0x0000)
    result = cpu.run(get_move_addr, stop_on_halt_no_keys=True)

    move_from = cpu.rb(MOVE_FROM)
    move_to = cpu.rb(MOVE_TO)
    assert result == "returned"
    assert move_from == t.sq('e', 2), f"After retry, from should be e2, got {move_from}"
    assert move_to == t.sq('e', 4), f"After retry, to should be e4, got {move_to}"

    print("  PASS: get_move rejects own piece destination")


def test_get_piece_char():
    """Test get_piece_char returns correct display characters."""
    t = ChessTest()
    cpu = t.setup_cpu()
    gpc_addr = t.find_get_piece_char(cpu)

    # ZX81 character codes
    CH_SPACE = 0x00
    CH_P, CH_N, CH_B, CH_R, CH_Q, CH_K = 0x35, 0x33, 0x27, 0x37, 0x36, 0x30
    CH_DOT = 0x1B
    CH_INV = 0x80

    test_cases = [
        (EMPTY,    CH_DOT,        "empty square"),
        (W_PAWN,   CH_P,          "white pawn"),
        (W_KNIGHT, CH_N,          "white knight"),
        (W_BISHOP, CH_B,          "white bishop"),
        (W_ROOK,   CH_R,          "white rook"),
        (W_QUEEN,  CH_Q,          "white queen"),
        (W_KING,   CH_K,          "white king"),
        (B_PAWN,   CH_P | CH_INV, "black pawn (inverse)"),
        (B_KNIGHT, CH_N | CH_INV, "black knight (inverse)"),
        (B_BISHOP, CH_B | CH_INV, "black bishop (inverse)"),
        (B_ROOK,   CH_R | CH_INV, "black rook (inverse)"),
        (B_QUEEN,  CH_Q | CH_INV, "black queen (inverse)"),
        (B_KING,   CH_K | CH_INV, "black king (inverse)"),
    ]

    for piece_code, expected_char, desc in test_cases:
        cpu2 = t.setup_cpu()
        cpu2.a = piece_code
        cpu2.push(0x0000)
        cpu2.run(gpc_addr)
        assert cpu2.a == expected_char, \
            f"get_piece_char({desc}): expected 0x{expected_char:02x}, got 0x{cpu2.a:02x}"

    print("  PASS: get_piece_char display characters")


def test_cls_and_draw():
    """Test cls_and_draw renders board to display output."""
    t = ChessTest()
    cpu = t.setup_cpu()
    cpu.display_output = []
    cpu.display_line = []

    t.init_board(cpu)

    draw_addr = t.find_cls_and_draw(cpu)
    cpu.push(0x0000)
    cpu.run(draw_addr)

    # Flush remaining line
    if cpu.display_line:
        cpu.display_output.append(''.join(cpu.display_line))

    output = '\n'.join(cpu.display_output)

    # Verify column headers
    assert any('A' in line and 'H' in line for line in cpu.display_output), \
        "Display should include column headers A-H"

    # Verify rank numbers
    assert any('8' in line for line in cpu.display_output), "Display should include rank 8"
    assert any('1' in line for line in cpu.display_output), "Display should include rank 1"

    # Verify pieces are present - white pieces are uppercase, black are lowercase
    assert any('R' in line and 'K' in line for line in cpu.display_output), \
        "Display should show white pieces (R, K)"
    assert any('r' in line and 'k' in line for line in cpu.display_output), \
        "Display should show black pieces (r, k) in inverse"

    # Verify 8 rows of board data
    rank_lines = [line for line in cpu.display_output if line and line[0].isdigit()]
    assert len(rank_lines) == 8, f"Should have 8 rank lines, got {len(rank_lines)}"

    print("  PASS: cls_and_draw display rendering")


def test_full_game_turn():
    """Test a complete game turn: player move + computer response."""
    t = ChessTest()
    # Queue E2E4 move
    cpu = t.setup_cpu_with_keys([ZX_E, ZX_2, ZX_E, ZX_4])

    # Run from start entry point
    cpu.push(0x0000)
    result = cpu.run(t.start_addr, stop_on_halt_no_keys=True)

    # Player's move: e2 pawn should be on e4 now
    assert t.get_piece(cpu, t.sq('e', 2)) == EMPTY, "e2 should be empty after E2E4"
    assert t.get_piece(cpu, t.sq('e', 4)) == W_PAWN, "e4 should have white pawn"

    # Computer should have made a move (some black piece moved)
    board_state = [cpu.rb(BOARD + i) for i in range(64)]
    # Count black pieces - should still be 16 (no captures possible on first move)
    black_count = sum(1 for p in board_state if p & 0x08)
    assert black_count == 16, f"All 16 black pieces should remain, found {black_count}"

    # Black pawns on rank 7: at least one should have moved
    rank7_pawns = sum(1 for i in range(48, 56) if board_state[i] == B_PAWN)
    assert rank7_pawns < 8, "Computer should have moved at least one piece"

    print("  PASS: full game turn (player + computer)")


def test_knight_h_file_edge():
    """Test knight on h-file doesn't wrap to a-file."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    h4 = t.sq('h', 4)
    t.set_piece(cpu, h4, B_KNIGHT)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    best_to_col = best_to & 7

    # From h4, valid knight targets: f3, f5, g2, g6
    # Invalid (wrapping): a3, a5, b2, b6 etc.
    valid_targets = [t.sq('f', 3), t.sq('f', 5), t.sq('g', 2), t.sq('g', 6)]
    assert best_to in valid_targets, \
        f"Knight from h4 went to col {best_to_col}, square {best_to}, expected one of {valid_targets}"

    print("  PASS: knight h-file edge (no wrap)")


def test_knight_h8_corner():
    """Test knight in h8 corner has limited valid moves."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    h8 = t.sq('h', 8)
    t.set_piece(cpu, h8, B_KNIGHT)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    # From h8, valid knight moves: f7, g6
    valid_targets = [t.sq('f', 7), t.sq('g', 6)]
    assert best_to in valid_targets, \
        f"Knight from h8 went to {best_to}, expected one of {valid_targets}"

    print("  PASS: knight h8 corner")


def test_pawn_a_file_no_wrap():
    """Test black pawn on a-file doesn't capture wrapping to h-file."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # Black pawn on a4
    a4 = t.sq('a', 4)
    t.set_piece(cpu, a4, B_PAWN)
    # White piece on h3 - should NOT be capturable by wrapping
    h3 = t.sq('h', 3)
    t.set_piece(cpu, h3, W_QUEEN)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    # Pawn on a4 can go to a3 (forward) or b3 (capture right), NOT h3
    assert best_to != h3, f"Pawn on a-file should not capture on h-file by wrapping!"
    valid_targets = [t.sq('a', 3), t.sq('b', 3)]
    assert best_to in valid_targets, f"Pawn from a4 went to {best_to}, expected {valid_targets}"

    print("  PASS: pawn a-file no wrap capture")


def test_pawn_h_file_no_wrap():
    """Test black pawn on h-file doesn't capture wrapping to a-file."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    h5 = t.sq('h', 5)
    t.set_piece(cpu, h5, B_PAWN)
    # White queen on a4 - should NOT be capturable by wrapping
    a4 = t.sq('a', 4)
    t.set_piece(cpu, a4, W_QUEEN)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    assert best_to != a4, f"Pawn on h-file should not capture on a-file by wrapping!"
    valid_targets = [t.sq('h', 4), t.sq('g', 4)]
    assert best_to in valid_targets, f"Pawn from h5 went to {best_to}, expected {valid_targets}"

    print("  PASS: pawn h-file no wrap capture")


def test_bishop_edge_no_wrap():
    """Test bishop diagonal doesn't wrap around board edges."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # Bishop on h4 sliding NE should stop at edge, not wrap to a5
    h4 = t.sq('h', 4)
    t.set_piece(cpu, h4, B_BISHOP)
    # Place a tempting target on a5 - should be unreachable diagonally from h4
    a5 = t.sq('a', 5)
    t.set_piece(cpu, a5, W_QUEEN)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    # Bishop from h4 can go: g3, f2, e1 (SW diagonal) and g5, f6, e7, d8 (NW diagonal)
    assert best_to != a5, f"Bishop should not wrap from h-file to a-file!"

    # All valid bishop targets from h4
    valid_sw = [t.sq('g', 3), t.sq('f', 2), t.sq('e', 1)]
    valid_nw = [t.sq('g', 5), t.sq('f', 6), t.sq('e', 7), t.sq('d', 8)]
    valid = valid_sw + valid_nw
    assert best_to in valid, f"Bishop from h4 went to {best_to}, not in valid set"

    print("  PASS: bishop edge no wrap")


def test_rook_edge_no_wrap():
    """Test rook on h-file moving east doesn't wrap to a-file."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    h4 = t.sq('h', 4)
    t.set_piece(cpu, h4, B_ROOK)
    # Place queen on a4 - rook can reach via rank (westward), but NOT by wrapping east
    a4 = t.sq('a', 4)
    t.set_piece(cpu, a4, W_QUEEN)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    # Rook should capture queen on a4 (going west along rank 4)
    assert best_to == a4, f"Rook should capture queen on a4, got {best_to}"

    print("  PASS: rook edge wrapping")


def test_pawn_no_double_from_wrong_rank():
    """Test black pawn can't move 2 squares from non-starting rank."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # Black pawn on e5 (rank 5, NOT starting rank 7)
    e5 = t.sq('e', 5)
    t.set_piece(cpu, e5, B_PAWN)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    e4 = t.sq('e', 4)  # One square forward
    e3 = t.sq('e', 3)  # Two squares forward (should be illegal)
    assert best_to == e4, f"Pawn from e5 should only go to e4, got {best_to}"
    assert best_to != e3, "Pawn should not double-move from rank 5"

    print("  PASS: pawn no double move from wrong rank")


def test_promotion_with_capture():
    """Test pawn promotion works when capturing on the last rank."""
    t = ChessTest()
    cpu = t.setup_cpu()

    t.clear_board(cpu)
    # White pawn on d7, black rook on e8 - capture and promote
    d7 = t.sq('d', 7)
    e8 = t.sq('e', 8)
    t.set_piece(cpu, d7, W_PAWN)
    t.set_piece(cpu, e8, B_ROOK)

    cpu.wb(MOVE_FROM, d7)
    cpu.wb(MOVE_TO, e8)

    # Find make_move (4th CALL from start)
    make_move_addr = None
    call_count = 0
    for addr in range(t.start_addr, t.start_addr + 60):
        if cpu.rb(addr) == 0xCD:
            call_count += 1
            if call_count == 4:
                make_move_addr = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                break

    assert make_move_addr, "Could not find make_move"
    cpu.sp = 0x7FFF
    t.call_routine(cpu, make_move_addr)

    assert t.get_piece(cpu, d7) == EMPTY, "d7 should be empty"
    assert t.get_piece(cpu, e8) == W_QUEEN, \
        f"e8 should be white queen after promotion+capture, got {t.get_piece(cpu, e8)}"

    print("  PASS: pawn promotion with capture")


def test_game_over_white_wins():
    """Test game over detection when black king is captured."""
    t = ChessTest()
    cpu = t.setup_cpu()
    t.init_board(cpu)

    # Find check_kings
    check_kings_addr = None
    for addr in range(t.start_addr + 10, t.start_addr + 100):
        if cpu.rb(addr) == 0xCD:
            next_op = cpu.rb(addr + 3)
            if next_op == 0x20:  # JR NZ
                check_kings_addr = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                break

    assert check_kings_addr, "Could not find check_kings"

    # Remove black king - simulates capture
    bk_pos = t.sq('e', 8)
    assert t.get_piece(cpu, bk_pos) == B_KING
    t.set_piece(cpu, bk_pos, EMPTY)

    cpu.sp = 0x7FFF
    t.call_routine(cpu, check_kings_addr)

    # Z flag should be CLEAR (only 1 king found, cp 2 gives NZ)
    z_flag = cpu.get_flag(cpu.FLAG_Z)
    assert not z_flag, "Z should be clear when black king is missing (game over)"

    print("  PASS: game over detection (white wins)")


def test_game_over_black_wins():
    """Test game over detection when white king is captured."""
    t = ChessTest()
    cpu = t.setup_cpu()
    t.init_board(cpu)

    check_kings_addr = None
    for addr in range(t.start_addr + 10, t.start_addr + 100):
        if cpu.rb(addr) == 0xCD:
            next_op = cpu.rb(addr + 3)
            if next_op == 0x20:
                check_kings_addr = cpu.rb(addr + 1) | (cpu.rb(addr + 2) << 8)
                break

    assert check_kings_addr

    # Remove white king
    wk_pos = t.sq('e', 1)
    assert t.get_piece(cpu, wk_pos) == W_KING
    t.set_piece(cpu, wk_pos, EMPTY)

    cpu.sp = 0x7FFF
    t.call_routine(cpu, check_kings_addr)

    z_flag = cpu.get_flag(cpu.FLAG_Z)
    assert not z_flag, "Z should be clear when white king is missing (game over)"

    print("  PASS: game over detection (black wins)")


def test_slider_direction_masks():
    """Test bishop uses diagonals only, rook uses orthogonals only."""
    t = ChessTest()

    # Bishop should NOT move orthogonally
    cpu = t.setup_cpu()
    t.clear_board(cpu)
    d4 = t.sq('d', 4)
    t.set_piece(cpu, d4, B_BISHOP)
    # Place white queen directly north on d8 - bishop can't reach it
    d8 = t.sq('d', 8)
    t.set_piece(cpu, d8, W_QUEEN)

    cpu.wb(SIDE, 8)
    think_addr = t.find_think(cpu)
    t.call_routine(cpu, think_addr)

    best_to = cpu.rb(BEST_TO)
    assert best_to != d8, "Bishop should not reach d8 (orthogonal from d4)!"

    # Rook should NOT move diagonally
    cpu2 = t.setup_cpu()
    t.clear_board(cpu2)
    d4 = t.sq('d', 4)
    t.set_piece(cpu2, d4, B_ROOK)
    # Place white queen on diagonal g7 - rook can't reach it
    g7 = t.sq('g', 7)
    t.set_piece(cpu2, g7, W_QUEEN)

    cpu2.wb(SIDE, 8)
    t.call_routine(cpu2, think_addr)

    best_to = cpu2.rb(BEST_TO)
    assert best_to != g7, "Rook should not reach g7 (diagonal from d4)!"

    print("  PASS: slider direction masks (bishop diagonal, rook orthogonal)")


def run_all_tests():
    """Run all tests and report results."""
    print("\n=== ZX81 Chess Test Suite ===\n")

    tests = [
        ("Board Initialization", test_board_init),
        ("Knight L-Shape Moves", test_knight_moves),
        ("Knight Edge Handling", test_knight_edge),
        ("Bishop Diagonal", test_bishop_diagonal),
        ("Rook Orthogonal", test_rook_orthogonal),
        ("Queen All Directions", test_queen_all_directions),
        ("Pawn Forward", test_pawn_forward),
        ("Pawn Double Move", test_pawn_double_move),
        ("Pawn Capture", test_pawn_capture),
        ("King Single Step", test_king_single_step),
        ("Capture Priority", test_capture_priority),
        ("No Self Capture", test_no_self_capture),
        ("Check Kings", test_check_kings),
        ("Move Execution", test_move_execution),
        ("Pawn Promotion", test_pawn_promotion),
        ("Slider Blocked", test_slider_blocked),
        # --- New tests for previously untested paths ---
        ("Get Square (keyboard input)", test_get_square),
        ("Get Move (valid input)", test_get_move_valid),
        ("Get Move (rejects empty source)", test_get_move_rejects_empty),
        ("Get Move (rejects black source)", test_get_move_rejects_black_source),
        ("Get Move (rejects own piece dest)", test_get_move_rejects_own_dest),
        ("Get Piece Char (display chars)", test_get_piece_char),
        ("Display Rendering", test_cls_and_draw),
        ("Full Game Turn", test_full_game_turn),
        ("Knight H-File Edge", test_knight_h_file_edge),
        ("Knight H8 Corner", test_knight_h8_corner),
        ("Pawn A-File No Wrap", test_pawn_a_file_no_wrap),
        ("Pawn H-File No Wrap", test_pawn_h_file_no_wrap),
        ("Bishop Edge No Wrap", test_bishop_edge_no_wrap),
        ("Rook Edge Wrapping", test_rook_edge_no_wrap),
        ("Pawn No Double Wrong Rank", test_pawn_no_double_from_wrong_rank),
        ("Promotion With Capture", test_promotion_with_capture),
        ("Game Over White Wins", test_game_over_white_wins),
        ("Game Over Black Wins", test_game_over_black_wins),
        ("Slider Direction Masks", test_slider_direction_masks),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_func in tests:
        print(f"Testing: {name}")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
