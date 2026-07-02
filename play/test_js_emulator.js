#!/usr/bin/env node
/**
 * Node.js test for the JS Z80 emulator - tests multi-turn game play
 * Simulates the browser's runFrame() loop to catch bugs that only
 * appear in the JS runtime (not the Python test harness).
 */

const {
    Z80, ZX_KEYS, BOARD_BASE, ENTRY_POINT,
    setupEmulator, getPiece, boardToString, runUntilIdle, queueKeys,
} = require('./emu_test_lib');

// ZX81 key codes
const ZX_A = ZX_KEYS.a, ZX_D = ZX_KEYS.d, ZX_E = ZX_KEYS.e, ZX_F = ZX_KEYS.f, ZX_G = ZX_KEYS.g;
const ZX_1 = ZX_KEYS[1], ZX_2 = ZX_KEYS[2], ZX_3 = ZX_KEYS[3], ZX_4 = ZX_KEYS[4];

// ============ TESTS ============

let passed = 0, failed = 0;

function assert(condition, msg) {
    if (!condition) {
        console.log(`  FAIL: ${msg}`);
        failed++;
        return false;
    }
    return true;
}

// --- Test 1: Board initialization and first idle ---
console.log('\n=== Test 1: Game startup ===');
{
    const { cpu, zx81 } = setupEmulator();
    cpu.sp = 0x7FFF;
    cpu.pc = ENTRY_POINT;
    cpu.ww(0x4025, 0xFFFF);

    const result = runUntilIdle(cpu, zx81);

    if (assert(result.status === 'idle', `Expected idle, got ${result.status} after ${result.frames} frames`)) {
        // Check board is initialized
        const wp = getPiece(cpu, 'e', 2); // White pawn
        const bk = getPiece(cpu, 'e', 8); // Black king
        assert(wp === 0x01, `e2 should be white pawn (0x01), got 0x${wp.toString(16)}`);
        assert(bk === 0x0E, `e8 should be black king (0x0E), got 0x${bk.toString(16)}`);
        console.log('  Board initialized, game waiting for input');
        console.log(`  Reached idle after ${result.frames} frames`);
        passed++;
    }
}

// --- Test 2: First move (E2E4) + computer response ---
console.log('\n=== Test 2: First player move (E2E4) + computer response ===');
{
    const { cpu, zx81 } = setupEmulator();
    cpu.sp = 0x7FFF;
    cpu.pc = ENTRY_POINT;
    cpu.ww(0x4025, 0xFFFF);

    // Run to idle (waiting for first move)
    runUntilIdle(cpu, zx81);

    // Send E2E4
    queueKeys(zx81, [ZX_E, ZX_2, ZX_E, ZX_4]);

    const result = runUntilIdle(cpu, zx81);

    if (assert(result.status === 'idle', `Expected idle after move 1, got ${result.status}`)) {
        // Check e2 is empty (pawn moved)
        const e2 = getPiece(cpu, 'e', 2);
        const e4 = getPiece(cpu, 'e', 4);
        assert(e2 === 0x00, `e2 should be empty after E2E4, got 0x${e2.toString(16)}`);
        assert(e4 === 0x01, `e4 should have white pawn, got 0x${e4.toString(16)}`);

        // Check computer made a move (at least one black piece should have moved)
        // Count black pieces not on starting positions
        let blackMoved = false;
        for (let sq = 0; sq < 64; sq++) {
            const piece = cpu.rb(BOARD_BASE + sq);
            if ((piece & 0x08) && sq < 48) { // Black piece below rank 7
                blackMoved = true;
                break;
            }
        }
        if (assert(blackMoved, 'Computer should have made a move (black piece moved)')) {
            console.log(`  Move 1 complete. Computer responded. Idle after ${result.frames} frames.`);
            console.log(boardToString(cpu));
            passed++;
        }
    }
}

// --- Test 3: TWO moves - the critical test ---
console.log('\n=== Test 3: Two consecutive player moves (E2E4, D2D4) ===');
{
    const { cpu, zx81 } = setupEmulator();
    cpu.sp = 0x7FFF;
    cpu.pc = ENTRY_POINT;
    cpu.ww(0x4025, 0xFFFF);

    // Run to idle
    runUntilIdle(cpu, zx81);
    console.log('  Game ready for first move');

    // First move: E2E4
    queueKeys(zx81, [ZX_E, ZX_2, ZX_E, ZX_4]);
    const result1 = runUntilIdle(cpu, zx81);

    if (!assert(result1.status === 'idle', `After move 1: expected idle, got ${result1.status}`)) {
        console.log(`  PC: 0x${cpu.pc.toString(16)}, frames: ${result1.frames}`);
    } else {
        const e2 = getPiece(cpu, 'e', 2);
        const e4 = getPiece(cpu, 'e', 4);
        assert(e2 === 0x00, `e2 empty after move 1: got 0x${e2.toString(16)}`);
        assert(e4 === 0x01, `e4 has white pawn after move 1: got 0x${e4.toString(16)}`);
        console.log(`  Move 1 (E2E4) complete after ${result1.frames} frames`);
        console.log(boardToString(cpu));
    }

    // Second move: D2D4
    queueKeys(zx81, [ZX_D, ZX_2, ZX_D, ZX_4]);
    const result2 = runUntilIdle(cpu, zx81);

    if (!assert(result2.status === 'idle', `After move 2: expected idle, got ${result2.status}`)) {
        console.log(`  CRITICAL: Second move failed! Status: ${result2.status}, PC: 0x${cpu.pc.toString(16)}, frames: ${result2.frames}`);
        console.log(`  Keys remaining: ${zx81.keyBuffer.length}`);
        console.log(boardToString(cpu));
    } else {
        const d2 = getPiece(cpu, 'd', 2);
        const d4 = getPiece(cpu, 'd', 4);
        if (assert(d2 === 0x00, `d2 empty after move 2: got 0x${d2.toString(16)}`)) {
            console.log(`  Move 2 (D2D4) complete after ${result2.frames} frames`);
            console.log(boardToString(cpu));
            passed++;
        }
    }
}

// --- Test 4: Three moves ---
console.log('\n=== Test 4: Three consecutive moves ===');
{
    const { cpu, zx81 } = setupEmulator();
    cpu.sp = 0x7FFF;
    cpu.pc = ENTRY_POINT;
    cpu.ww(0x4025, 0xFFFF);

    runUntilIdle(cpu, zx81);

    const moves = [
        { keys: [ZX_E, ZX_2, ZX_E, ZX_4], desc: 'E2E4', checkEmpty: ['e', 2] },
        { keys: [ZX_D, ZX_2, ZX_D, ZX_4], desc: 'D2D4', checkEmpty: ['d', 2] },
        { keys: [ZX_G, ZX_1, ZX_F, ZX_3], desc: 'G1F3', checkEmpty: ['g', 1] },
    ];

    let allOk = true;
    for (let i = 0; i < moves.length; i++) {
        const m = moves[i];
        queueKeys(zx81, m.keys);
        const result = runUntilIdle(cpu, zx81);

        if (result.status !== 'idle') {
            console.log(`  FAIL: Move ${i+1} (${m.desc}): got ${result.status} after ${result.frames} frames`);
            console.log(`  PC: 0x${cpu.pc.toString(16)}, keys remaining: ${zx81.keyBuffer.length}`);
            allOk = false;
            break;
        }

        const piece = getPiece(cpu, m.checkEmpty[0], m.checkEmpty[1]);
        if (piece !== 0x00) {
            console.log(`  FAIL: Move ${i+1} (${m.desc}): ${m.checkEmpty[0]}${m.checkEmpty[1]} not empty (0x${piece.toString(16)})`);
            allOk = false;
            break;
        }

        console.log(`  Move ${i+1} (${m.desc}) OK after ${result.frames} frames`);
    }

    if (allOk) {
        console.log('  Board after 3 moves:');
        console.log(boardToString(cpu));
        passed++;
    }
}

// --- Test 5: JR instruction correctness ---
console.log('\n=== Test 5: Unconditional JR jumps to correct target ===');
{
    const cpu = new Z80();
    // Place JR +4 at address 0x1000: opcode 0x18, offset 0x04
    // After fetching both bytes, PC = 0x1002. Target should be 0x1002 + 4 = 0x1006.
    cpu.wb(0x1000, 0x18); // JR
    cpu.wb(0x1001, 0x04); // offset +4
    cpu.wb(0x1006, 0x00); // NOP at target
    cpu.pc = 0x1000;
    cpu.step();
    if (assert(cpu.pc === 0x1006, `JR +4 from 0x1000: expected PC=0x1006, got 0x${cpu.pc.toString(16)}`)) {
        console.log('  JR forward: OK');
    }

    // Test JR backward: JR -3 at address 0x2000
    // After fetching both bytes, PC = 0x2002. Target should be 0x2002 + (-3) = 0x1FFF.
    cpu.wb(0x2000, 0x18); // JR
    cpu.wb(0x2001, 0xFD); // offset -3 (signed)
    cpu.pc = 0x2000;
    cpu.step();
    if (assert(cpu.pc === 0x1FFF, `JR -3 from 0x2000: expected PC=0x1FFF, got 0x${cpu.pc.toString(16)}`)) {
        console.log('  JR backward: OK');
        passed++;
    }
}

// --- Test 6: clearDisplay writes 0x76 row markers ---
console.log('\n=== Test 6: clearDisplay writes 0x76 row markers ===');
{
    const { cpu, zx81 } = setupEmulator();

    // Corrupt the display file to simulate a collapsed .P file (no 0x76 markers)
    const displayStart = zx81.getDisplayStart();
    for (let i = 0; i < 25 * 33; i++) {
        cpu.wb(displayStart + i, 0x00);
    }

    // clearDisplay should rebuild the full structure
    zx81.clearDisplay();

    // Verify leading 0x76
    let ok = true;
    if (!assert(cpu.rb(displayStart) === 0x76, 'Display file should start with 0x76')) ok = false;

    // Verify each row ends with 0x76
    for (let row = 0; row < 24 && ok; row++) {
        const markerAddr = displayStart + 1 + row * 33 + 32;
        const val = cpu.rb(markerAddr);
        if (!assert(val === 0x76,
            `Row ${row} should end with 0x76 at offset ${markerAddr - displayStart}, got 0x${val.toString(16)}`)) {
            ok = false;
        }
    }

    // Verify DF_CC points to first printable position
    const dfcc = cpu.rw(0x400E);
    if (!assert(dfcc === displayStart + 1, `DF_CC should be displayStart+1, got 0x${dfcc.toString(16)}`)) ok = false;

    if (ok) {
        console.log('  clearDisplay correctly writes all 0x76 row markers');
        passed++;
    }
}

// --- Test 7: tickFrames decrements FRAMES and wraps ---
console.log('\n=== Test 7: tickFrames decrements FRAMES with 16-bit wrap ===');
{
    const { cpu, zx81 } = setupEmulator();

    cpu.ww(0x4034, 0x8000);
    zx81.tickFrames();
    let ok = assert(cpu.rw(0x4034) === 0x7FFF,
        `FRAMES should go 0x8000 -> 0x7FFF, got 0x${cpu.rw(0x4034).toString(16)}`);

    cpu.ww(0x4034, 0x0000);
    zx81.tickFrames();
    if (!assert(cpu.rw(0x4034) === 0xFFFF,
        `FRAMES should wrap 0x0000 -> 0xFFFF, got 0x${cpu.rw(0x4034).toString(16)}`)) ok = false;

    if (ok) {
        console.log('  tickFrames decrements and wraps correctly');
        passed++;
    }
}

// --- Test 8: on-screen keyboard has a working DEL key ---
// The page's handleKey/updateKeyboard special-case 'DEL', but for a long
// time no key element emitted it, so touch users could not correct a
// mistyped coordinate. Guard the wiring until a browser-level test exists.
console.log('\n=== Test 8: index.html wires an on-screen DEL key ===');
{
    const fs = require('fs');
    const path = require('path');
    const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');

    let ok = assert(html.includes('data-key="DEL"'),
        'index.html should have a kb-key with data-key="DEL"');
    if (!assert(html.includes("k === 'DEL' && pos > 0"),
        'updateKeyboard should mark DEL valid once a character is typed')) ok = false;

    if (ok) {
        console.log('  on-screen DEL key present and handled');
        passed++;
    }
}

// --- Test 9: ALU flag semantics match the Python reference ---
// The JS core historically skipped P/V (overflow/parity) and left N/H
// stale on ADD HL / rotates. Nothing in the game tests those flags
// *today*, but a future opcode that does would diverge silently.
console.log('\n=== Test 9: ALU flag semantics (P/V, H, N) ===');
{
    const cpu = new Z80();
    const C = cpu.FLAG_C, N = cpu.FLAG_N, PV = cpu.FLAG_PV,
          H = cpu.FLAG_H, Z = cpu.FLAG_Z, S = cpu.FLAG_S;
    let ok = true;
    const check = (desc, actual, expected) => {
        if (!assert(actual === expected,
            `${desc}: flags 0x${actual.toString(16)}, expected 0x${expected.toString(16)}`)) ok = false;
    };

    // ADD overflow: 0x7F + 1 = 0x80 sets S, PV, H
    cpu.setFlagsAdd(0x7F, 0x01);
    check('ADD 7F+01', cpu.f, S | PV | H);

    // SUB overflow: 0x80 - 1 = 0x7F sets PV, H (plus N for subtraction)
    cpu.setFlagsSub(0x80, 0x01);
    check('SUB 80-01', cpu.f, N | PV | H);

    // CP equal: Z and N only
    cpu.setFlagsSub(0x42, 0x42);
    check('CP 42,42', cpu.f, N | Z);

    // Logic parity: 0x03 has even parity -> PV; 0x01 odd -> no PV
    cpu.setFlagsLogic(0x03);
    check('LOGIC 03', cpu.f, PV);
    cpu.setFlagsLogic(0x01);
    check('LOGIC 01', cpu.f, 0);

    // ADD HL,DE must clear H (and N), not just N
    cpu.f = N | H;
    cpu.setHL(0x1000); cpu.setDE(0x0100);
    cpu.wb(0x5000, 0x19); cpu.pc = 0x5000; cpu.step();
    check('ADD HL,DE', cpu.f & (N | H | C), 0);

    // RRCA must clear N and H, keep only its carry
    cpu.f = N | H;
    cpu.a = 0x01;
    cpu.wb(0x5001, 0x0F); cpu.pc = 0x5001; cpu.step();
    check('RRCA', cpu.f & (N | H | C), C);

    if (ok) {
        console.log('  flag semantics match the Python reference');
        passed++;
    }
}

// --- Test 10: cycle counter powers a runaway guard ---
// cycles/maxCycles were declared but never maintained, so drivers had
// no way to bound a spinning program. step() now counts instructions.
console.log('\n=== Test 10: cycle counting bounds a runaway program ===');
{
    const cpu = new Z80();
    cpu.wb(0x5000, 0x18); cpu.wb(0x5001, 0xFE);  // JR $ - spins forever
    cpu.pc = 0x5000;
    cpu.cycles = 0;
    cpu.maxCycles = 5000;
    let steps = 0;
    while (cpu.cycles < cpu.maxCycles) { cpu.step(); steps++; }
    let ok = assert(steps === 5000, `budget of 5000 should stop after 5000 steps, ran ${steps}`);
    if (!assert(cpu.pc === 0x5000 || cpu.pc === 0x5002 - 2,
        `JR $ should stay at 0x5000, pc = 0x${cpu.pc.toString(16)}`)) ok = false;

    if (ok) {
        console.log('  a spinning program exhausts its budget instead of hanging');
        passed++;
    }
}

// --- Summary ---
console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);
