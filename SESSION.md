# One Session with Claude Fable 5

This document records a single autonomous session with **Claude Fable 5**
(Anthropic's Mythos-class model, July 2026) against this repository: what it
found, what it fixed, and how that compares with the repository's earlier
AI-assisted history. Everything below is verifiable from `git log` on this
branch and from [ROADMAP.md](ROADMAP.md), which the session wrote first and
then executed end to end.

## The shape of the session

One prompt: *"suggest a schedule of improvements, prioritise bugs."* One
follow-up: *"run the schedule in order, creating commits and testing as you
go."* Everything else — the survey, the prioritisation, the sixteen
implementation commits, the tests that gate each one — happened in a single
session without further steering.

The session first surveyed the whole repository in parallel (the Z80 assembly
and its docs; the frontend, both emulators, the test suites, CI), wrote the
prioritised roadmap, and then worked through all five milestones in order,
running the full test suite before every commit and adding a regression test
with every fix.

## Bugs found that had survived every earlier pass

This repository had already been through many AI-assisted sessions — 92
commits, 28 PRs, including a dedicated repo-review session (PR #28). These
bugs survived all of them:

1. **Engine memory corruption** (`ai_make_move`). If the AI ever had no legal
   move — a boxed-in lone king — `think`'s `$FF` "no move" sentinel was used
   unchecked as a board index, and `do_move` wrote through `board + $FF` into
   the machine code at `$4181`, corrupting the program. Found by reading the
   assembly, confirmed with a failing test *before* the fix, fixed in 3 bytes
   paid for by deleting a dead branch that had also gone unnoticed
   (`jr z, gp_cap2` jumped to the next instruction).

2. **Touch users couldn't correct a typo.** The page's input code had a
   complete `DEL` handling path — highlight logic and all — but no on-screen
   key ever emitted `DEL`. The branch was dead code shipped for months; one
   mistap and the fourth character auto-sent the move.

3. **The deployed game could silently ship a stale binary.** The page embeds
   the whole tape image as base64, and nothing kept that copy in sync with the
   assembled `chess.p`. Not hypothetical: the session's *first* engine fix made
   the embedded copy stale, and the new CI check caught its own scenario the
   same hour it was written.

4. **A boot-time input race.** Frames without a HALT were treated as "the AI
   is thinking", and a HALT that consumed a key was treated as "engine idle" —
   both wrong by one frame. Fast typing could invent a history entry from
   stale state. The session found this itself, when its own new feature
   (move history) made the latent race observable, and fixed it by modelling
   engine readiness properly instead of trusting frame timing.

5. **The AI declined free material.** A quiet move to a centre file scored 2;
   capturing a free pawn scored 1. The engine had been politely refusing pawns
   since the centre bonus was added. Promotion was similarly invisible to the
   evaluation (a queening push scored 1, like any shuffle). Both fixed inside
   the byte budget, with the en passant capture repriced *explicitly* — it had
   only been priced correctly by a numeric coincidence the rescale would have
   silently broken.

## The contrast the git history draws

The most direct comparison is written into the log. In the repository's
earlier life, a browser bug — "keys are delivered but moves don't get
processed" — consumed **sixteen consecutive debugging commits** (PRs #8–#19:
`Debug:`, `Debug v2`, `v3` … `v7`), after which the session gave up and
committed `DEBUG_PROMPT.md`, literally titled *"Add debugging prompt for
handoff to another model"*. The eventual fix, in a later session, turned out
to require five separate root causes (register-mapping bugs, a rook direction
mask, a stack/code collision, a JR off-by-one, keyboard state after the AI
moved). The maintainer's account is that those sessions ran on earlier Claude
models, most recently Claude Opus 4.8.

This session's equivalents — the `$FF` corruption, the idle-HALT race, undoing
a *finished* game by re-entering the engine's game loop at the right address —
were each diagnosed from first principles (reading the Z80 source and the
emulator loop, not adding debug prints), reproduced with a failing test first,
and fixed in one commit each. `DEBUG_PROMPT.md` itself was deleted as part of
the docs sweep: its addresses were stale and its suggested stack pointer sat
inside the code region.

## The numbers

| | Session start | Session end |
|---|---|---|
| Binary size | 983 / 984 bytes (1 free) | **961 / 984 bytes (23 free)** — with *more* features |
| Engine features | en passant | + no-move guard, promotion-aware scoring, material-first evaluation, honest ep pricing |
| Python unit tests | 40 | 43 |
| JS emulator tests | 7 | 10 |
| Differential games | 5 games / 37 positions | 8 games / 58 positions, incl. a genuine AI en-passant capture and the suite's first black-wins ending |
| Browser (Playwright) tests | none | 10, driving the real page |
| Test addressing | hard-coded offsets + byte-pattern scans | pasmo symbol table (`chess.sym`) |
| Emulator parity | hand-maintained, silently divergent flags | opcode-coverage probe (78 instructions × 2 emulators) + aligned P/V, H, N flag semantics |
| CI | build + tests, main branch only | + artifact-drift check, browser smoke test, all branches |
| Web UI | play only | + move history, full-turn undo (works even after game over), board flip, optional legal-move hints, save/resume across reloads, keyboard accessibility |

The engine work is the part that shows the byte-budget discipline: merging the
knight and king generators (byte-for-byte twins except one table pointer and
one immediate) freed 36 bytes, which paid for every engine improvement above
with 23 bytes left over — the binary got *smaller* while the chess got better.

## What was deliberately not done

Honesty matters more than a clean sweep. Three roadmap items were consciously
skipped, with reasons recorded in [ROADMAP.md](ROADMAP.md): the "-2
pawn-attack penalty" (risks all-zero scores colliding with the `$FF` sentinel
for ~20 bytes of marginal strength), null-move rejection (turned out to be
already implicit in the own-piece check — verified, not assumed), and the JS
dispatch-table rewrite (its testability rationale was delivered by the opcode
probe at a fraction of the churn).

---

*Written at the end of the session it describes. The commit history on this
branch is the primary source; nothing here is claimed that a `git log -p`
can't confirm.*
