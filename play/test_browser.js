#!/usr/bin/env node
/**
 * Browser smoke test for play/index.html, driven by Playwright.
 *
 * The Node tests (test_js_emulator.js) exercise the Z80 core directly;
 * this is the only coverage for the page's inline script - input
 * assembly, the on-screen keyboard (including DEL), the skin toggle,
 * and the modern click-to-move board.
 *
 * The browser does NOT pin FRAMES, so the AI's tie-break is genuinely
 * random - assertions here must hold for any legal AI reply.
 *
 * Run: make browser-test   (needs `npm install playwright` + chromium)
 */

const path = require('path');
const { chromium } = require('playwright');

let passed = 0, failed = 0;

function assert(cond, msg) {
    if (!cond) {
        console.log(`  FAIL: ${msg}`);
        failed++;
        return false;
    }
    return true;
}

async function pressKey(page, key) {
    const el = page.locator(`.kb-key[data-key="${key}"]`);
    await page.waitForFunction(
        (k) => document.querySelector(`.kb-key[data-key="${k}"]`).classList.contains('valid'),
        key);
    await el.dispatchEvent('pointerdown');
}

async function waitForInputTurn(page) {
    // s0 shows the 'active' cursor class whenever it's the player's move
    await page.waitForFunction(
        () => document.getElementById('s0').className.includes('active'),
        null, { timeout: 15000 });
}

async function pieceAt(page, sq) {
    return page.evaluate((s) => {
        const use = document.querySelector(`.square[data-sq="${s}"] use`);
        return use ? use.getAttribute('href') : null;
    }, sq);
}

async function waitForPiece(page, sq, expected) {
    // The modern board re-renders on the 50ms frame tick - wait for it
    try {
        await page.waitForFunction(([s, exp]) => {
            const use = document.querySelector(`.square[data-sq="${s}"] use`);
            return (use ? use.getAttribute('href') : null) === exp;
        }, [sq, expected], { timeout: 5000 });
        return expected;
    } catch (e) {
        return pieceAt(page, sq);
    }
}

async function main() {
    // CHROMIUM_PATH lets environments with a system chromium skip
    // `npx playwright install` (CI installs the matching browser).
    const browser = await chromium.launch(
        process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
    const page = await browser.newPage();
    await page.goto('file://' + path.join(__dirname, 'index.html'));

    // --- Test 1: page boots into a running game ---
    console.log('\n=== Browser 1: page loads and waits for input ===');
    await waitForInputTurn(page);
    console.log('  game auto-started, player to move');
    passed++;

    // --- Test 2: on-screen typing with DEL correction (ZX81 skin) ---
    console.log('\n=== Browser 2: type E2, DEL, then complete E2E4 ===');
    await pressKey(page, 'E');
    await pressKey(page, '2');
    let s1 = await page.locator('#s1').textContent();
    let ok = assert(s1 === '2', `slot s1 should show '2', got '${s1}'`);
    await pressKey(page, 'DEL');
    s1 = await page.locator('#s1').textContent();
    if (!assert(s1 === '_', `after DEL, slot s1 should be '_', got '${s1}'`)) ok = false;
    await pressKey(page, '2');
    await pressKey(page, 'E');
    await pressKey(page, '4');   // 4th char auto-sends the move
    await waitForInputTurn(page);  // AI has replied
    if (ok) { console.log('  DEL corrects input; move was sent and AI replied'); passed++; }

    // --- Test 3: modern skin reflects the position ---
    console.log('\n=== Browser 3: skin toggle and board state ===');
    await page.locator('#skin-toggle').dispatchEvent('click');
    const e4 = await waitForPiece(page, 28, '#wP');   // e4 = rank 3 * 8 + file 4
    const e2 = await pieceAt(page, 12);
    ok = assert(e4 === '#wP', `e4 should hold a white pawn, got ${e4}`);
    if (!assert(e2 === null, `e2 should be empty after E2E4, got ${e2}`)) ok = false;
    const counts = await page.evaluate(() => {
        const uses = [...document.querySelectorAll('.square use')];
        return {
            white: uses.filter(u => u.getAttribute('href').startsWith('#w')).length,
            black: uses.filter(u => u.getAttribute('href').startsWith('#b')).length,
        };
    });
    if (!assert(counts.white === 16 && counts.black === 16,
        `expected 16 v 16 pieces after one quiet turn, got ${counts.white} v ${counts.black}`)) ok = false;
    if (ok) { console.log('  modern board shows the position (16 v 16, wP on e4)'); passed++; }

    // --- Test 4: modern click-to-move ---
    console.log('\n=== Browser 4: click-to-move G1 -> F3 ===');
    await page.locator('.square[data-sq="6"]').dispatchEvent('pointerdown');   // g1
    await page.locator('.square[data-sq="21"]').dispatchEvent('pointerdown');  // f3
    await waitForInputTurn(page);
    const f3 = await waitForPiece(page, 21, '#wN');
    if (assert(f3 === '#wN', `f3 should hold the white knight, got ${f3}`)) {
        console.log('  knight moved by clicking, AI replied');
        passed++;
    }

    // --- Test 5: NEW GAME resets the board ---
    console.log('\n=== Browser 5: reset ===');
    await page.locator('#btn-modern-reset').dispatchEvent('click');
    await waitForInputTurn(page);
    const e2again = await waitForPiece(page, 12, '#wP');
    const f3again = await pieceAt(page, 21);
    if (assert(e2again === '#wP' && f3again === null,
        `after reset e2 should be a pawn and f3 empty, got ${e2again}/${f3again}`)) {
        console.log('  reset restores the starting position');
        passed++;
    }

    // --- Test 6: move history records and undo rewinds a full turn ---
    console.log('\n=== Browser 6: history + undo ===');
    await page.locator('.square[data-sq="12"]').dispatchEvent('pointerdown');  // e2
    await page.locator('.square[data-sq="28"]').dispatchEvent('pointerdown');  // e4
    await waitForInputTurn(page);
    await page.waitForFunction(() =>
        document.querySelectorAll('#history-list li').length === 1);
    const entry = await page.locator('#history-list li').first().textContent();
    ok = assert(entry.startsWith('E2-E4 ') && entry.length > 6,
        `history should show E2-E4 plus the AI reply, got '${entry}'`);
    await page.locator('#btn-modern-undo').dispatchEvent('click');
    const e2back = await waitForPiece(page, 12, '#wP');
    if (!assert(e2back === '#wP', `after undo, e2 should hold the pawn again, got ${e2back}`)) ok = false;
    const histCount = await page.evaluate(() =>
        document.querySelectorAll('#history-list li').length);
    if (!assert(histCount === 0, `after undo, history should be empty, got ${histCount} rows`)) ok = false;
    const undoDisabled = await page.evaluate(() =>
        document.getElementById('btn-modern-undo').disabled);
    if (!assert(undoDisabled, 'undo button should disable when the stack empties')) ok = false;
    if (ok) { console.log('  history records the turn; undo rewinds it'); passed++; }

    // --- Test 7: undo revives a finished game ---
    console.log('\n=== Browser 7: undo after game over ===');
    await page.locator('.square[data-sq="3"]').dispatchEvent('pointerdown');   // d1 queen
    await page.locator('.square[data-sq="60"]').dispatchEvent('pointerdown');  // e8 king
    await page.waitForFunction(() =>
        document.getElementById('game-over-overlay').classList.contains('visible'),
        null, { timeout: 15000 });
    console.log('  captured the king, game over shown');
    await page.locator('#btn-modern-undo').dispatchEvent('click');
    await waitForInputTurn(page);
    const kingBack = await waitForPiece(page, 60, '#bK');
    const overlayGone = await page.evaluate(() =>
        !document.getElementById('game-over-overlay').classList.contains('visible'));
    if (assert(kingBack === '#bK' && overlayGone,
        `after undo the black king should be back and overlay hidden, got ${kingBack}/${overlayGone}`)) {
        console.log('  undo revives the game from the game-over screen');
        passed++;
    }

    // --- Test 8: board flip and keyboard accessibility ---
    console.log('\n=== Browser 8: flip + keyboard access ===');
    await page.locator('#btn-modern-flip').dispatchEvent('click');
    ok = await page.evaluate(() =>
        document.getElementById('modern-view').classList.contains('flipped') &&
        document.getElementById('btn-modern-flip').getAttribute('aria-pressed') === 'true');
    assert(ok, 'flip button should add the flipped class and set aria-pressed');
    await page.locator('#btn-modern-flip').dispatchEvent('click');

    // Squares and membrane keys are keyboard-operable buttons
    const a11y = await page.evaluate(() => {
        const sq = document.querySelector('.square[data-sq="12"]');
        const key = document.querySelector('.kb-key[data-key="E"]');
        return {
            sqRole: sq.getAttribute('role'), sqTab: sq.tabIndex,
            sqLabel: sq.getAttribute('aria-label'),
            keyRole: key.getAttribute('role'), keyTab: key.tabIndex,
            zoomable: !document.querySelector('meta[name="viewport"]')
                .content.includes('user-scalable=no'),
        };
    });
    if (!assert(a11y.sqRole === 'button' && a11y.sqTab === 0 &&
        a11y.sqLabel === 'e2, white pawn',
        `square a11y wrong: ${JSON.stringify(a11y)}`)) ok = false;
    if (!assert(a11y.keyRole === 'button' && a11y.keyTab === 0,
        'membrane keys should be focusable buttons')) ok = false;
    if (!assert(a11y.zoomable, 'pinch zoom should not be blocked')) ok = false;

    // Move a piece with the keyboard only: focus e2, Enter, focus e4, Enter
    await page.evaluate(() => document.querySelector('.square[data-sq="12"]').focus());
    await page.keyboard.press('Enter');
    await page.evaluate(() => document.querySelector('.square[data-sq="28"]').focus());
    await page.keyboard.press('Enter');
    await waitForInputTurn(page);
    const kbE4 = await waitForPiece(page, 28, '#wP');
    if (!assert(kbE4 === '#wP', `keyboard-only move failed, e4 holds ${kbE4}`)) ok = false;
    if (ok) { console.log('  flip toggles, squares/keys keyboard-operable, zoom allowed'); passed++; }

    // --- Test 9: legality hints toggle ---
    console.log('\n=== Browser 9: legal-move hints ===');
    await page.locator('#btn-modern-reset').dispatchEvent('click');
    await waitForInputTurn(page);
    await page.locator('#btn-modern-hints').dispatchEvent('click');   // hints on
    await page.locator('.square[data-sq="12"]').dispatchEvent('pointerdown');  // select e2
    let hints = await page.evaluate(() =>
        [...document.querySelectorAll('.square.hint')].map(s => +s.dataset.sq).sort((a, b) => a - b));
    ok = assert(JSON.stringify(hints) === JSON.stringify([20, 28]),
        `e2 pawn hints should be e3+e4 [20,28], got [${hints}]`);
    // Deselecting by completing a move clears the dots
    await page.locator('.square[data-sq="28"]').dispatchEvent('pointerdown');
    await waitForInputTurn(page);
    hints = await page.evaluate(() => document.querySelectorAll('.square.hint').length);
    if (!assert(hints === 0, `hints should clear after the move, got ${hints}`)) ok = false;
    // Toggle off: selecting shows no dots
    await page.locator('#btn-modern-hints').dispatchEvent('click');
    await page.locator('.square[data-sq="6"]').dispatchEvent('pointerdown');   // g1 knight
    hints = await page.evaluate(() => document.querySelectorAll('.square.hint').length);
    if (!assert(hints === 0, `hints off should show no dots, got ${hints}`)) ok = false;
    if (ok) { console.log('  hints show real pawn moves, clear on move, respect toggle'); passed++; }

    // --- Test 10: game persists across a reload and resumes ---
    console.log('\n=== Browser 10: save + resume across reload ===');
    // Test 9 ended after a completed E2-E4 turn, so a save exists
    await page.reload();
    await waitForInputTurn(page);
    const resumeVisible = await page.evaluate(() =>
        !document.getElementById('btn-modern-resume').hidden);
    ok = assert(resumeVisible, 'resume button should appear when a save exists');
    // Fresh boot starts from the initial position...
    const freshE4 = await pieceAt(page, 28);
    if (!assert(freshE4 === null, `fresh boot should not replay the save, e4 = ${freshE4}`)) ok = false;
    // ...and resuming brings the game back
    await page.evaluate(() => document.getElementById('skin-toggle').click());
    await page.locator('#btn-modern-resume').dispatchEvent('click');
    const resumedE4 = await waitForPiece(page, 28, '#wP');
    if (!assert(resumedE4 === '#wP', `resume should restore the pawn on e4, got ${resumedE4}`)) ok = false;
    const resumedHist = await page.evaluate(() =>
        document.querySelectorAll('#history-list li').length);
    if (!assert(resumedHist === 1, `resume should restore the history, got ${resumedHist} rows`)) ok = false;
    if (ok) { console.log('  saved game survives reload and resumes on demand'); passed++; }

    await browser.close();
    console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
    process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => { console.error(err); process.exit(1); });
