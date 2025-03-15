```
 ___  ___  __   ___  ____  ___  ___  __  __
|   \/   | \ \ / / |/ ___||_ _|/ _ \|  \/  \ \ \/ /
| |\  /| |  \   /    \___ \ | || | | | |\/| |\ \  /
| | \/ | |   | |     ___) || || |_| | |  | | / /\ \
|_|    |_|   |_|    |____/|___|\___/|_|  |_|/_/  \_\
```

# My Story: A 14-Year-Old, a ZX81, and a Dream

---

## Christmas 1981

It came in a white box, smaller than I expected. My dad had ordered it from an advert in the back of a Sunday newspaper supplement. The **Sinclair ZX81** - Britain's cheapest computer, yours for 49.95 in kit form or 69.95 ready-built. Ours was ready-built. Dad wasn't much for soldering.

The box contained:
- One ZX81 computer (about the size of a paperback book)
- One TV lead (RF modulator)
- One power supply (9V DC, ran hot enough to fry an egg)
- One manual (the famous Sinclair BASIC programming manual)
- No monitor (use your telly)
- No tape recorder (use your own)
- No software (write your own)

I plugged it into the family television, connected the power, and was greeted by the now-iconic inverse-K cursor blinking at me from a white screen.

```
  ____________________
 |                    |
 | K                  |
 |                    |
 |                    |
 |____________________|

    (The ZX81 boot screen.
     That K cursor meant
     "I'm ready. What do
     you want me to do?")
```

I typed my first program:

```
10 PRINT "HELLO"
20 GOTO 10
RUN
```

The screen filled with "HELLO" over and over. I was hooked.

---

## The 1K Problem

The ZX81 came with 1 kilobyte of RAM. One thousand and twenty-four bytes. To understand how little that is:

- This paragraph is about 300 bytes
- A single smartphone photo is about 3,000,000 bytes
- The ZX81 had roughly enough memory for three tweets

Of that 1K, the system variables consumed 125 bytes, the display file needed at least 25 bytes (more if you actually wanted to show anything on screen), and the BASIC program itself took up space. A simple 10-line BASIC program could easily use half the available memory.

The result: most serious programs were about 10-20 lines of BASIC. Games were tiny. The classic "1K games" from the ZX81 era were marvels of compression - simple but playable. A maze game. A space invader. A number guessing game.

But I wanted to write a chess game.

Everyone said it was impossible.

---

## The Book That Changed Everything

My birthday was in March. I asked for one thing: **"Mastering Machine Code on Your ZX81" by Toni Baker** (published by Reston Publishing / Interface Publications, 1983).

```
  _________________________
 |  _____________________  |
 | |                     | |
 | |  MASTERING          | |
 | |  MACHINE CODE       | |
 | |  ON YOUR            | |
 | |  ZX81               | |
 | |                     | |
 | |  Toni Baker         | |
 | |_____________________| |
 |_________________________|

  (The book that launched
   a thousand programs)
```

This book was a revelation. Toni Baker had an extraordinary gift for explaining the Z80 processor in terms a teenager could understand. She didn't talk down to you, but she didn't assume you had a computer science degree either. She started with the basics - what a register is, what the program counter does, how binary arithmetic works - and built up to writing real machine code programs.

The key insight, the one that changed everything for me, was on page 47:

> *"A REM statement in BASIC is simply a section of memory that the BASIC interpreter ignores. But the Z80 processor doesn't know what a REM statement is. If you POKE machine code into a REM statement and then call it with USR, the processor will execute it as if it were any other program."*

A REM statement. The BASIC interpreter skips over anything after REM - it's a comment, meant for humans. But if you filled it with machine code bytes and then jumped to it with `RAND USR`, the Z80 would happily execute those bytes as instructions.

This was the key to fitting a real program in 1K. No BASIC interpreter overhead. No tokenised keywords eating up precious bytes. Just raw Z80 instructions, pretending to be a comment.

---

## Learning Z80: The Hard Way

There was no assembler for the ZX81. Not one I could afford, anyway, and certainly nothing that would run in 1K. So I did what Toni Baker's book taught me to do: I assembled the code **by hand**.

This meant:
1. Write the Z80 mnemonics on paper (LD A, 42 / CP 64 / JR NZ, $F6)
2. Look up each instruction in the opcode table at the back of the book
3. Write down the hex bytes (3E 2A / FE 40 / 20 F6)
4. Calculate the relative jump offsets by hand
5. Double-check everything
6. Type the bytes into the ZX81 using POKE commands
7. Pray

Step 7 was important because one wrong byte - one single wrong byte - and the ZX81 would crash. Not a polite error message. Not a helpful debugger. A crash. Screen goes mental, strange patterns appear, and you're back to the K cursor having lost everything you'd typed in because there was no auto-save.

```
  POKE 16514, 33        (LD HL, ...)
  POKE 16515, 130       (low byte)
  POKE 16516, 64        (high byte)
  POKE 16517, 6         (LD B, 64)
  POKE 16518, 64
  POKE 16519, 175       (XOR A)
  POKE 16520, 119       (LD (HL), A)
  POKE 16521, 35        (INC HL)
  POKE 16522, 16        (DJNZ ...)
  POKE 16523, 252       (-4 in two's complement)
  ...
  ...
  ... (672 bytes later) ...
  ...
  RAND USR 16514
```

If it worked, chess. If it didn't, crash. There was no middle ground.

---

## The Design Process

I filled an entire school exercise book with the chess program design. Diagrams of the board representation. Tables of piece movements. Flowcharts for the move generation algorithm. Columns of hex bytes with arrows showing the jumps and calls.

The biggest challenge was **fitting everything in 672 bytes**. That was the budget: 1024 bytes total, minus 125 for system variables, minus 25 for the display file, minus about 200 for the collapsed display during gameplay, minus the 6-byte overhead for the BASIC lines. It worked out to roughly 672 bytes for the machine code *including* the 64-byte chess board.

### Key Design Decisions

**Decision 1: The board lives inside the REM statement**

I realised that the 64 bytes at the start of the REM statement could be the chess board itself. The machine code entry point jumps past the board data to the actual code. This saved having a separate board area - the board WAS the code. Sort of.

**Decision 2: Trust the player**

Full move validation for chess is complex. Legal move generation for every piece type, check detection, pin detection, castling rules, en passant... each of these would cost 30-80 bytes. I couldn't afford any of it.

So I made a decision that horrified my chess-playing friends: **the player is responsible for making legal moves**. The program checks that you're moving your own piece and not landing on your own piece. That's it. You can move your King across the board in one step if you want to. You're cheating yourself.

**Decision 3: King capture = checkmate**

Real chess ends when a King is in checkmate. Detecting checkmate requires checking if the King is in check, if any move can block the check, if the King can escape... easily 100 bytes.

Instead, the game simply ends when a King is captured. Yes, this means you can technically move into check, and the computer might not notice. But in practice, the computer WILL take your King if you leave it hanging, because its evaluation function values the King at 50 points.

**Decision 4: One-ply search**

The computer looks one move ahead. That's it. It evaluates every possible move and picks the one that captures the most valuable piece (or makes a non-capture move if nothing's hanging).

This means it has no concept of tactics, combinations, or strategy. It won't set up forks, pins, or skewers. But it will always take a free piece, and it will prefer taking your Queen over taking a Pawn.

Surprisingly, this is enough to give a beginner a reasonable game. Novice players leave pieces hanging all the time, and a computer that always punishes that is tougher than you'd think.

---

## Three Evenings

It took three evenings to type in the machine code. Three evenings of:

```
POKE 16523, 252
```

*Is that right? Check the notebook. Yes, 252. DJNZ backwards 4 bytes. Two's complement of -4 is... 256 - 4 = 252. Yes.*

```
POKE 16524, 33
```

*LD HL, nn. Next two bytes are the address, low byte first...*

My mum kept calling me for dinner. "Just five more bytes, Mum!"

On the first evening, I entered about 200 bytes and tested it. The board displayed! It was wonky - the pieces were in the wrong places - but the display routine worked. I saved to tape (recording machine code to a portable cassette recorder, with all the attendant SCREEEEE sounds) and went to bed buzzing.

On the second evening, I got the player input working. You could type E2 E4 and the piece would move. The thrill of seeing that first pawn advance was indescribable. It was like the first time I'd made the TV show "HELLO", but multiplied by a thousand.

On the third evening, I entered the computer's thinking routine. This was the big one - about 250 bytes of move generation, evaluation, and selection code. I'd checked and rechecked the hex bytes against my notebook. I typed in the last POKE, saved to tape twice (paranoia), and typed:

```
RAND USR 16514
```

The board appeared. I played E2 E4. The computer "thought" for about two seconds (at 3.25 MHz, scanning 64 squares and generating moves took a noticeable moment), and then it played D7 D5.

The Scandinavian Defence.

I stared at the screen. The computer had made a real chess move. A named opening. It wasn't a coincidence - the computer chose D5 because it could immediately recapture with the Queen if I took the pawn. It was *thinking*.

I played D2 D4. The computer played E7 E5. It was improvising, but it was making moves that made sense. When I left a piece hanging, it took it. When I tried to trade pieces, it chose the trade that benefited it.

It wasn't Deep Blue. It wasn't even particularly good chess. But it was MY chess program, running in 1K of RAM, playing chess against me on a computer that cost less than a bicycle.

I was 14 years old, and I had taught a pile of silicon to play chess.

---

## What Happened Next

I showed it to everyone who would look. My mates at school were suitably impressed (most of them were still writing 10 PRINT "BUM" / 20 GOTO 10). My CS teacher, Mr. Henderson, spent his lunch break playing it and declared it "remarkable" - the highest praise he ever gave anything.

I sent a description to *Sinclair User* magazine but never heard back. I suspect they had already seen David Horne's 1K ZX Chess by then (published in 1983, and a much more polished program than mine - David was a professional programmer, I was a kid with a book).

Eventually, I got a 16K RAM pack and moved on to bigger programs. The chess game lived on a C15 cassette tape, which lived in a shoebox, which lived under my bed, which moved with me through two house moves and a decade of growth.

I found the cassette again years later, but by then the ZX81 was in a museum and the tape was too degraded to load. The code existed only in my exercise book, which I'd used to level a wobbly table in my first flat and subsequently lost.

This repository is my attempt to reconstruct it. The code here is based on what I remember and what I've learned since. The spirit is the same: every byte counts, every trick is fair game, and the goal is to make the impossible merely very difficult.

---

## To Every Kid With a ZX81

If you're 14 years old and you've just got a computer and you're wondering if you can make it do something amazing: yes. You can. It doesn't matter if your computer has 1K or 1TB. The magic isn't in the hardware.

The magic is that feeling when the cursor blinks and you type RUN and something you built from nothing comes alive on the screen.

That feeling hasn't changed in forty years. I hope it never does.

---

```
  +-+-+-+-+-+-+-+-+
 8|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 7|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 6|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 5|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 4|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 3|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 2|.|.|.|.|.|.|.|.|
  +-+-+-+-+-+-+-+-+
 1|.|.|.|.|K|.|.|.|
  +-+-+-+-+-+-+-+-+
   A B C D E F G H

  (Sometimes the best games
   end with a lone King.)
```
