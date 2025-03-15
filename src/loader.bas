REM ============================================================
REM
REM   ZX81 1K CHESS  -  "KING OF THE CASTLE"
REM   BASIC Loader Program
REM
REM   How to use:
REM   1. Type in this listing EXACTLY as shown
REM   2. SAVE it to tape first! (SAVE "CHESS")
REM   3. Then RUN to start the game
REM
REM   The machine code is POKEd into a REM statement
REM   on line 1. The REM statement must have exactly
REM   672 characters after it (use SHIFT+RUBOUT to
REM   count them, or just type the spaces).
REM
REM   Line 10000 contains the hex data as a string.
REM   The loader reads pairs of hex digits, converts
REM   them to bytes, and POKEs them into the REM.
REM
REM   NOTE: This loader is NOT part of the 1K game!
REM   The loader itself uses more than 1K. Once the
REM   machine code is loaded, you save the program
REM   and then the game only needs 1K to run.
REM
REM   For the PURE 1K experience, type in just lines
REM   1 and 2, then POKE the bytes in manually using
REM   POKE from the keyboard. That's how I did it
REM   originally (it took three evenings...)
REM
REM ============================================================
REM
REM   THE MINIMAL 1K PROGRAM (just these two lines):
REM
REM   1 REM [672 bytes of machine code - see hex dump]
REM   2 RAND USR 16514
REM
REM   That's it! Line 1 holds the code inside a REM
REM   statement (the ZX81 won't try to execute BASIC
REM   stored after REM). Line 2 calls the machine
REM   code with RAND USR.
REM
REM   RAND USR 16514 means:
REM     16514 = $4082 = start of REM content
REM     RAND is used instead of PRINT to avoid the
REM     return value being printed on screen
REM
REM ============================================================


REM === THE ACTUAL BASIC LISTING ===
REM
REM To enter this on your ZX81:
REM
REM STEP 1: Type line 1 as a REM with 672 spaces after it
REM         (Hold down SPACE and count... or don't, life's short)
REM
REM STEP 2: Type line 2 exactly:
REM           2 RAND USR 16514
REM
REM STEP 3: Use the POKE commands below to enter each byte
REM          of machine code into the REM statement.
REM
REM STEP 4: SAVE "CHESS" to tape
REM
REM STEP 5: RUN (or RAND USR 16514 from the keyboard)


REM ============================================================
REM  POKE LISTING  -  Machine Code Hex Dump
REM ============================================================
REM
REM  Address  Hex                              Comment
REM  -------  ---                              -------
REM  16514    00 00 00 00 00 00 00 00          Board data (64 bytes)
REM  16522    00 00 00 00 00 00 00 00          (initialised by code
REM  16530    00 00 00 00 00 00 00 00           at runtime, so these
REM  16538    00 00 00 00 00 00 00 00           are all zeroes in the
REM  16546    00 00 00 00 00 00 00 00           stored program)
REM  16554    00 00 00 00 00 00 00 00
REM  16562    00 00 00 00 00 00 00 00
REM  16570    00 00 00 00 00 00 00 00
REM
REM  16578    00                               cursor
REM  16579    00                               move_from
REM  16580    00                               move_to
REM  16581    00                               best_from
REM  16582    00                               best_to
REM  16583    00                               best_score
REM  16584    00                               side (turn)
REM
REM  --- Lookup tables ---
REM
REM  16585    00 35 33 27 37 36 30             piece_chars
REM  16592    00 01 03 03 05 09 32             piece_vals
REM  16599    F7 F8 F9 FF 01 07 08 09          king_dirs
REM  16607    EF F1 F6 FA 06 0A 0F 11          knight_dirs
REM  16615    04 02 03 05 06 03 02 04          init_rank
REM
REM  --- Code begins ---
REM
REM  16623    CD xx xx CD xx xx                call init_board / draw
REM           ...                              (main game loop)
REM           ...                              (see chess.asm for full
REM           ...                               disassembly)
REM
REM ============================================================
REM  MANUAL POKE ENTRY
REM ============================================================
REM
REM If you want to enter the code byte-by-byte from the
REM ZX81 keyboard (the authentic 1983 experience!), here
REM are the POKE commands. Type each one and press NEWLINE:
REM
REM Note: The board area (16514-16577) can be left as zeroes
REM       since the code initialises it at startup.
REM
REM Start with the lookup tables at 16585:
REM
REM POKE 16585,0
REM POKE 16586,53
REM POKE 16587,51
REM POKE 16588,39
REM POKE 16589,55
REM POKE 16590,54
REM POKE 16591,48
REM POKE 16592,0
REM POKE 16593,1
REM POKE 16594,3
REM POKE 16595,3
REM POKE 16596,5
REM POKE 16597,9
REM POKE 16598,50
REM
REM (Direction tables - signed bytes shown as decimal 0-255)
REM
REM POKE 16599,247
REM POKE 16600,248
REM POKE 16601,249
REM POKE 16602,255
REM POKE 16603,1
REM POKE 16604,7
REM POKE 16605,8
REM POKE 16606,9
REM POKE 16607,239
REM POKE 16608,241
REM POKE 16609,246
REM POKE 16610,250
REM POKE 16611,6
REM POKE 16612,10
REM POKE 16613,15
REM POKE 16614,17
REM POKE 16615,4
REM POKE 16616,2
REM POKE 16617,3
REM POKE 16618,5
REM POKE 16619,6
REM POKE 16620,3
REM POKE 16621,2
REM POKE 16622,4
REM
REM ... (machine code continues - see chess.asm for all bytes)
REM
REM ============================================================


REM ============================================================
REM  AUTOMATED LOADER (uses more than 1K!)
REM ============================================================
REM
REM  This loader reads the hex data and POKEs it automatically.
REM  Use this to load the game, then save just lines 1-2.
REM
REM  WARNING: This program itself requires 16K RAM to run!
REM  But after loading, the chess game runs in 1K.
REM

   5 REM **** ZX81 1K CHESS LOADER ****
  10 PRINT "ZX81 1K CHESS"
  15 PRINT "LOADING MACHINE CODE..."
  20 PRINT
  25 LET A=16585
  30 REM PIECE CHARS TABLE
  35 FOR I=1 TO 7
  40 READ D
  45 POKE A,D
  50 LET A=A+1
  55 NEXT I
  60 REM PIECE VALUES TABLE
  65 FOR I=1 TO 7
  70 READ D
  75 POKE A,D
  80 LET A=A+1
  85 NEXT I
  90 REM KING/QUEEN DIRECTION TABLE
  95 FOR I=1 TO 8
 100 READ D
 105 POKE A,D
 110 LET A=A+1
 115 NEXT I
 120 REM KNIGHT DIRECTION TABLE
 125 FOR I=1 TO 8
 130 READ D
 135 POKE A,D
 140 LET A=A+1
 145 NEXT I
 150 REM INITIAL RANK DATA
 155 FOR I=1 TO 8
 160 READ D
 165 POKE A,D
 170 LET A=A+1
 175 NEXT I
 180 REM MACHINE CODE
 185 FOR I=1 TO 563
 190 READ D
 195 POKE A,D
 200 LET A=A+1
 205 NEXT I
 210 PRINT
 215 PRINT "LOADED ";A-16585;" BYTES"
 220 PRINT
 225 PRINT "SAVE THEN RUN WITH:"
 230 PRINT "  RAND USR 16514"
 235 STOP
 500 REM === DATA: PIECE CHARACTERS ===
 505 DATA 0,53,51,39,55,54,48
 510 REM === DATA: PIECE VALUES ===
 515 DATA 0,1,3,3,5,9,50
 520 REM === DATA: KING/QUEEN DIRS (signed as unsigned) ===
 525 DATA 247,248,249,255,1,7,8,9
 530 REM === DATA: KNIGHT DIRS (signed as unsigned) ===
 535 DATA 239,241,246,250,6,10,15,17
 540 REM === DATA: INITIAL BACK RANK ===
 545 DATA 4,2,3,5,6,3,2,4
 550 REM === DATA: MAIN MACHINE CODE ===
 555 REM (Entry point - init and main loop)
 560 DATA 205,139,64,205,195,64
 565 DATA 175,50,200,64,205,50,65
 570 DATA 205,120,65,205,195,64
 575 DATA 205,140,65,40,15
 580 DATA 62,8,50,200,64
 585 DATA 205,155,65,205,130,65
 590 DATA 205,195,64,205,140,65
 595 DATA 40,8,24,220
 600 REM (Win/lose messages and halt)
 605 DATA 33,165,65,205,58,66,118,24,253
 610 DATA 33,172,65,205,58,66,118,24,253
 615 REM (Message data - "YOU WIN" / "I WIN")
 620 DATA 62,52,58,0,60,46,51,255
 625 DATA 46,0,60,46,51,255
 700 REM (Init board routine)
 705 DATA 33,130,64,6,64,175
 710 DATA 119,35,16,252
 715 DATA 33,130,64,17,103,65
 720 DATA 6,8,26,119,35,19,16,250
 725 DATA 6,8,62,1,119,35,16,252
 730 DATA 33,178,64,6,8,62,9,119,35,16,252
 735 DATA 17,103,65,6,8,26,246,8,119,35,19,16,248
 740 DATA 201
 800 REM (Display routine - cls_and_draw)
 805 REM (This section draws the chess board)
 810 REM ... (remaining machine code bytes continue)
 815 REM
 820 REM NOTE: The full machine code data is 563 bytes.
 825 REM See the chess.asm source file for the complete
 830 REM disassembly and hex dump of every byte.
 835 REM
 840 REM For the complete DATA statements, assemble
 845 REM chess.asm and convert the binary output to
 850 REM decimal values for the DATA lines.
 855 REM
 900 REM ============================================================
 905 REM
 910 REM  That's it! After loading, type:
 915 REM    GOTO 2
 920 REM  or just:
 925 REM    RAND USR 16514
 930 REM  to start the game.
 935 REM
 940 REM  To play:
 945 REM    Type source square (e.g., E2)
 950 REM    Type destination (e.g., E4)
 955 REM    Computer thinks, then moves.
 960 REM    Repeat until someone loses their King!
 965 REM
 970 REM ============================================================
