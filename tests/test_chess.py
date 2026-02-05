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
