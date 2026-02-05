/**
 * Z80 CPU Emulator for ZX81 Chess
 * A minimal Z80 emulator implementing the instructions needed for the 1K chess game.
 */

class Z80 {
    constructor() {
        this.memory = new Uint8Array(65536);
        this.a = 0; this.f = 0;
        this.b = 0; this.c = 0;
        this.d = 0; this.e = 0;
        this.h = 0; this.l = 0;
        this.pc = 0; this.sp = 0;
        this.ix = 0; this.iy = 0;
        this.halted = false;
        this.cycles = 0;
        this.maxCycles = 1000000;

        this.FLAG_C = 0x01; this.FLAG_N = 0x02; this.FLAG_PV = 0x04;
        this.FLAG_H = 0x10; this.FLAG_Z = 0x40; this.FLAG_S = 0x80;

        this.onPrintChar = null;
        this.onRomCall = null;
    }

    rb(addr) {
        const val = this.memory[addr & 0xFFFF];
        // Debug: only log non-FF LAST_K reads (filter out the noise)
        if ((addr & 0xFFFF) === 0x4025 && val !== 0xFF) {
            const el = document.getElementById('debug');
            if (el) el.textContent = 'R:' + val.toString(16) + ' ' + el.textContent.substring(0, 100);
        }
        return val;
    }
    wb(addr, val) {
        this.memory[addr & 0xFFFF] = val & 0xFF;
        // Debug: only log non-FF LAST_K writes
        if ((addr & 0xFFFF) === 0x4025 && (val & 0xFF) !== 0xFF) {
            const el = document.getElementById('debug');
            if (el) el.textContent = 'W:' + val.toString(16) + ' ' + el.textContent.substring(0, 100);
        }
    }
    debugLog(msg) {
        const el = document.getElementById('debug');
        if (el) el.textContent = msg + ' ' + el.textContent.substring(0, 150);
    }
    rw(addr) { return this.rb(addr) | (this.rb(addr + 1) << 8); }
    ww(addr, val) { this.wb(addr, val & 0xFF); this.wb(addr + 1, (val >> 8) & 0xFF); }
    fetch() { return this.rb(this.pc++); }
    fetchWord() { const lo = this.fetch(); return lo | (this.fetch() << 8); }

    bc() { return (this.b << 8) | this.c; }
    de() { return (this.d << 8) | this.e; }
    hl() { return (this.h << 8) | this.l; }
    setBC(v) { this.b = (v >> 8) & 0xFF; this.c = v & 0xFF; }
    setDE(v) { this.d = (v >> 8) & 0xFF; this.e = v & 0xFF; }
    setHL(v) { this.h = (v >> 8) & 0xFF; this.l = v & 0xFF; }

    push(val) { this.sp = (this.sp - 2) & 0xFFFF; this.ww(this.sp, val); }
    pop() { const val = this.rw(this.sp); this.sp = (this.sp + 2) & 0xFFFF; return val; }

    getFlag(flag) { return (this.f & flag) !== 0; }
    signedByte(b) { return b > 127 ? b - 256 : b; }

    setFlagsAdd(a, b, carry = 0) {
        const result = a + b + carry;
        const result8 = result & 0xFF;
        this.f = 0;
        if (result8 === 0) this.f |= this.FLAG_Z;
        if (result8 & 0x80) this.f |= this.FLAG_S;
        if (result > 0xFF) this.f |= this.FLAG_C;
        if (((a & 0x0F) + (b & 0x0F) + carry) > 0x0F) this.f |= this.FLAG_H;
        return result8;
    }

    setFlagsSub(a, b, carry = 0) {
        const result = a - b - carry;
        const result8 = result & 0xFF;
        this.f = this.FLAG_N;
        if (result8 === 0) this.f |= this.FLAG_Z;
        if (result8 & 0x80) this.f |= this.FLAG_S;
        if (result < 0) this.f |= this.FLAG_C;
        if (((a & 0x0F) - (b & 0x0F) - carry) < 0) this.f |= this.FLAG_H;
        return result8;
    }

    setFlagsLogic(result) {
        this.f = 0;
        if (result === 0) this.f |= this.FLAG_Z;
        if (result & 0x80) this.f |= this.FLAG_S;
    }

    setFlagsInc(val) {
        const result = (val + 1) & 0xFF;
        this.f = (this.f & this.FLAG_C);
        if (result === 0) this.f |= this.FLAG_Z;
        if (result & 0x80) this.f |= this.FLAG_S;
        if (val === 0x7F) this.f |= this.FLAG_PV;
        if ((val & 0x0F) === 0x0F) this.f |= this.FLAG_H;
        return result;
    }

    setFlagsDec(val) {
        const result = (val - 1) & 0xFF;
        this.f = (this.f & this.FLAG_C) | this.FLAG_N;
        if (result === 0) this.f |= this.FLAG_Z;
        if (result & 0x80) this.f |= this.FLAG_S;
        if (val === 0x80) this.f |= this.FLAG_PV;
        if ((val & 0x0F) === 0x00) this.f |= this.FLAG_H;
        return result;
    }

    loadBinary(data, addr) {
        for (let i = 0; i < data.length; i++) this.memory[addr + i] = data[i];
    }

    getReg(idx) {
        const regs = [this.b, this.c, this.d, this.e, this.h, this.l, this.rb(this.hl()), this.a];
        return regs[idx];
    }

    setReg(idx, val) {
        val &= 0xFF;
        if (idx === 0) this.b = val;
        else if (idx === 1) this.c = val;
        else if (idx === 2) this.d = val;
        else if (idx === 3) this.e = val;
        else if (idx === 4) this.h = val;
        else if (idx === 5) this.l = val;
        else if (idx === 6) this.wb(this.hl(), val);
        else this.a = val;
    }

    step() {
        // Check for ROM calls
        if (this.pc < 0x4000 && this.onRomCall) {
            if (this.onRomCall(this.pc)) {
                this.pc = this.pop();
                return;
            }
        }

        const op = this.fetch();

        if (op === 0x00) return; // NOP
        if (op === 0x76) { this.halted = true; return 'halt'; } // HALT

        // LD r, r'
        if ((op & 0xC0) === 0x40 && op !== 0x76) {
            this.setReg((op >> 3) & 7, this.getReg(op & 7));
            return;
        }

        // LD r, n
        if ((op & 0xC7) === 0x06) { this.setReg((op >> 3) & 7, this.fetch()); return; }

        // LD A, (BC/DE/nn)
        if (op === 0x0A) { this.a = this.rb(this.bc()); return; }
        if (op === 0x1A) { this.a = this.rb(this.de()); return; }
        if (op === 0x3A) { this.a = this.rb(this.fetchWord()); return; }

        // LD (BC/DE/nn), A
        if (op === 0x02) { this.wb(this.bc(), this.a); return; }
        if (op === 0x12) { this.wb(this.de(), this.a); return; }
        if (op === 0x32) { this.wb(this.fetchWord(), this.a); return; }

        // LD rr, nn
        if (op === 0x01) { this.setBC(this.fetchWord()); return; }
        if (op === 0x11) { this.setDE(this.fetchWord()); return; }
        if (op === 0x21) { this.setHL(this.fetchWord()); return; }
        if (op === 0x31) { this.sp = this.fetchWord(); return; }

        // LD HL, (nn) / LD (nn), HL
        if (op === 0x2A) { this.setHL(this.rw(this.fetchWord())); return; }
        if (op === 0x22) { this.ww(this.fetchWord(), this.hl()); return; }
        if (op === 0xF9) { this.sp = this.hl(); return; }

        // PUSH/POP
        if (op === 0xC5) { this.push(this.bc()); return; }
        if (op === 0xD5) { this.push(this.de()); return; }
        if (op === 0xE5) { this.push(this.hl()); return; }
        if (op === 0xF5) { this.push((this.a << 8) | this.f); return; }
        if (op === 0xC1) { this.setBC(this.pop()); return; }
        if (op === 0xD1) { this.setDE(this.pop()); return; }
        if (op === 0xE1) { this.setHL(this.pop()); return; }
        if (op === 0xF1) { const v = this.pop(); this.a = (v >> 8) & 0xFF; this.f = v & 0xFF; return; }

        // EX DE, HL
        if (op === 0xEB) { [this.d, this.h] = [this.h, this.d]; [this.e, this.l] = [this.l, this.e]; return; }

        // ALU operations
        if ((op & 0xF8) === 0x80) { this.a = this.setFlagsAdd(this.a, this.getReg(op & 7)); return; }
        if ((op & 0xF8) === 0x88) { this.a = this.setFlagsAdd(this.a, this.getReg(op & 7), this.getFlag(this.FLAG_C) ? 1 : 0); return; }
        if ((op & 0xF8) === 0x90) { this.a = this.setFlagsSub(this.a, this.getReg(op & 7)); return; }
        if ((op & 0xF8) === 0x98) { this.a = this.setFlagsSub(this.a, this.getReg(op & 7), this.getFlag(this.FLAG_C) ? 1 : 0); return; }
        if ((op & 0xF8) === 0xA0) { this.a &= this.getReg(op & 7); this.setFlagsLogic(this.a); this.f |= this.FLAG_H; return; }
        if ((op & 0xF8) === 0xA8) { this.a ^= this.getReg(op & 7); this.setFlagsLogic(this.a); return; }
        if ((op & 0xF8) === 0xB0) { this.a |= this.getReg(op & 7); this.setFlagsLogic(this.a); return; }
        if ((op & 0xF8) === 0xB8) { this.setFlagsSub(this.a, this.getReg(op & 7)); return; }

        if (op === 0xC6) { this.a = this.setFlagsAdd(this.a, this.fetch()); return; }
        if (op === 0xCE) { this.a = this.setFlagsAdd(this.a, this.fetch(), this.getFlag(this.FLAG_C) ? 1 : 0); return; }
        if (op === 0xD6) { this.a = this.setFlagsSub(this.a, this.fetch()); return; }
        if (op === 0xDE) { this.a = this.setFlagsSub(this.a, this.fetch(), this.getFlag(this.FLAG_C) ? 1 : 0); return; }
        if (op === 0xE6) { this.a &= this.fetch(); this.setFlagsLogic(this.a); this.f |= this.FLAG_H; return; }
        if (op === 0xEE) { this.a ^= this.fetch(); this.setFlagsLogic(this.a); return; }
        if (op === 0xF6) { this.a |= this.fetch(); this.setFlagsLogic(this.a); return; }
        if (op === 0xFE) { this.setFlagsSub(this.a, this.fetch()); return; }

        // INC/DEC r
        if ((op & 0xC7) === 0x04) { const r = (op >> 3) & 7; this.setReg(r, this.setFlagsInc(this.getReg(r))); return; }
        if ((op & 0xC7) === 0x05) { const r = (op >> 3) & 7; this.setReg(r, this.setFlagsDec(this.getReg(r))); return; }

        // INC/DEC rr
        if (op === 0x03) { this.setBC((this.bc() + 1) & 0xFFFF); return; }
        if (op === 0x13) { this.setDE((this.de() + 1) & 0xFFFF); return; }
        if (op === 0x23) { this.setHL((this.hl() + 1) & 0xFFFF); return; }
        if (op === 0x33) { this.sp = (this.sp + 1) & 0xFFFF; return; }
        if (op === 0x0B) { this.setBC((this.bc() - 1) & 0xFFFF); return; }
        if (op === 0x1B) { this.setDE((this.de() - 1) & 0xFFFF); return; }
        if (op === 0x2B) { this.setHL((this.hl() - 1) & 0xFFFF); return; }
        if (op === 0x3B) { this.sp = (this.sp - 1) & 0xFFFF; return; }

        // ADD HL, rr
        if (op === 0x09 || op === 0x19 || op === 0x29 || op === 0x39) {
            let val = op === 0x09 ? this.bc() : op === 0x19 ? this.de() : op === 0x29 ? this.hl() : this.sp;
            const result = this.hl() + val;
            this.f &= ~(this.FLAG_C | this.FLAG_N);
            if (result > 0xFFFF) this.f |= this.FLAG_C;
            this.setHL(result & 0xFFFF);
            return;
        }

        // Jumps
        if (op === 0xC3) { this.pc = this.fetchWord(); return; }
        if (op === 0xE9) { this.pc = this.hl(); return; }
        if (op === 0xC2) { const addr = this.fetchWord(); if (!this.getFlag(this.FLAG_Z)) this.pc = addr; return; }
        if (op === 0xCA) { const addr = this.fetchWord(); if (this.getFlag(this.FLAG_Z)) this.pc = addr; return; }
        if (op === 0xD2) { const addr = this.fetchWord(); if (!this.getFlag(this.FLAG_C)) this.pc = addr; return; }
        if (op === 0xDA) { const addr = this.fetchWord(); if (this.getFlag(this.FLAG_C)) this.pc = addr; return; }

        // JR
        if (op === 0x18) { this.pc = (this.pc + this.signedByte(this.fetch())) & 0xFFFF; return; }
        if (op === 0x20) { const e = this.signedByte(this.fetch()); if (!this.getFlag(this.FLAG_Z)) this.pc = (this.pc + e) & 0xFFFF; return; }
        if (op === 0x28) { const e = this.signedByte(this.fetch()); if (this.getFlag(this.FLAG_Z)) this.pc = (this.pc + e) & 0xFFFF; return; }
        if (op === 0x30) { const e = this.signedByte(this.fetch()); if (!this.getFlag(this.FLAG_C)) this.pc = (this.pc + e) & 0xFFFF; return; }
        if (op === 0x38) { const e = this.signedByte(this.fetch()); if (this.getFlag(this.FLAG_C)) this.pc = (this.pc + e) & 0xFFFF; return; }

        // DJNZ
        if (op === 0x10) {
            const e = this.signedByte(this.fetch());
            this.b = (this.b - 1) & 0xFF;
            if (this.b !== 0) this.pc = (this.pc + e) & 0xFFFF;
            return;
        }

        // CALL
        if (op === 0xCD) { const addr = this.fetchWord(); this.push(this.pc); this.pc = addr; return; }
        if (op === 0xC4) { const addr = this.fetchWord(); if (!this.getFlag(this.FLAG_Z)) { this.push(this.pc); this.pc = addr; } return; }
        if (op === 0xCC) { const addr = this.fetchWord(); if (this.getFlag(this.FLAG_Z)) { this.push(this.pc); this.pc = addr; } return; }
        if (op === 0xD4) { const addr = this.fetchWord(); if (!this.getFlag(this.FLAG_C)) { this.push(this.pc); this.pc = addr; } return; }
        if (op === 0xDC) { const addr = this.fetchWord(); if (this.getFlag(this.FLAG_C)) { this.push(this.pc); this.pc = addr; } return; }

        // RET
        if (op === 0xC9) { this.pc = this.pop(); return; }
        if (op === 0xC0) { if (!this.getFlag(this.FLAG_Z)) this.pc = this.pop(); return; }
        if (op === 0xC8) { if (this.getFlag(this.FLAG_Z)) this.pc = this.pop(); return; }
        if (op === 0xD0) { if (!this.getFlag(this.FLAG_C)) this.pc = this.pop(); return; }
        if (op === 0xD8) { if (this.getFlag(this.FLAG_C)) this.pc = this.pop(); return; }

        // RST
        if ((op & 0xC7) === 0xC7) {
            const addr = op & 0x38;
            if (addr === 0x10 && this.onPrintChar) { this.onPrintChar(this.a); return; }
            if (addr === 0x08) return; // Error handler - ignore
            this.push(this.pc);
            this.pc = addr;
            return;
        }

        // Rotate A
        if (op === 0x07) { const c = (this.a >> 7) & 1; this.a = ((this.a << 1) | c) & 0xFF; this.f = (this.f & ~this.FLAG_C) | (c ? this.FLAG_C : 0); return; }
        if (op === 0x0F) { const c = this.a & 1; this.a = ((this.a >> 1) | (c << 7)) & 0xFF; this.f = (this.f & ~this.FLAG_C) | (c ? this.FLAG_C : 0); return; }
        if (op === 0x17) { const c = (this.a >> 7) & 1; this.a = ((this.a << 1) | (this.getFlag(this.FLAG_C) ? 1 : 0)) & 0xFF; this.f = (this.f & ~this.FLAG_C) | (c ? this.FLAG_C : 0); return; }
        if (op === 0x1F) { const c = this.a & 1; this.a = ((this.a >> 1) | ((this.getFlag(this.FLAG_C) ? 1 : 0) << 7)) & 0xFF; this.f = (this.f & ~this.FLAG_C) | (c ? this.FLAG_C : 0); return; }

        // CPL, SCF, CCF
        if (op === 0x2F) { this.a = (~this.a) & 0xFF; this.f |= this.FLAG_N | this.FLAG_H; return; }
        if (op === 0x37) { this.f = (this.f & ~this.FLAG_N) | this.FLAG_C; return; }
        if (op === 0x3F) { const c = this.getFlag(this.FLAG_C); this.f = (this.f & ~(this.FLAG_N | this.FLAG_C)) | (c ? 0 : this.FLAG_C); return; }

        // CB prefix
        if (op === 0xCB) return this.executeCB(this.fetch());

        // ED prefix
        if (op === 0xED) return this.executeED(this.fetch());

        // DD/FD prefixes (IX/IY) - minimal support
        if (op === 0xDD) return this.executeDD(this.fetch());
        if (op === 0xFD) return this.executeFD(this.fetch());

        console.log(`Unknown opcode: ${op.toString(16)} at ${(this.pc-1).toString(16)}`);
        return 'error';
    }

    executeCB(op) {
        const idx = op & 7;
        let val = this.getReg(idx);

        // BIT b, r
        if ((op & 0xC0) === 0x40) {
            const bit = (op >> 3) & 7;
            this.f = (this.f & this.FLAG_C) | this.FLAG_H;
            if (!(val & (1 << bit))) this.f |= this.FLAG_Z;
            return;
        }
        // RES b, r
        if ((op & 0xC0) === 0x80) {
            this.setReg(idx, val & ~(1 << ((op >> 3) & 7)));
            return;
        }
        // SET b, r
        if ((op & 0xC0) === 0xC0) {
            this.setReg(idx, val | (1 << ((op >> 3) & 7)));
            return;
        }
        // SRL r
        if ((op & 0xF8) === 0x38) {
            const c = val & 1;
            val = (val >> 1) & 0xFF;
            this.setFlagsLogic(val);
            if (c) this.f |= this.FLAG_C;
            this.setReg(idx, val);
            return;
        }
        // SLA r
        if ((op & 0xF8) === 0x20) {
            const c = (val >> 7) & 1;
            val = (val << 1) & 0xFF;
            this.setFlagsLogic(val);
            if (c) this.f |= this.FLAG_C;
            this.setReg(idx, val);
            return;
        }
        // RL r
        if ((op & 0xF8) === 0x10) {
            const c = (val >> 7) & 1;
            val = ((val << 1) | (this.getFlag(this.FLAG_C) ? 1 : 0)) & 0xFF;
            this.setFlagsLogic(val);
            if (c) this.f |= this.FLAG_C;
            this.setReg(idx, val);
            return;
        }
        // RR r
        if ((op & 0xF8) === 0x18) {
            const c = val & 1;
            val = ((val >> 1) | ((this.getFlag(this.FLAG_C) ? 1 : 0) << 7)) & 0xFF;
            this.setFlagsLogic(val);
            if (c) this.f |= this.FLAG_C;
            this.setReg(idx, val);
            return;
        }
        console.log(`Unknown CB opcode: ${op.toString(16)}`);
    }

    executeED(op) {
        if (op === 0x44) { this.a = this.setFlagsSub(0, this.a); return; } // NEG
        if (op === 0x4B) { this.setBC(this.rw(this.fetchWord())); return; }
        if (op === 0x5B) { this.setDE(this.rw(this.fetchWord())); return; }
        if (op === 0x7B) { this.sp = this.rw(this.fetchWord()); return; }
        if (op === 0x43) { this.ww(this.fetchWord(), this.bc()); return; }
        if (op === 0x53) { this.ww(this.fetchWord(), this.de()); return; }
        if (op === 0x73) { this.ww(this.fetchWord(), this.sp); return; }
        // LDIR
        if (op === 0xB0) {
            do {
                this.wb(this.de(), this.rb(this.hl()));
                this.setHL((this.hl() + 1) & 0xFFFF);
                this.setDE((this.de() + 1) & 0xFFFF);
                this.setBC((this.bc() - 1) & 0xFFFF);
            } while (this.bc() !== 0);
            return;
        }
        console.log(`Unknown ED opcode: ${op.toString(16)}`);
    }

    executeDD(op) {
        if (op === 0x21) { this.ix = this.fetchWord(); return; }
        if (op === 0xE5) { this.push(this.ix); return; }
        if (op === 0xE1) { this.ix = this.pop(); return; }
        if ((op & 0xC7) === 0x46 && op !== 0x76) {
            const d = this.signedByte(this.fetch());
            this.setReg((op >> 3) & 7, this.rb((this.ix + d) & 0xFFFF));
            return;
        }
        if (op === 0x19) { const r = this.ix + this.de(); this.f &= ~this.FLAG_C; if (r > 0xFFFF) this.f |= this.FLAG_C; this.ix = r & 0xFFFF; return; }
        console.log(`Unknown DD opcode: ${op.toString(16)}`);
    }

    executeFD(op) {
        if (op === 0x21) { this.iy = this.fetchWord(); return; }
        if (op === 0xE5) { this.push(this.iy); return; }
        if (op === 0xE1) { this.iy = this.pop(); return; }
        console.log(`Unknown FD opcode: ${op.toString(16)}`);
    }
}

if (typeof window !== 'undefined') window.Z80 = Z80;
