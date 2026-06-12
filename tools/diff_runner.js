#!/usr/bin/env node
/**
 * JS half of the cross-emulator differential test.
 *
 * Replays the scripted games from tests/games.json through the JS
 * Z80/ZX81 emulator (the one the browser uses) and emits one JSON line
 * per position: after startup and after each player move + AI reply.
 *
 * tools/diff_test.py runs the same protocol through the Python harness
 * and compares the output line by line.
 *
 * FRAMES ($4034) is pinned to 0 after loading chess.p (which sets it to
 * $FFFF) so the AI's tie-break coin flip is deterministic and matches
 * the Python harness.
 */

const fs = require('fs');
const path = require('path');
const {
    BOARD_BASE, BEST_FROM, BEST_TO, FRAMES, ENTRY_POINT,
    setupEmulator, runUntilIdle, queueKeys, moveToKeys,
} = require('../play/emu_test_lib');

const GAMES_PATH = path.join(__dirname, '..', 'tests', 'games.json');

function boardHex(cpu) {
    let hex = '';
    for (let i = 0; i < 64; i++) {
        hex += cpu.rb(BOARD_BASE + i).toString(16).padStart(2, '0');
    }
    return hex;
}

function kingsPresent(cpu) {
    let kings = 0;
    for (let i = 0; i < 64; i++) {
        if ((cpu.rb(BOARD_BASE + i) & 0x07) === 6) kings++;
    }
    return kings;
}

function normalizeStatus(cpu, runStatus) {
    // On game over the code spins in JR $ and never idles, so detect it
    // from the board rather than the run status.
    if (kingsPresent(cpu) < 2) return 'gameover';
    return runStatus === 'idle' ? 'idle' : runStatus;
}

function emit(game, move, cpu, status) {
    console.log(JSON.stringify({
        game,
        move,
        board: boardHex(cpu),
        bestFrom: cpu.rb(BEST_FROM),
        bestTo: cpu.rb(BEST_TO),
        status,
    }));
}

const games = JSON.parse(fs.readFileSync(GAMES_PATH, 'utf8')).games;

for (const [name, moves] of Object.entries(games)) {
    const { cpu, zx81 } = setupEmulator();
    cpu.sp = 0x7FFF;
    cpu.pc = ENTRY_POINT;
    cpu.ww(0x4025, 0xFFFF);
    cpu.ww(FRAMES, 0); // pin AFTER loadPFile, which sets $FFFF

    let status = normalizeStatus(cpu, runUntilIdle(cpu, zx81).status);
    emit(name, 'start', cpu, status);

    for (const move of moves) {
        if (status === 'gameover') break;
        queueKeys(zx81, moveToKeys(move));
        // 300 frames is generous (normal moves idle within ~40) while
        // keeping the post-gameover JR $ spin from taking forever.
        status = normalizeStatus(cpu, runUntilIdle(cpu, zx81, 300).status);
        emit(name, move, cpu, status);
    }
}
