#!/usr/bin/env node
// JS half of tools/opcode_check.py: reads a JSON array of instruction
// byte sequences on stdin, single-steps each through a fresh Z80, and
// prints the indexes of any that hit the 'error' (unimplemented) path.

const { Z80 } = require('../play/emu_test_lib.js');

let input = '';
process.stdin.on('data', (d) => { input += d; });
process.stdin.on('end', () => {
    const instructions = JSON.parse(input);
    const failures = [];

    // Silence the emulator's "Unknown opcode" logging during probes
    const log = console.log;
    console.log = () => {};

    instructions.forEach((bytes, i) => {
        const cpu = new Z80();
        const addr = 0x5000;
        bytes.forEach((b, j) => cpu.wb(addr + j, b));
        cpu.pc = addr;
        cpu.sp = 0x7000;
        if (cpu.step() === 'error') failures.push(i);
    });

    console.log = log;
    console.log(JSON.stringify(failures));
    process.exit(failures.length ? 1 : 0);
});
