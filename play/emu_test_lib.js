/**
 * Shared Node.js helpers for driving the JS Z80/ZX81 emulator outside
 * the browser. Used by test_js_emulator.js and tools/diff_runner.js.
 *
 * Loads z80.js and zx81.js (which attach to window.*) inside a minimal
 * browser-like vm context, and exposes the same setup/run/inspect
 * helpers the tests have always used.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// Create a minimal browser-like context
const context = {
    window: {},
    document: { getElementById: () => ({ textContent: '', getContext: () => ({
        fillStyle: '', fillRect: () => {},
    }) }) },
    navigator: {},
    console: console,
};
vm.createContext(context);

vm.runInContext(fs.readFileSync(path.join(__dirname, 'z80.js'), 'utf8'), context);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'zx81.js'), 'utf8'), context);

const Z80 = context.window.Z80;
const ZX81 = context.window.ZX81;

// ZX81 character codes for the keys the game reads
const ZX_KEYS = {
    a: 0x26, b: 0x27, c: 0x28, d: 0x29, e: 0x2A, f: 0x2B, g: 0x2C, h: 0x2D,
    1: 0x1D, 2: 0x1E, 3: 0x1F, 4: 0x20, 5: 0x21, 6: 0x22, 7: 0x23, 8: 0x24,
};

const BOARD_BASE = 0x4082;
const ENTRY_POINT = 0x40EF;
const BEST_FROM = 0x40C5;
const BEST_TO = 0x40C6;
const FRAMES = 0x4034;

function setupEmulator(pFilePath) {
    const cpu = new Z80();

    const mockCanvas = {
        width: 768, height: 576,
        getContext: () => ({
            fillStyle: '',
            fillRect: () => {},
        }),
    };

    const zx81 = new ZX81(cpu, mockCanvas);
    zx81.initSystemVars();

    const pData = fs.readFileSync(pFilePath || path.join(__dirname, '..', 'chess.p'));
    zx81.loadPFile(pData);

    return { cpu, zx81 };
}

function getPiece(cpu, file, rank) {
    const idx = (rank - 1) * 8 + (file.charCodeAt(0) - 'a'.charCodeAt(0));
    return cpu.rb(BOARD_BASE + idx);
}

function boardToString(cpu) {
    const pieceChars = { 0: '.', 1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K' };
    let result = '';
    for (let rank = 7; rank >= 0; rank--) {
        result += (rank + 1) + '|';
        for (let file = 0; file < 8; file++) {
            const piece = cpu.rb(BOARD_BASE + rank * 8 + file);
            const ptype = piece & 0x07;
            const isBlack = (piece & 0x08) !== 0;
            let ch = pieceChars[ptype] || '?';
            if (isBlack) ch = ch.toLowerCase();
            result += ch;
        }
        result += '\n';
    }
    result += '  abcdefgh';
    return result;
}

/**
 * Run frames exactly like the browser does.
 * Returns when HALT is hit with no keys, or after maxFrames.
 */
function runUntilIdle(cpu, zx81, maxFrames = 5000) {
    let frames = 0;
    let consecutiveIdleHalts = 0;

    while (frames < maxFrames) {
        let hitHalt = false;

        for (let i = 0; i < 100000; i++) {
            if (cpu.pc === 0) return { status: 'returned_to_zero', frames };

            const result = cpu.step();

            if (result === 'halt') {
                const key = zx81.getKey();
                if (key !== 0xFF) {
                    cpu.ww(0x4025, key);
                    consecutiveIdleHalts = 0;
                } else {
                    cpu.ww(0x4025, 0xFFFF);
                }
                cpu.halted = false;
                hitHalt = true;
                break;
            }

            if (result === 'error') {
                return { status: 'error', frames, pc: cpu.pc };
            }
        }

        frames++;

        if (hitHalt && zx81.keyBuffer.length === 0) {
            consecutiveIdleHalts++;
            // If we've had 3 consecutive idle HALTs, the game is waiting for input
            if (consecutiveIdleHalts >= 3) {
                return { status: 'idle', frames };
            }
        } else {
            consecutiveIdleHalts = 0;
        }
    }

    return { status: 'timeout', frames };
}

function queueKeys(zx81, keys) {
    for (const key of keys) {
        zx81.keyBuffer.push(key);
    }
}

/** Convert a move string like "e2e4" to ZX81 key codes. */
function moveToKeys(move) {
    return move.toLowerCase().split('').map((ch) => {
        const key = ZX_KEYS[ch];
        if (key === undefined) throw new Error(`No ZX81 key for '${ch}' in move '${move}'`);
        return key;
    });
}

module.exports = {
    Z80, ZX81,
    ZX_KEYS, BOARD_BASE, ENTRY_POINT, BEST_FROM, BEST_TO, FRAMES,
    setupEmulator, getPiece, boardToString, runUntilIdle, queueKeys, moveToKeys,
};
