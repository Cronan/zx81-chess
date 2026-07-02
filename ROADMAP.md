# Improvement Roadmap

A prioritised schedule of improvements, based on a full survey of the assembly,
the browser frontend, the two emulators, the test suites, and CI (July 2026).
Bugs first, then tests that lock the fixes in, then new features paid for out of
freed bytes, then UI and performance polish.

Current state: `chess.bin` is **983 of 984 bytes** (1 byte of headroom), all
tests pass (40 Python unit tests, 7 JS emulator tests, 5 differential games /
37 positions), and there are no open GitHub issues. Any new engine feature must
be paid for by freeing bytes first.

---

## Milestone 1 — Bugs and correctness (do first)

### 1.1 AI memory corruption when it has no legal move — **the one real engine bug**

`think` initialises `best_from` to `$FF` as a "no move found" sentinel
(`src/chess.asm:694-697`), but `ai_make_move` (`src/chess.asm:559`) loads it
unconditionally and calls `do_move`. If Black ever has zero pseudo-legal moves
(rare but reachable: a boxed-in lone king), `do_move` indexes `board + $FF` =
`$4181` — **inside the machine-code region** — reads a garbage "piece", zeroes
that code byte, and writes it onto the board. Memory corruption instead of a
stalemate.

**Fix (~4–8 bytes):** after `think`, test `best_from` for `$FF` and skip the
move — ideally branching to the existing `show_result` path so "AI has no move"
becomes a proper game-over. Pay for it with the free byte plus fix 1.2.

### 1.2 Dead branch in pawn capture generation (frees 2 bytes)

`jr z, gp_cap2` at `src/chess.asm:787` jumps to the *very next instruction*, so
it does nothing on any flag state. Delete it: 2 bytes freed, which together
with the 1 spare byte nearly covers the guard in 1.1.

### 1.3 Touch users cannot correct input in the ZX81 skin

`play/index.html` special-cases `key === 'DEL'` in `handleKey` and
`updateKeyboard`, but **no on-screen key emits `DEL`** (40 `data-key` elements,
none is delete) — the branch is dead code. On a phone, one mistap on a valid
file/rank is committed forever and the 4th character auto-sends the move. Wire
the shifted-0 membrane key (the real ZX81 DELETE) or add an explicit ⌫ key.
Physical Backspace already works, so this is wiring, not new logic.

### 1.4 Embedded binary in the web page can silently drift

`play/index.html` inlines the entire `.P` file as a base64 `CHESS_P` constant
(line ~899). Nothing checks it matches the built `chess.p` — the differential
tests run the *file*, not the string, so the deployed game could ship a stale
binary while CI stays green. **Fix:** a Makefile target that regenerates the
constant from `chess.p`, plus a CI step that fails on mismatch.

### 1.5 Stale docs and comments that actively mislead

- `src/chess.asm:745`: "Note: no en passant! That would eat about 40 bytes we
  don't have." — en passant **is implemented** now; the comment predates it.
- `src/chess.asm:676-678`: the `think` header advertises a "-2 penalty for
  moving to a square attacked by an enemy pawn" that **is not implemented
  anywhere**. Either delete the claim or implement it (see 3.3).
- `DEBUG_PROMPT.md`: a debugging brief for a long-fixed web bug, with stale
  addresses (`wait_key` at `$423D` vs the real `$421E`) and `SP = $43FF`
  (inside the code region — contradicts every other doc). Delete or move to
  `docs/` clearly marked historical.
- `docs/ANNOTATED.md` Part 6 shows `think` inlining board indexing; the code
  now uses `call board_addr` (`src/chess.asm:704`).
- `docs/MEMORY-MAP.md` buckets machine-code bytes inconsistently (860 vs 874)
  between its own tables.

*Effort: one short PR for 1.1+1.2 (with tests, see 2.1), one for 1.3, one for
1.4, one docs sweep for 1.5.*

---

## Milestone 2 — Test improvements (lock in Milestone 1, de-risk Milestone 3)

### 2.1 Regression tests for the fixes

- Python unit test: position where Black has no pseudo-legal move → assert no
  write outside the board and a clean game-over (covers 1.1).
- JS/browser test for the DEL key path (covers 1.3).
- The CI drift check from 1.4.

### 2.2 Make the Python harness robust to asm changes

`tests/test_chess.py` locates routines by hard-coded offsets
(`start_addr = 0x4082 + 109`) and byte-pattern scans ("the Nth `CALL` from
start", `3E 08 32 .. CD` for `think`). Any reordering in `chess.asm` breaks the
locators before logic is even tested. **Fix:** emit a symbol table from pasmo
at build time and have the tests load addresses from it. This is the single
biggest enabler for Milestone 3's refactors.

### 2.3 Close the emulator-parity gaps before they bite

Every new opcode the asm uses must be hand-added to *two* emulators. Known
asymmetries today:

- Python lacks `ADC A,*`, `SBC A,*`, `LDIR`, `RLA`, all of CB
  `SLA/RL/RR/RLC/RRC/SRA`, and several same-register `LD r,r` NOPs that the JS
  core handles generically — Python would error while JS passes.
- JS never computes the P/V (overflow/parity) flag and diverges from Python on
  `ADD HL,rr` H-flag and rotate N/H clearing. Harmless *today* only because no
  conditional in the program tests those flags.

**Fix:** a static scan test that disassembles `chess.bin` and asserts every
opcode present is implemented in both emulators, plus targeted flag-correctness
unit tests for the JS core. Cheap insurance against the recurring
"instruction accuracy" bug class called out in CLAUDE.md.

### 2.4 Deepen the differential suite

`tests/games.json` is 5 games, ≤10 plies each (~32 player moves). Add: one
full-length game (30+ plies), a game combining en passant + promotion +
game-over, and games that exercise the honour-system edge cases (illegal input
retry, null-move attempts). Positions are cheap — the comparator already checks
board, AI choice, ep square, and status every move.

### 2.5 End-to-end browser test

The Node tests drive the Z80 core, but `index.html`'s inline script — input
handling, both skins, the modern board, game-over overlay — has **zero
automated coverage**. Chromium + Playwright are available in CI-capable form;
add a smoke test: load the page, play a move in each skin, toggle skins, verify
DEL, finish a game. Also let CI trigger on all branches/PRs, not just
main/master.

*Effort: 2.1 lands with Milestone 1. 2.2 and 2.3 are each a focused PR and
should land **before** Milestone 3. 2.4/2.5 can proceed in parallel anytime.*

---

## Milestone 3 — Engine features within the memory boundary

The 984-byte ceiling stays. The plan is: **free ~45–55 bytes, then spend them.**

### 3.1 Free bytes

| Refactor | Est. bytes freed |
|---|---|
| Merge `gen_knight`/`gen_king` (`src/chess.asm:829-899`) — byte-for-byte identical except the direction table and one `cp` immediate; parameterise on HL + delta limit | ~38–42 |
| Dead `jr z, gp_cap2` (done in 1.2) | 2 |
| Shared table-lookup helper for the `ld e,a / ld d,0 / ld hl,tbl / add hl,de / ld a,(hl)` idiom (appears in `board_addr`, `get_piece_char`, `score_move`) | ~6–10 |
| Share the "WIN" tail between `msg_win`/`msg_lose` | ~0–4 (marginal) |

Each refactor must land as its own PR with the differential suite green —
history shows these dedups are where emulator divergence surfaces.

### 3.2 Spend bytes (in priority order)

| Feature | Est. cost | Why |
|---|---|---|
| No-move guard / stalemate game-over (1.1) | 4–8 | Fixes corruption |
| Promotion-aware pawn scoring — `gen_pawn` scores a promoting push as 1; score it as queen value (9) so the AI actually queens | 6–10 | Biggest playing-strength win per byte |
| Rebalance centre bonus vs captures — today a quiet central move (score 2) **outbids winning a pawn** (score 1), so the AI declines free pawns | few bytes | Playing strength |
| Reject null moves (source == dest) in `get_move` | ~4 | Correctness nicety |
| Implement the advertised "-2 if target square attacked by enemy pawn" penalty, making the `think` comment true | 15–25 | Playing strength, if budget remains |

Also worth hardening while in `check_pawn_cap`: en-passant capture is priced
*by accident* (the empty ep square happens to score 1 = a pawn); make the
pawn value explicit so a future scoring change can't silently mis-price ep.

### 3.3 Explicitly out of budget (stays on Known Limitations)

Under-promotion (~15–20 bytes for near-zero value), check indication (~40+,
needs attack generation), castling (~40+ and no free working-variable bytes at
`$40C2-$40C8`). Multi-ply search remains out of scope.

*Effort: 3.1's knight/king merge is the risky one — do it first, alone, after
2.2/2.3. Then spend in the table order; stop when the budget runs out.*

---

## Milestone 4 — Frontend UI improvements

All JS-side, zero engine bytes.

1. **Move history panel** — record moves as they're made (the UI already reads
   the chosen move from `$40C5/$40C6`); show algebraic list, both skins.
2. **Undo/takeback** — snapshot the 64-byte board + working variables
   (`$4082-$40C8`) before each player move; restore on demand. Doubles as
   save/load: persist snapshots to `localStorage` alongside the palette.
3. **Board flip** for the modern skin.
4. **Optional legality hints** — JS-side move validation in the modern skin
   (highlight legal destinations, warn on illegal moves) as a toggle, keeping
   the engine's authentic honour system as the default.
5. **Accessibility pass** — modern-board squares and membrane keys are bare
   `<div>`s: add `role`/`tabindex`/ARIA and keyboard operability; drop
   `user-scalable=no` from the viewport meta; give the canvas screen a text
   alternative. The skin toggle is already done right — match it.
6. Minor: make the "Computer thinking…" status event-driven rather than the
   current frame-count heuristic; remove the dead `debugLog`/`#debug` and
   `lastKeyRead` code in `play/zx81.js`.

*Effort: 1–3 are one PR each; 4 and 5 are the larger pieces. The Playwright
harness from 2.5 should exist first so each lands with a test.*

---

## Milestone 5 — Performance and internals

Measured reality first: the Python test suite runs in ~0.1 s and the whole
`make test` in seconds — **test performance is a non-issue**. Browser-side:

1. **Implement the JS runaway guard** — `cycles`/`maxCycles` in `play/z80.js`
   are declared but never used; the only protection is the 100 000-step inner
   cap. A malformed program (or a bad refactor in Milestone 3) can spin the
   main thread.
2. **Opcode dispatch table** in `play/z80.js` — replace the long `if`-chain
   with a 256-entry table. Faster, and each handler becomes independently
   testable (feeds 2.3).
3. **Web Worker for emulation** — nice-to-have; the 1-ply AI thinks fast, so
   only do this if 3.2's extra scoring terms make think time noticeable.

---

## Suggested sequence

| Order | Work | Depends on |
|---|---|---|
| 1 | 1.1 + 1.2 + 2.1 (corruption fix, freed bytes, regression test) | — |
| 2 | 1.3 (DEL key), 1.4 (CHESS_P drift check), 1.5 (docs sweep) | — (parallel) |
| 3 | 2.2 (symbol-table test addressing), 2.3 (emulator parity) | — |
| 4 | 2.4 + 2.5 (deeper diff games, Playwright smoke test) | — (parallel) |
| 5 | 3.1 knight/king merge, then 3.2 features in order | 2.2, 2.3 |
| 6 | Milestone 4 UI items | 2.5 |
| 7 | Milestone 5 internals | any time |
