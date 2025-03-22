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

Chess was important to me. My dad had taught me to play when I was small — I don't remember exactly when, maybe seven or eight — and by the time I was eleven I could beat him every time. He didn't let me win, either. I just got better. There's something about chess that suited my brain: the patterns, the logic, the way you have to think several steps ahead. It's a lot like programming, actually, though I didn't make that connection until years later.

So when I thought about what I wanted to make the ZX81 do, chess was the obvious answer. Not because it was easy — even I knew it wasn't easy — but because it mattered to me. The idea of teaching a computer to play chess, *my* computer, the one sitting on the carpet next to the telly — that was irresistible.

My dad, when I told him what I wanted to do, thought about it for a while and then said I'd need to learn machine code. I didn't know what machine code was. He didn't really either, to be honest, but he knew it was faster and smaller than BASIC. That was the conversation that led to the Zaks book appearing at Christmas.

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

I don't remember exactly where I first learned that trick. Might have been one of the magazines my dad occasionally brought home. It wasn't from another programmer — I didn't know a single other person who programmed. Not one. No school computer club, no friends with ZX81s, no local user group. This was Durban in 1982, not Silicon Valley. There was no Internet. There was me, the Zaks book, and whatever I could glean from the occasional copy of *Your Computer* or *Sinclair User* that made it to South Africa.

Everything I learned, I learned alone. Looking back, that was probably both the hardest and the most important part. When there's nobody to ask, you have to figure things out for yourself. And when you figure something out for yourself, it stays figured out.

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

The chess game wasn't a weekend project. It took the better part of two years.

I started thinking about it seriously in mid-1982, maybe six months after getting the ZX81. By then I'd written loads of small programs — games, utilities, graphics demos — and I understood the machine well enough to know what was possible and what wasn't. But chess was different. Chess was the thing everyone said couldn't be done in 1K. That, obviously, made me want to do it more.

I filled a school exercise book with the design. Page after page of diagrams, tables, calculations. How to represent the board. How to encode each piece in a single byte (bits 0-2 for the type, bit 3 for the colour). Direction offsets for each piece type. Memory budgets scribbled in the margins, adding up the same numbers over and over, trying to make it all fit. I knew I needed about 64 bytes for the board and that left me roughly 600 bytes for everything else.

The constraints were brutal:

- No castling (40 bytes I couldn't spare)
- No en passant (another 30 bytes)
- No real check detection (80+ bytes)
- No opening book (forget it)
- Minimal input validation (the player can cheat — that's on them)

The computer's "AI" was the hardest part. I spent months — on and off, between school and homework and being a teenager — working out how to generate moves for all the piece types efficiently. The breakthrough was using a bitmask to share one sliding loop between the Bishop, Rook, and Queen. That saved about 30 bytes, which doesn't sound like much until you realise the entire program is 672 bytes. I remember the moment I figured that trick out. I was on the bus home from school and I nearly shouted.

### Writing It, Breaking It, Fixing It

The actual coding happened in fits and starts over months. I'd write a section on paper — hand-assemble it from the Zaks opcode tables — then type in the bytes and test it. More often than not, it would crash. One wrong byte and the ZX81 just died on you. No error message, no debugger. Just garbage on the telly and that sinking feeling.

The board display came first. Weeks of getting the piece characters right, figuring out how to write directly to the display file, getting the ranks the right way up (I had them upside down for an embarrassingly long time). But when I finally saw a proper chess board on our family telly — white pieces in normal video, black pieces in inverse — I nearly fell off my chair.

Player input came next. Type E2, type E4, and the pawn moves. That moment — seeing a chess piece actually move on screen because of code I'd written, bytes I'd assembled by hand on paper — I can still feel that. It was like electricity.

The thinking routine was the mountain. About 250 bytes of move generation and evaluation, and every bug was agony to track down. I'd check and recheck the hex against my notebook, staring at columns of numbers until my eyes went funny. By the time I got it working properly, it was well into 1983. I was fourteen.

I typed in the last POKE. Saved to tape. Saved to tape again, on a different cassette, because I wasn't stupid. Then:

```
RAND USR 16514
```

The board appeared. I played E2 E4. The computer thought for maybe two seconds, and played D7 D5.

I didn't know the name for it then, but that's the Scandinavian Defence. The computer chose it because it could recapture with the queen if I took the pawn. It was *thinking*. Not well, not deeply, but it was looking at the board and making decisions based on what it saw.

I played it for hours that night. Then I played my dad. He didn't really understand what he was looking at — inverse video characters on a wobbly black-and-white telly — but he played along. When the computer took his bishop, he looked at me and said, "It's actually quite good, isn't it?" Coming from my dad, the man who'd taught me chess, that meant everything.

The computer wasn't good. It only looks one move ahead, so it can't see traps or plan combinations. But it always took your pieces if you left them hanging, and it put up a real fight against a casual player. Against me it didn't stand a chance — I could see too far ahead for it. But against someone who wasn't paying attention, it'd punish every mistake. That felt right. That felt like the chess my dad had taught me: pay attention, or you'll lose your queen.

---

## What Happened After

Eventually I got a 16K RAM pack — the big grey block that wobbled in its connector and crashed the machine if you breathed on it. With 16K the world opened up. I could write proper programs, with variables and loops and strings and everything. I moved on, the way you do.

The chess game stayed on a C15 cassette tape that I labelled "CHESS" in biro. The tape went into a shoebox, the shoebox went under my bed, and it followed me through a house move and eventually out of Durban altogether.

I found the cassette years later. But by then the tape was degraded beyond loading, and the exercise book with the hex dump was long gone. I think it ended up levelling a table in my first flat in Johannesburg. The code existed only in my memory, and memory — as any ZX81 programmer can tell you — is a lousy storage medium.

---

## About This Repository

I want to be honest about something. **This is not the code I wrote in 1982-83.** That code is gone. The tape is unreadable, the notebook is lost, and I can't reconstruct 672 bytes of hand-assembled Z80 from forty-year-old memories.

What this repository contains is a **complete rewrite**, done by me as an adult, in the spirit of that twelve-year-old kid sitting cross-legged on the carpet in Durban. I've tried to stay true to what I remember of the original design — the board encoding, the direction tables, the REM statement hack, the general shape of the AI. Some of the tricks in here are ones I genuinely used back then. Others are probably better than what teenage me managed, because I've had decades of programming experience since, and it would be dishonest to pretend otherwise.

But the constraints are real. 1K of RAM. The Z80A instruction set. Every byte earned. And the feeling — that same feeling of making something impossible fit into something tiny — that hasn't changed at all. I still get the same buzz from shaving a byte off a routine that I got in 1983, and I suspect I always will.

This is my love letter to the kid I was, the machine that started everything, and the 624-page book that taught me how computers actually think.

---

## The Book, Revisited

I still have my copy of Zaks somewhere. The spine is cracked and several pages are loose. There are pencil annotations in the margins — opcode mnemonics I was trying to memorise, tiny notes in my teenage handwriting. Page 47 has a coffee ring on it from my dad's mug.

The Zaks book wasn't written for kids. It was written for engineers and professional programmers. But it was *clear*, and that was what mattered. It didn't patronise, but it didn't assume you already knew everything either. It built up from first principles — bits, bytes, two's complement, registers, memory, instructions — and by the time you reached the advanced chapters on interrupt handling, you actually understood what you were reading.

If I'm honest, I probably understood about 60% of the book at age twelve. By fourteen, maybe 80%. The remaining 20% I figured out over the next few decades, usually by getting things wrong and then going back to Zaks to find out what I should have done.

624 pages. Not a wasted one.

---

## To Every Kid Sitting Cross-Legged on the Carpet

If you're twelve or fourteen and you've got a computer and you're wondering whether you can make it do something amazing: yes. You can. Even if there's nobody around to help you. Even if you're the only person you know who does this. *Especially* then.

I learned to program entirely on my own, in a city where I didn't know a single other programmer, with no Internet, no mentor, no community. Just a machine, a book, and the stubbornness to keep going when things crashed. And things crashed a lot.

It doesn't matter if your machine has 1K or 1TB. It doesn't matter if you're learning from a 624-page reference book or a YouTube video. The fundamentals are the same. Bits, logic, persistence. The willingness to sit with a problem until it gives in.

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
