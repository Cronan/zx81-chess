```
 ___  ___  __   ___  ____  ___  ___  __  __
|   \/   | \ \ / / |/ ___||_ _|/ _ \|  \/  \ \ \/ /
| |\  /| |  \   /    \___ \ | || | | | |\/| |\ \  /
| | \/ | |   | |     ___) || || |_| | |  | | / /\ \
|_|    |_|   |_|    |____/|___|\___/|_|  |_|/_/  \_\
```

# My Story: A Kid in Durban, a ZX81, and 1024 Bytes

---

## Christmas 1981

I was twelve years old and living in Durban, South Africa. On Christmas morning my dad handed me two presents. One was small and surprisingly light. The other was heavy — properly heavy, the way only a thick book can be.

The small one was a **Sinclair ZX81**. He'd ordered it from somewhere overseas — I never did find out exactly where, or how long it took to get through. Importing anything electronic into South Africa in those days was a mission. You couldn't just pop down to the shops. There was no CompuTech on the corner. You waited, and you hoped customs didn't lose it.

The heavy one was **"Programming the Z80"** by Rodnay Zaks. 624 pages. My dad must have known — or guessed, or been told by someone at work — that if you wanted to do anything serious with the ZX81, you'd need to understand the processor inside it. He wasn't a computer person himself, but he was the kind of dad who'd figure out what his kid needed and then quietly go and find it.

The ZX81 was smaller than my school textbooks. Lighter than my pencil case. A flat membrane keyboard that felt like typing on a placemat. One kilobyte of RAM.

The most beautiful thing I'd ever seen.

```
  ____________________
 |                    |
 | K                  |
 |                    |
 |                    |
 |____________________|

    That inverse-K cursor,
    blinking on our family
    television in the lounge.
    Christmas morning, 1981.
    Durban.
```

We hooked it up to the telly with the RF lead. Channel 36 — or whatever the PAL equivalent was in South Africa. The picture was terrible. Black and white, slightly wobbly, and if someone walked past the aerial lead the screen would scramble. None of that mattered.

I typed:

```
10 PRINT "HELLO"
20 GOTO 10
RUN
```

The screen filled up. HELLO HELLO HELLO HELLO. My dad looked over my shoulder and said something like "that's clever" and went back to his Christmas lunch. But I sat there, cross-legged on the carpet in the Durban heat — Christmas in the southern hemisphere, thirty-something degrees outside — staring at the telly, and thought: *I can make this thing do anything.*

I was wrong about that, obviously. You can't make 1K do anything. But I didn't know that yet. And the Zaks book sat on the carpet next to me, waiting.

---

## The 1K Wall

The ZX81 came with 1 kilobyte of RAM. I didn't properly understand what that meant at first. I just knew that after typing in about fifteen lines of BASIC, the machine would print `4/MEMORY FULL` at me and refuse to do any more.

So my first few programs were tiny. Number guessing games. A thing that drew random patterns with PLOT. A program that printed my name in a loop, which I thought was hilarious for about ten minutes. The usual stuff.

But I wanted more. I wanted to make a game that was actually *good*. Not just random dots or guessing numbers. Something with a board, and pieces, and an opponent. Something like chess.

I mentioned this to my dad. He thought about it for a while and then said I'd need to learn machine code. I didn't know what machine code was. He didn't really either, to be honest, but he knew it was faster and smaller than BASIC.

---

## The Book

The Zaks book. I didn't open it properly until a few days after Christmas — I was too busy typing in BASIC programs. But when I did open it, I couldn't stop.

```
  _________________________
 |  _____________________  |
 | |                     | |
 | |  PROGRAMMING        | |
 | |  THE Z80            | |
 | |                     | |
 | |  Rodnay Zaks        | |
 | |                     | |
 | |  SYBEX              | |
 | |_____________________| |
 |_________________________|

  624 pages. The Bible.
```

It wasn't a ZX81-specific book — it was a proper Z80 reference, written for anyone programming the Z80 processor, whether that was in a Sinclair, a CP/M machine, or an industrial controller. It covered everything from basic binary arithmetic right through to interrupt handling and I/O operations. The third revised edition, published by Sybex. Probably the most important book I've ever owned.

Chapter 1 started with number representation. Binary, hexadecimal, BCD. And then two's complement.

I remember sitting at the kitchen table with a pencil and graph paper, working through the exercises. *What is the two's complement of +16? Of -17? Of -18?* The book walked you through it methodically. It wasn't dumbed down, but it was clear. Zaks had a way of building concepts one on top of the next, so by the time you got to something complicated, you'd already done all the groundwork.

The two's complement stuff stuck with me. Not just because it was clever — though it is clever, the way you can add and subtract signed numbers without worrying about the sign — but because it was the first time I realised that a computer doesn't think in the way people imagine. It doesn't know what "negative" means. It just flips bits and adds them up. The meaning is something we impose on the numbers. That idea opened a door in my head that never closed.

I also had access to an IBM reference manual — I can't remember exactly which one, something from my dad's work, probably a System/360 principles of operation manual or one of the training textbooks. It had a more formal treatment of two's complement arithmetic and binary representations. Between that and the Zaks book, I had a decent grounding in how numbers actually work at the hardware level, even if I was only twelve.

---

## Learning Z80 the Hard Way

The Zaks book wasn't specifically about the ZX81. That was both a problem and an advantage. It didn't tell me where to POKE things or how the display file worked. But it gave me a thorough understanding of the Z80 instruction set — every opcode, every addressing mode, every flag bit.

For the ZX81-specific bits, I picked up what I could from magazines and other kids' programs. The key trick — the one that made everything possible — was the REM statement hack.

The idea is dead simple: the BASIC interpreter skips over anything after REM. But the Z80 processor doesn't know what REM is. If you fill a REM statement with machine code bytes and then jump to them with `RAND USR`, the processor will happily execute them. Your entire program can hide inside a BASIC comment.

I don't remember exactly where I first learned that trick. It was common knowledge among ZX81 hackers by 1982. Might have been a magazine, might have been another kid at school. In Durban there was a small but dedicated group of us who had these machines, and we traded tips the way other kids traded football stickers.

There was no assembler. Not one I could afford, and certainly nothing that would run in 1K. So I assembled the code by hand. That meant:

1. Write the Z80 mnemonics on paper (LD A, 42 / CP 64 / JR NZ, -4)
2. Look up each instruction in the opcode table at the back of the Zaks book
3. Write down the hex bytes (3E 2A / FE 40 / 20 FC)
4. Calculate the jump offsets by hand (counting bytes forward or backward)
5. Double-check everything
6. Type the bytes into the ZX81 using POKE commands from the keyboard
7. Hold your breath and type RAND USR 16514

If it worked, you got your program. If you'd got one byte wrong — one single byte — the ZX81 would crash. Not a polite error message. A hard crash. The screen would go mental, garbage characters everywhere, and you'd be back to the K cursor having lost everything you hadn't saved to tape. And saving to tape meant fiddling with a portable cassette recorder, hoping the heads were clean and the volume was right.

```
  POKE 16514, 33
  POKE 16515, 130
  POKE 16516, 64
  POKE 16517, 6
  POKE 16518, 64
  POKE 16519, 175
  ...
  ... 672 bytes ...
  ...
  RAND USR 16514
```

That was the process. One byte at a time.

---

## The Chess Game

By 1983 I was fourteen and I'd been programming the ZX81 for two years. I'd written loads of small programs — games, utilities, graphics demos. But the chess game was the one I really wanted to do. The one everyone said couldn't be done.

I filled a school exercise book with the design. Diagrams of the board representation. Tables of piece movements. I'd worked out how to encode each piece in a single byte (bits 0-2 for the type, bit 3 for the colour). I'd figured out the direction offsets for each piece type. I knew I needed about 64 bytes for the board and that left me roughly 600 bytes for everything else.

The constraints were brutal:

- No castling (40 bytes I couldn't spare)
- No en passant (another 30 bytes)
- No real check detection (80+ bytes)
- No opening book (forget it)
- Minimal input validation (the player can cheat — that's on them)

The computer's "AI" was the hardest part. I spent ages working out how to generate moves for all the piece types efficiently. The breakthrough was using a bitmask to share one sliding loop between the Bishop, Rook, and Queen — that saved about 30 bytes, which doesn't sound like much until you realise the entire program is 672 bytes.

### Three Evenings

It took three evenings to type in the machine code. I'd come home from school, do my homework (or claim to), and sit in front of the ZX81 typing POKE commands.

On the first evening I got the board display working. The pieces showed up on screen — white pieces in normal video, black pieces in inverse. It was wonky at first (I had the ranks upside down), but when I fixed it and saw a proper chess board on our family telly, I nearly fell off my chair.

On the second evening I got the player input working. Type E2, type E4, and the pawn moves. That moment — seeing a chess piece actually move on screen because of code I'd written — I can still feel that. It was like electricity.

On the third evening, the computer's thinking routine. About 250 bytes of move generation and evaluation. I'd checked and rechecked the hex against my notebook. Typed in the last POKE. Saved to tape. Saved to tape again, on a different cassette, because I wasn't stupid. Then:

```
RAND USR 16514
```

The board appeared. I played E2 E4. The computer thought for maybe two seconds, and played D7 D5.

I didn't know the name for it then, but that's the Scandinavian Defence. The computer chose it because it could recapture with the queen if I took the pawn. It was *thinking*. Not well, not deeply, but it was looking at the board and making decisions based on what it saw.

I played it for hours that night. The computer wasn't good — it only looks one move ahead, so it can't see traps or plan combinations — but it always took my pieces if I left them hanging, and it put up a real fight. My mate Steven came round and played it and said "that's actually not bad" which, from Steven, was basically a standing ovation.

---

## What Happened After

Eventually I got a 16K RAM pack — the big grey block that wobbled in its connector and crashed the machine if you breathed on it. I moved on to bigger programs. The chess game stayed on a C15 cassette tape that I labelled "CHESS" in biro. The tape went into a shoebox, the shoebox went under my bed, and it followed me through a house move and eventually out of Durban altogether.

I found the cassette years later. But by then the tape was degraded beyond loading, and the exercise book with the hex dump was long gone. I think it ended up levelling a table in my first flat in Johannesburg. The code lived on only in my memory, and memory is a lousy storage medium.

This repository is my attempt to reconstruct it. The code here is based on what I remember and what I've learned since — some of the tricks are exactly as I did them, others are probably better than what fourteen-year-old me managed. But the spirit is the same: every byte counts, every trick is fair game, and the whole thing has to fit in 1K.

---

## The Book, Revisited

I still have my copy of Zaks somewhere. The spine is cracked and several pages are loose. There are pencil annotations in the margins — opcode mnemonics I was trying to memorise, tiny notes in my teenage handwriting. Page 47 has a coffee ring on it from my dad's mug.

The Zaks book wasn't written for kids. It was written for engineers and professional programmers. But it was *clear*, and that was what mattered. It didn't patronise, but it didn't assume you already knew everything either. It built up from first principles — bits, bytes, two's complement, registers, memory, instructions — and by the time you reached the advanced chapters on interrupt handling, you actually understood what you were reading.

If I'm honest, I probably understood about 60% of the book at age twelve. By fourteen, maybe 80%. The remaining 20% I figured out over the next few decades, usually by getting things wrong and then going back to Zaks to find out what I should have done.

624 pages. Not a wasted one.

---

## To Every Kid Sitting Cross-Legged on the Carpet

If you're twelve or fourteen and you've got a computer and you're wondering whether you can make it do something amazing: yes. You can.

It doesn't matter if your machine has 1K or 1TB. It doesn't matter if you're in Durban or Dublin or Dallas. It doesn't matter if you're learning from a 624-page reference book or a YouTube video. The fundamentals are the same. Bits, logic, persistence.

The magic is that moment when you type RUN and something you built from nothing comes alive on the screen. That hasn't changed in forty-odd years. I hope it never does.

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

  Sometimes the best games
  end with a lone King
  and a kid who wouldn't
  give up.
```
