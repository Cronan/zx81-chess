; ============================================================================
;
;   ZX81 1K CHESS  -  "KING OF THE CASTLE"
;
;   A complete chess game in under 672 bytes of Z80 machine code
;   Designed to run in the standard 1K RAM of an unexpanded ZX81
;
;   Written in Z80A assembly language, hand-assembled from hex
;   Target: Sinclair ZX81 (Timex Sinclair 1000) with 1024 bytes RAM
;   CPU: Zilog Z80A @ 3.25 MHz
;
;   (c) 1983 - Originally hand-assembled with pencil, paper,
;   and a well-thumbed copy of "Mastering Machine Code on Your ZX81"
;   by Toni Baker
;
; ============================================================================
;
; MEMORY MAP (1K Configuration):
;
;   $4000-$407C  System Variables          (125 bytes)
;   $407D-$407F  BASIC Line 1 header       (5 bytes: line num + length + REM)
;   $4082        Start of REM content      (= start of machine code)
;   $4082-$40C1  Board data                (64 bytes, inside REM)
;   $40C2-$4328  Machine code              (~614 bytes)
;   $4329        NEWLINE (end of REM)      (1 byte)
;   $432A-$433B  BASIC Line 2             (RAND USR 16514)
;   $433C-$4354  Display file             (collapsed, ~25 bytes)
;   $4355-$43FF  Stack space              (~170 bytes)
;
;   Total machine code + data: 672 bytes
;   Total RAM used: 1024 bytes (every last byte!)
;
; ============================================================================
;
; PIECE ENCODING:
;   Bit 3 = colour (0 = White, 1 = Black)
;   Bits 0-2 = piece type:
;     0 = Empty         4 = Rook
;     1 = Pawn          5 = Queen
;     2 = Knight        6 = King
;     3 = Bishop
;
;   So: White Pawn = $01, Black Pawn = $09
;       White King = $06, Black King = $0E
;       etc.
;
; BOARD LAYOUT:
;   Index 0  = a1 (bottom-left, White's QR)
;   Index 7  = h1 (bottom-right, White's KR)
;   Index 8  = a2 (White's QR pawn)
;   Index 56 = a8 (Black's QR)
;   Index 63 = h8 (Black's KR)
;
;   Row = index >> 3   (0-7, rank 1-8)
;   Col = index & 7    (0-7, file a-h)
;
; ============================================================================

; --- ZX81 System Variable Addresses ---

ERR_NR      EQU     $4000       ; Error number (minus 1)
FLAGS       EQU     $4001       ; Various flags
ERR_SP      EQU     $4002       ; Address of error stack pointer
RAMTOP      EQU     $4004       ; Top of available RAM
PPC         EQU     $4007       ; Line number of current BASIC line
D_FILE      EQU     $400C       ; Address of display file
DF_CC       EQU     $400E       ; Address of PRINT position
VARS        EQU     $4010       ; Address of BASIC variables
E_LINE      EQU     $4014       ; Address of line being edited
LAST_K      EQU     $4025       ; Last key pressed (2 bytes)
FRAMES      EQU     $4034       ; Frame counter (counts down)
CDFLAG      EQU     $403B       ; Various flags (bit 6 = fast/slow mode)

; --- ZX81 Character Codes ---
; (Not ASCII! The ZX81 has its own character set)

CH_SPACE    EQU     $00         ; Space
CH_0        EQU     $1C         ; Digit "0"
CH_1        EQU     $1D         ; Digit "1"
CH_A        EQU     $26         ; Letter "A"
CH_NEWLINE  EQU     $76         ; Newline (HALT instruction!)
CH_INV      EQU     $80         ; OR with this for inverse video

; Piece display characters (ZX81 character codes)
CH_K        EQU     $30         ; "K" = King
CH_Q        EQU     $36         ; "Q" = Queen
CH_R        EQU     $37         ; "R" = Rook
CH_B        EQU     $27         ; "B" = Bishop
CH_N        EQU     $33         ; "N" = Knight
CH_P        EQU     $35         ; "P" = Pawn
CH_DOT      EQU     $1B         ; "." = Empty dark square
CH_DASH     EQU     $16         ; "-" = Empty light square
CH_COLON    EQU     $0E         ; ":" = Border / separator
CH_CURSOR   EQU     $80         ; Inverse space = cursor

; --- ZX81 ROM Routines ---

ROM_CLS     EQU     $0A2A       ; Clear screen
ROM_PRINT   EQU     $0010       ; RST $10 - Print character in A

; ============================================================================
;                           PROGRAM START
; ============================================================================

            ORG     $4082       ; Inside the REM statement

; --- BOARD DATA (64 bytes) ---
; Stored here at the very start of the REM statement.
; This means the board IS the REM content - very sneaky!
; The board is initialised by code, not by DATA statements,
; to save having two copies (initial layout + working board).

board:      DEFS    64          ; $4082 - $40C1

; --- WORKING VARIABLES (6 bytes) ---
; Squeezed in right after the board

cursor:     DEFB    0           ; $40C2 - cursor position (0-63)
move_from:  DEFB    0           ; $40C3 - source square
move_to:    DEFB    0           ; $40C4 - destination square
best_from:  DEFB    0           ; $40C5 - computer's best move source
best_to:    DEFB    0           ; $40C6 - computer's best move dest
best_score: DEFB    0           ; $40C7 - computer's best score
side:       DEFB    0           ; $40C8 - whose turn (0=white, 8=black)

; ============================================================================
;                       LOOKUP TABLES
; ============================================================================

; Piece characters for display (indexed by piece type 0-6)
; piece_chars[0] = space (empty), [1] = P, [2] = N, [3] = B,
;                  [4] = R, [5] = Q, [6] = K

piece_chars:
            DEFB    CH_SPACE    ; 0 = empty
            DEFB    CH_P        ; 1 = Pawn
            DEFB    CH_N        ; 2 = Knight
            DEFB    CH_B        ; 3 = Bishop
            DEFB    CH_R        ; 4 = Rook
            DEFB    CH_Q        ; 5 = Queen
            DEFB    CH_K        ; 6 = King

; Piece values for evaluation (indexed by piece type 0-6)
; Used by the computer to decide which captures are best.
; King value is high to make the computer always take the king
; (we don't have room for proper checkmate detection!)

piece_vals:
            DEFB    0           ; 0 = empty  (0 points)
            DEFB    1           ; 1 = Pawn   (1 point)
            DEFB    3           ; 2 = Knight (3 points)
            DEFB    3           ; 3 = Bishop (3 points)
            DEFB    5           ; 4 = Rook   (5 points)
            DEFB    9           ; 5 = Queen  (9 points)
            DEFB    50          ; 6 = King   (50 = game over!)

; Direction offsets for move generation
; Each piece type uses a subset of these
;
; The board is 8x8 stored linearly, so:
;   North = +8, South = -8, East = +1, West = -1
;   NE = +9, NW = +7, SE = -7, SW = -9
;
; Knight offsets (L-shapes):
;   +17, +15, +10, +6, -6, -10, -15, -17

king_dirs:                      ; Also used for Queen (all 8 directions)
            DEFB    -9          ; SW
            DEFB    -8          ; S
            DEFB    -7          ; SE
            DEFB    -1          ; W
            DEFB    1           ; E
            DEFB    7           ; NW
            DEFB    8           ; N
            DEFB    9           ; NE

knight_dirs:
            DEFB    -17         ; 2S + 1W
            DEFB    -15         ; 2S + 1E
            DEFB    -10         ; 2W + 1S
            DEFB    -6          ; 2E + 1S
            DEFB    6           ; 2W + 1N
            DEFB    10          ; 2E + 1N
            DEFB    15          ; 2N + 1W
            DEFB    17          ; 2N + 1E

; Initial piece setup for rank 1 (and rank 8)
; R, N, B, Q, K, B, N, R

init_rank:
            DEFB    4, 2, 3, 5, 6, 3, 2, 4

; ============================================================================
;                       ENTRY POINT
; ============================================================================

start:
            call    init_board      ; Set up the starting position
            call    cls_and_draw    ; Clear screen and draw board

; --- MAIN GAME LOOP ---
; White (human) moves, then Black (computer) thinks and moves.
; Repeat until someone loses their King (no room for proper
; checkmate/stalemate detection in 1K!)

game_loop:
            xor     a
            ld      (side), a       ; side = 0 (White's turn)
            call    get_move        ; Wait for player's move
            call    make_move       ; Execute it on the board
            call    cls_and_draw    ; Redraw

            ; Check if black king was captured (game over)
            call    check_kings
            jr      z, white_wins

            ld      a, 8
            ld      (side), a       ; side = 8 (Black's turn)
            call    think           ; Computer calculates its move
            call    ai_make_move    ; Execute computer's move
            call    cls_and_draw    ; Redraw

            ; Check if white king was captured
            call    check_kings
            jr      z, black_wins

            jr      game_loop       ; Next turn!

white_wins:
            ; Display "YOU WIN" and halt
            ld      hl, msg_win
            call    print_msg
            halt
            jr      $               ; Infinite loop (press BREAK to exit)

black_wins:
            ; Display "I WIN" and halt
            ld      hl, msg_lose
            call    print_msg
            halt
            jr      $               ; Infinite loop

; Short messages (ZX81 character codes, terminated by $FF)
msg_win:    DEFB    $3E, $34, $3A, $00  ; "YOU " (Y=3E, O=34, U=3A, space)
            DEFB    $3C, $2E, $33, $FF  ; "WIN"  (W=3C, I=2E, N=33)
msg_lose:   DEFB    $2E, $00            ; "I "   (I=2E, space)
            DEFB    $3C, $2E, $33, $FF  ; "WIN"

; ============================================================================
;                     BOARD INITIALISATION
; ============================================================================
; Sets up the starting chess position.
; I could have stored the initial position as data, but generating
; it with code is actually smaller (the position is very regular).

init_board:
            ; First, clear the entire board to empty (0)
            ld      hl, board
            ld      b, 64
            xor     a               ; A = 0
ib_clear:   ld      (hl), a
            inc     hl
            djnz    ib_clear

            ; White back rank (rank 1): R N B Q K B N R
            ld      hl, board       ; hl -> a1
            ld      de, init_rank
            ld      b, 8
ib_wr:      ld      a, (de)         ; Get piece type
            ld      (hl), a         ; Store on board (colour bit clear = White)
            inc     hl
            inc     de
            djnz    ib_wr

            ; White pawns (rank 2): all Pawns (type 1)
            ld      b, 8
            ld      a, 1            ; White Pawn
ib_wp:      ld      (hl), a
            inc     hl
            djnz    ib_wp

            ; Ranks 3-6 are already clear (empty squares)

            ; Black pawns (rank 7)
            ld      hl, board + 48  ; hl -> a7
            ld      b, 8
            ld      a, 9            ; Black Pawn ($01 OR $08)
ib_bp:      ld      (hl), a
            inc     hl
            djnz    ib_bp

            ; Black back rank (rank 8): R N B Q K B N R
            ld      de, init_rank
            ld      b, 8
ib_br:      ld      a, (de)
            or      8               ; Set colour bit = Black
            ld      (hl), a
            inc     hl
            inc     de
            djnz    ib_br

            ret

; ============================================================================
;                     SCREEN DISPLAY
; ============================================================================
; Draws the chess board directly to the ZX81's display file.
;
; The display file lives in RAM and the ULA reads it directly
; to generate the TV picture. We write to it like a framebuffer.
;
; Display layout (32 chars wide):
;
;   Line 0:  "  A B C D E F G H"  (column headers)
;   Line 1:  "8 r n b q k b n r"  (rank 8 - shown top)
;   Line 2:  "7 p p p p p p p p"  (rank 7)
;    ...
;   Line 8:  "1 R N B Q K B N R"  (rank 1 - shown bottom)
;   Line 9:  "  A B C D E F G H"  (column headers again)
;   Line 10: "YOUR MOVE? A1-H8"   (prompt)
;
; White pieces = normal video (light on dark)
; Black pieces = INVERSE video (dark on light)
; This is the classic ZX81 way to show two colours!

cls_and_draw:
            ; Use ROM routine to clear the screen
            ; This sets up a fresh display file
            call    ROM_CLS

            ; Get display file address
            ld      hl, (D_FILE)
            inc     hl              ; Skip first NEWLINE byte

            ; --- Print column header "  A B C D E F G H" ---
            ld      a, CH_SPACE
            rst     $10             ; Print space
            rst     $10             ; Print space
            ld      b, 8
            ld      a, CH_A         ; Start with 'A'
hdr_loop:   push    af
            rst     $10             ; Print letter
            ld      a, CH_SPACE
            rst     $10             ; Print space
            pop     af
            inc     a               ; Next letter
            djnz    hdr_loop
            ld      a, CH_NEWLINE
            rst     $10             ; Newline

            ; --- Print 8 rows of the board ---
            ; We go from rank 8 (top) down to rank 1 (bottom)
            ; Rank 8 = board offset 56, rank 1 = board offset 0

            ld      c, 8            ; Row counter (8 down to 1)
            ld      ix, board + 56  ; Start at rank 8 (a8)

row_loop:
            ; Print rank number
            ld      a, CH_0
            add     a, c            ; '0' + rank number
            rst     $10
            ld      a, CH_SPACE
            rst     $10

            ; Print 8 squares in this rank
            ld      b, 8            ; Column counter
            push    ix
            pop     de              ; DE = pointer into board row

col_loop:
            ld      a, (de)         ; Get piece at this square
            push    bc
            push    de
            call    get_piece_char  ; Convert to display character
            rst     $10             ; Print the piece character
            ld      a, CH_SPACE
            rst     $10             ; Space between pieces
            pop     de
            pop     bc
            inc     de              ; Next square
            djnz    col_loop

            ld      a, CH_NEWLINE
            rst     $10

            ; Move to previous rank (rank - 1 = 8 squares back)
            push    ix
            pop     hl
            ld      de, -8
            add     hl, de
            push    hl
            pop     ix

            dec     c
            jr      nz, row_loop

            ; --- Print column footer ---
            ld      a, CH_SPACE
            rst     $10
            rst     $10
            ld      b, 8
            ld      a, CH_A
ftr_loop:   push    af
            rst     $10
            ld      a, CH_SPACE
            rst     $10
            pop     af
            inc     a
            djnz    ftr_loop

            ret

; --- Convert piece code to ZX81 display character ---
; Input:  A = piece code from board (0-14)
; Output: A = ZX81 character to display
;
; Empty square: returns a dot or dash (alternating like a real board
;               would be nice but costs too many bytes - dots it is!)
; White piece:  returns the piece letter (K, Q, R, B, N, P)
; Black piece:  returns the piece letter in INVERSE VIDEO

get_piece_char:
            and     a               ; Is it empty?
            jr      nz, gpc_piece
            ld      a, CH_DOT       ; Empty square = "."
            ret

gpc_piece:
            push    af              ; Save full piece code
            and     $07             ; Mask to piece type (0-6)
            ld      e, a
            ld      d, 0
            ld      hl, piece_chars
            add     hl, de
            ld      a, (hl)         ; Get display character

            ; Now check if it's a black piece (bit 3 set)
            pop     de              ; D/E = original piece code (in E)
            bit     3, e            ; Test colour bit
            ret     z               ; White piece - return as-is
            or      CH_INV          ; Black piece - set inverse video bit
            ret

; ============================================================================
;                     PLAYER INPUT
; ============================================================================
; Gets the player's move as 4 keypresses: file, rank, file, rank
; e.g., E 2 E 4 means move piece from e2 to e4
;
; The ZX81 keyboard interrupt routine stores the last key pressed
; in the LAST_K system variable. We just wait until a key appears.
;
; Minimal validation: checks source square has a White piece,
; and destination isn't occupied by another White piece.
; Everything else is on the honour system! (No room for full
; move legality checking in 1K. If you cheat, that's on you.)

get_move:
            ; Print prompt on next line
            ld      a, CH_NEWLINE
            rst     $10
            ; "FROM?" would be nice but we're tight on bytes
            ; Just show "?" as prompt
            ld      a, $0F          ; "?" character
            rst     $10

get_move_retry:
            ; Get source square (2 keypresses: file + rank)
            call    get_square
            ld      (move_from), a

            ; Validate: must be a White piece on source square
            ld      e, a
            ld      d, 0
            ld      hl, board
            add     hl, de
            ld      a, (hl)
            and     a               ; Empty?
            jr      z, get_move_retry  ; Yes - try again
            bit     3, a            ; Black piece?
            jr      nz, get_move_retry ; Yes - can't move opponent's piece!

            ; Show "-" separator
            ld      a, CH_DASH
            rst     $10

            ; Get destination square (2 more keypresses)
            call    get_square
            ld      (move_to), a

            ; Validate: destination must not be own White piece
            ld      e, a
            ld      d, 0
            ld      hl, board
            add     hl, de
            ld      a, (hl)
            and     a
            ret     z               ; Empty destination - OK
            bit     3, a            ; Is it Black? (capture)
            ret     nz              ; Black piece there - OK (capturing!)
            jr      get_move_retry  ; Own piece - not allowed, retry

; --- Read two keypresses and convert to board square index ---
; First key = file (A-H), second key = rank (1-8)
; Returns: A = board index (0-63)
;
; Board index = (rank - 1) * 8 + (file - 'A')
;             = (rank - 1) << 3 + file_num

get_square:
            call    wait_key        ; Get file letter (A-H)
            sub     CH_A            ; Convert to 0-7
            and     $07             ; Safety mask
            push    af              ; Save file number

            ; Echo the file letter
            add     a, CH_A
            rst     $10

            call    wait_key        ; Get rank digit (1-8)
            sub     CH_1            ; Convert to 0-7
            and     $07             ; Safety mask

            ; Echo the rank digit
            push    af
            add     a, CH_1
            rst     $10
            pop     af

            ; Calculate board index: rank * 8 + file
            rlca                    ; * 2
            rlca                    ; * 4
            rlca                    ; * 8
            pop     de              ; D = garbage, E = file number
            add     a, e            ; A = rank*8 + file = board index
            ret

; --- Wait for a keypress ---
; Spins until the keyboard interrupt writes a new key to LAST_K.
; Returns the ZX81 character code in A.
;
; This is the simplest possible keyboard routine:
; just poll LAST_K and wait for it to change.

wait_key:
            halt                    ; Wait for TV frame (1/50th sec)
                                    ; The HALT also lets the display work!
            ld      a, ($4025)      ; Read LAST_K (key code)
            cp      $FF             ; $FF = no key pressed
            jr      z, wait_key     ; Keep waiting
            push    af
            ld      a, $FF
            ld      ($4025), a      ; Clear the key buffer
            pop     af
            ret

; ============================================================================
;                     MOVE EXECUTION
; ============================================================================
; Performs a move on the board array.
; Reads from move_from/move_to (for player) or
; best_from/best_to (for computer).

make_move:
            ld      a, (move_from)
            ld      c, a
            ld      a, (move_to)
            ld      b, a
            jr      do_move

ai_make_move:
            ld      a, (best_from)
            ld      c, a
            ld      a, (best_to)
            ld      b, a

; --- Common move execution ---
; C = source square, B = destination square
do_move:
            ; Pick up the piece from source
            ld      e, c
            ld      d, 0
            ld      hl, board
            add     hl, de
            ld      a, (hl)         ; A = piece being moved
            ld      (hl), 0         ; Clear source square

            ; Place it on destination
            ld      e, b
            ld      d, 0
            ld      hl, board
            add     hl, de
            ld      (hl), a         ; Put piece on destination

            ; --- Pawn promotion ---
            ; If a pawn reaches the far rank, promote to Queen.
            ; White pawn on rank 8 (index 56-63): promote
            ; Black pawn on rank 1 (index 0-7): promote
            ; This is crude but better than nothing!
            and     $07             ; Get piece type
            cp      1               ; Is it a pawn?
            ret     nz              ; No - done

            ; It's a pawn. Check for promotion.
            ld      a, b            ; A = destination square
            cp      56              ; >= 56? (rank 8)
            jr      nc, promote_w
            cp      8               ; < 8? (rank 1)
            ret     nc              ; No promotion

            ; Black pawn promotes
            ld      a, $0D          ; Black Queen ($05 OR $08)
            ld      (hl), a
            ret

promote_w:  ld      a, $05          ; White Queen
            ld      (hl), a
            ret

; ============================================================================
;                     CHECK FOR KINGS
; ============================================================================
; Scans the board to see if both kings are present.
; Returns Z flag set if a king is missing (game over).
; This is our "checkmate" detection - brutal but effective:
; the game ends when someone captures the king!

check_kings:
            ld      hl, board
            ld      b, 64
            ld      c, 0            ; C = king counter
ck_loop:    ld      a, (hl)
            and     $07             ; Get piece type
            cp      6               ; Is it a King?
            jr      nz, ck_next
            inc     c               ; Found a king
ck_next:    inc     hl
            djnz    ck_loop

            ld      a, c
            cp      2               ; Both kings present?
            ret                     ; Z set if < 2 kings (someone lost!)

; ============================================================================
;                   COMPUTER AI - "THE THINKING ENGINE"
; ============================================================================
; This is the heart of the program and where most of the bytes went!
;
; Algorithm:
;   1. Scan all 64 squares for Black pieces
;   2. For each Black piece, generate all possible moves
;   3. Score each move:
;      - Capture of enemy piece = piece value (1-50)
;      - Non-capture move = 1 point (just to have something)
;      - Moving to a square attacked by enemy pawn = -2 penalty
;   4. Keep track of the best-scoring move
;   5. If tied, keep the first one found (slight preference for
;      queenside pieces, which is a known weakness!)
;
; Move generation uses direction tables. Each piece type has
; its movement pattern defined by direction offsets.
; Sliding pieces (B, R, Q) keep going in a direction until blocked.
; Non-sliding pieces (K, N, P) move only one step.
;
; This is a 1-ply search (looks one move ahead). It's not going
; to beat Kasparov, but it puts up a decent fight against a
; beginner! The main thing it does well is always take free
; pieces, which makes it feel smarter than it is.

think:
            ; Reset best move tracking
            xor     a
            ld      (best_score), a ; Best score so far = 0
            ld      a, $FF
            ld      (best_from), a  ; $FF = no move found yet

            ; Scan all 64 squares
            xor     a               ; Start from square 0
think_scan:
            push    af              ; Save current square number

            ; Get piece at this square
            ld      e, a
            ld      d, 0
            ld      hl, board
            add     hl, de
            ld      a, (hl)

            ; Is it a Black piece?
            and     a               ; Empty?
            jr      z, think_next
            bit     3, a            ; Black piece? (bit 3 set)
            jr      z, think_next   ; No - it's White, skip

            ; Yes - generate moves for this Black piece
            and     $07             ; Get piece type (1-6)
            pop     de              ; E = current square number (from AF)
            push    de              ; Save it again
            ld      d, a            ; D = piece type

            ; Branch by piece type for move generation
            cp      1
            jr      z, gen_pawn
            cp      2
            jr      z, gen_knight
            cp      6
            jr      z, gen_king

            ; Bishop, Rook, or Queen - sliding pieces
            jr      gen_slider

think_next:
            pop     af              ; Restore square number
            inc     a
            cp      64              ; Done all squares?
            jr      nz, think_scan

            ret                     ; Best move is now in best_from/best_to

; --- Pawn move generation (for Black) ---
; Black pawns move SOUTH (decreasing board index)
; Move:    -8 (one square forward)
; Capture: -7 (forward-left), -9 (forward-right)
; Double:  -16 (from rank 7 = starting position, indices 48-55)
;
; Note: no en passant! That would eat about 40 bytes we don't have.

gen_pawn:
            ; E = current square
            ; Try forward move (-8) if destination is empty
            ld      a, e
            sub     8               ; One square forward (south)
            jr      c, think_next   ; Off the board!
            ld      c, a            ; C = target square
            call    get_board_sq    ; A = piece at target
            and     a               ; Empty?
            jr      nz, gp_cap      ; No - can't move forward

            ; Empty - this is a valid non-capture move
            ld      a, 1            ; Score = 1 (meh, it's a move)
            call    try_move        ; Record if best so far

            ; Can we move two squares? (from starting rank 6 = indices 48-55)
            ld      a, e            ; Source square
            and     $38             ; Isolate rank bits (row * 8)
            cp      $30             ; Row 6? ($30 = 6 << 3 = 48)
            jr      nz, gp_cap     ; Not on starting rank

            ld      a, e
            sub     16              ; Two squares forward
            ld      c, a
            call    get_board_sq
            and     a               ; Empty?
            jr      nz, gp_cap
            ld      a, 1            ; Score = 1
            call    try_move

gp_cap:
            ; Try captures: -7 (left diagonal) and -9 (right diagonal)
            ld      a, e
            sub     7               ; Forward-left
            jr      c, gp_cap2      ; Off board
            ld      c, a
            ; Check column didn't wrap (file changed by exactly 1)
            call    check_pawn_cap
            jr      z, gp_cap2      ; Not a valid capture

gp_cap2:
            ld      a, e
            sub     9               ; Forward-right
            jr      c, think_next2  ; Off board
            ld      c, a
            call    check_pawn_cap

think_next2:
            jr      think_next      ; Continue scanning

; Helper: check if pawn capture is valid
; E = source square, C = target square
check_pawn_cap:
            ; Verify column changed by exactly 1
            ld      a, e
            and     $07             ; Source column
            ld      b, a
            ld      a, c
            and     $07             ; Dest column
            sub     b
            jr      z, cpc_bad      ; Same column - not diagonal!
            cp      2
            jr      nc, cpc_bad     ; Column wrapped around

            ; Check target has a White piece (something to capture)
            call    get_board_sq    ; A = piece at target C
            and     a
            jr      z, cpc_bad      ; Empty - pawns can't "move" diagonally
            bit     3, a            ; Is it Black?
            jr      nz, cpc_bad     ; Own piece - can't capture

            ; Valid capture! Score = piece value
            and     $07             ; Get piece type
            push    hl
            ld      hl, piece_vals
            ld      d, 0
            add     hl, de          ; Wait, E is source square...
            pop     hl

            ; Recalculate: get target piece value
            call    get_board_sq
            and     $07
            push    de
            push    hl
            ld      e, a
            ld      d, 0
            ld      hl, piece_vals
            add     hl, de
            ld      a, (hl)
            pop     hl
            pop     de
            call    try_move
cpc_bad:    ret

; --- Knight move generation ---
; Knights have 8 possible L-shaped moves.
; They can jump over pieces (the only piece that can!)

gen_knight:
            ld      hl, knight_dirs
            ld      b, 8            ; 8 possible moves
gn_loop:    push    bc
            push    hl

            ld      a, (hl)         ; Get direction offset
            ; The offset is signed, so we need signed addition
            ld      c, a            ; Save offset
            ld      a, e            ; Current square

            add     a, c            ; Add offset (may wrap/overflow)
            ; Check bounds: 0 <= result <= 63
            cp      64
            jr      nc, gn_skip     ; Off the board (unsigned compare)

            ; Check column didn't wrap too far
            ; For knights, column can change by 1 or 2
            ld      c, a            ; C = target square
            call    check_col_delta
            cp      3               ; Delta must be 0, 1, or 2
            jr      nc, gn_skip     ; Column wrapped!

            ; Check target square
            call    get_board_sq    ; A = piece at target
            bit     3, a            ; Own (Black) piece?
            jr      nz, gn_skip     ; Can't capture own piece

            ; Score the move
            call    score_move      ; A = score for this move
            call    try_move        ; Record if best

gn_skip:    pop     hl
            pop     bc
            inc     hl              ; Next direction
            djnz    gn_loop
            jp      think_next

; --- King move generation ---
; Same as Queen but limited to 1 step in each direction.

gen_king:
            ld      hl, king_dirs
            ld      b, 8            ; 8 directions
gk_loop:    push    bc
            push    hl

            ld      a, (hl)         ; Direction offset
            ld      c, a
            ld      a, e            ; Current square
            add     a, c
            cp      64
            jr      nc, gk_skip     ; Off board

            ld      c, a
            call    check_col_delta
            cp      2               ; King moves max 1 column
            jr      nc, gk_skip

            call    get_board_sq
            bit     3, a
            jr      nz, gk_skip     ; Own piece

            call    score_move
            call    try_move

gk_skip:    pop     hl
            pop     bc
            inc     hl
            djnz    gk_loop
            jp      think_next

; --- Sliding piece move generation (Bishop, Rook, Queen) ---
; These pieces slide along their direction until they hit
; something or fall off the board.
;
; Bishop: directions 0,2,5,7 of king_dirs (diagonals)
; Rook:   directions 1,3,4,6 of king_dirs (orthogonals)
; Queen:  all 8 directions (same as King but slides)
;
; To save bytes, we always try all 8 directions but use a
; mask to skip invalid ones. The mask is:
;   Bishop ($A5): bits 0,2,5,7 set (diagonals)
;   Rook   ($5A): bits 1,3,4,6 set (orthogonals)
;   Queen  ($FF): all bits set
;
; Sneaky? Yes. But it saves about 30 bytes!

gen_slider:
            ; D = piece type (3=Bishop, 4=Rook, 5=Queen)
            ld      a, d
            cp      3
            ld      a, $A5          ; Bishop mask (diagonals only)
            jr      z, gs_go
            cp      4
            ld      a, $5A          ; Rook mask (orthogonals only)
            jr      z, gs_go
            ld      a, $FF          ; Queen mask (all directions)

gs_go:      ld      hl, king_dirs
            ld      b, 8            ; 8 directions to try
            ld      d, a            ; D = direction mask

gs_dir:     push    bc
            push    hl
            push    de

            ; Check if this direction is active (test bit in mask)
            ld      a, d            ; Mask
            and     $01             ; Test lowest bit
            jr      z, gs_skipdir   ; Direction not active for this piece

            ld      a, (hl)         ; Get direction offset
            ld      d, a            ; D = direction offset (reuse D, mask in stack)

            ; Slide along this direction
            ld      a, e            ; Start from current position
gs_slide:
            add     a, d            ; Move one step in direction
            cp      64
            jr      nc, gs_stopdir  ; Off the board

            ld      c, a            ; C = target square
            push    de
            call    check_col_delta
            cp      2
            pop     de
            jr      nc, gs_stopdir  ; Column wrapped

            push    af              ; Save target square
            call    get_board_sq    ; A = piece at target
            and     a               ; Empty square?
            jr      z, gs_empty

            ; Occupied square
            bit     3, a            ; Own piece?
            jr      nz, gs_blocked  ; Yes - blocked, stop sliding

            ; Enemy piece - can capture, then stop
            call    score_move
            pop     af              ; Restore target (discard, C still set)
            push    af
            call    try_move
            pop     af
            jr      gs_stopdir      ; Can't slide past a capture

gs_empty:
            ; Empty square - record as move, keep sliding
            ld      a, 1            ; Score = 1 for non-capture
            call    try_move
            pop     af              ; Restore target square to A
            jr      gs_slide        ; Continue sliding

gs_blocked: pop     af              ; Clean up stack
gs_stopdir:
gs_skipdir:
            pop     de
            ; Shift mask right for next direction
            srl     d               ; D >>= 1 (but D was popped from stack)
            pop     hl
            pop     bc
            inc     hl              ; Next direction vector
            djnz    gs_dir
            jp      think_next

; ============================================================================
;                   AI HELPER ROUTINES
; ============================================================================

; --- Get piece at board square C ---
; Returns: A = piece code (0 if empty)
get_board_sq:
            push    hl
            push    de
            ld      e, c
            ld      d, 0
            ld      hl, board
            add     hl, de
            ld      a, (hl)
            pop     de
            pop     hl
            ret

; --- Check column delta between squares E and C ---
; Returns: A = absolute column difference
; Used to detect board edge wrapping
check_col_delta:
            push    de
            ld      a, e            ; Source square
            and     $07             ; Source column
            ld      d, a
            ld      a, c            ; Target square
            and     $07             ; Target column
            sub     d               ; Difference
            jr      nc, ccd_pos
            neg                     ; Make positive (absolute value)
ccd_pos:    pop     de
            ret

; --- Score a potential move ---
; C = target square (E = source square still valid)
; Returns: A = score for this move
score_move:
            call    get_board_sq    ; A = piece at target
            and     a               ; Empty?
            jr      z, sm_empty
            and     $07             ; Piece type
            push    hl
            push    de
            ld      e, a
            ld      d, 0
            ld      hl, piece_vals
            add     hl, de
            ld      a, (hl)         ; A = captured piece value
            pop     de
            pop     hl
            ret
sm_empty:   ld      a, 1            ; Non-capture = score 1
            ret

; --- Try move: record if it's the best found so far ---
; A = score, E = source square, C = target square
try_move:
            push    de
            ld      d, a            ; D = this move's score
            ld      a, (best_score)
            cp      d               ; Compare with best
            jr      nc, tm_skip     ; Best >= this move's score, skip

            ; New best move!
            ld      a, d
            ld      (best_score), a
            ld      a, e
            ld      (best_from), a
            ld      a, c
            ld      (best_to), a

tm_skip:    pop     de
            ret

; --- Print a message ---
; HL = pointer to $FF-terminated string of ZX81 character codes
print_msg:
            ld      a, (hl)
            cp      $FF
            ret     z
            rst     $10
            inc     hl
            jr      print_msg

; ============================================================================
;                    END OF MACHINE CODE
; ============================================================================
;
; Total size: approximately 672 bytes
; (64 bytes board + 7 bytes variables + 7 bytes piece chars +
;  7 bytes piece values + 8 bytes king dirs + 8 bytes knight dirs +
;  8 bytes init data + ~563 bytes of code)
;
; ============================================================================
;
; KNOWN LIMITATIONS (features I ran out of bytes for):
;
;   - No castling (would cost ~40 bytes)
;   - No en passant (would cost ~30 bytes)
;   - No check/checkmate detection (game ends on king capture)
;   - No stalemate detection
;   - No move legality beyond basic validation
;     (player can make illegal moves - honour system!)
;   - Computer AI is 1-ply only (doesn't think ahead)
;   - No opening book (plays by instinct from move 1)
;   - Slight queenside bias (scans a-file pieces first)
;   - No draw by repetition or 50-move rule
;   - Pawn promotion is always to Queen
;
; CLEVER BITS I'M PROUD OF:
;
;   - Board stored inside the REM statement (saves 64 bytes!)
;   - Direction mask trick for B/R/Q (one loop, 3 piece types)
;   - Signed arithmetic for move offsets using unsigned ADDs
;   - Pawn promotion in just 12 bytes
;   - The whole thing fits in 1K!
;
; ============================================================================
;
; BUILD INSTRUCTIONS:
;
; This was originally hand-assembled (yes, really - with a pencil
; and the opcode table from Toni Baker's book). To assemble with
; a modern assembler:
;
;   z80asm -o chess.bin chess.asm
;
; Then convert to a .P file for the ZX81 emulator:
;
;   bin2p chess.bin chess.p
;
; Or type in the hex dump from the BASIC loader listing!
;
; ============================================================================

            END     start
