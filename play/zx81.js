/**
 * ZX81 System Emulation for Chess
 * Handles display rendering, keyboard input, and ROM call interception.
 */

class ZX81 {
    constructor(cpu, canvas) {
        this.cpu = cpu;
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.charset = this.createCharset();

        this.scale = 3;
        this.charWidth = 8;
        this.charHeight = 8;

        this.canvas.width = 32 * this.charWidth * this.scale;
        this.canvas.height = 24 * this.charHeight * this.scale;

        this.keyBuffer = [];
        this.keyMap = this.createKeyMap();

        this.setupHandlers();
        this.setupKeyboard();
    }

    // Get display file address from D_FILE system variable
    getDisplayStart() {
        return this.cpu.rw(0x400C);
    }

    createKeyMap() {
        const map = {};
        for (let i = 0; i < 26; i++) {
            map[String.fromCharCode(65 + i)] = 0x26 + i;
            map[String.fromCharCode(97 + i)] = 0x26 + i;
        }
        for (let i = 0; i < 10; i++) map[String(i)] = 0x1C + i;
        map[' '] = 0x00;
        map['.'] = 0x1B;
        map['Enter'] = 0x76;
        return map;
    }

    createCharset() {
        const chars = new Map();
        chars.set(0x00, [0,0,0,0,0,0,0,0]); // Space
        chars.set(0x76, [0,0,0,0,0,0,0,0]); // Newline

        // Digits 0-9
        const digits = [
            [0x3C,0x46,0x4A,0x52,0x62,0x3C,0x00,0x00],
            [0x18,0x28,0x08,0x08,0x08,0x3E,0x00,0x00],
            [0x3C,0x42,0x02,0x1C,0x20,0x7E,0x00,0x00],
            [0x3C,0x42,0x0C,0x02,0x42,0x3C,0x00,0x00],
            [0x08,0x18,0x28,0x48,0x7E,0x08,0x00,0x00],
            [0x7E,0x40,0x7C,0x02,0x42,0x3C,0x00,0x00],
            [0x3C,0x40,0x7C,0x42,0x42,0x3C,0x00,0x00],
            [0x7E,0x02,0x04,0x08,0x10,0x10,0x00,0x00],
            [0x3C,0x42,0x3C,0x42,0x42,0x3C,0x00,0x00],
            [0x3C,0x42,0x42,0x3E,0x02,0x3C,0x00,0x00],
        ];
        for (let i = 0; i < 10; i++) chars.set(0x1C + i, digits[i]);

        // Letters A-Z
        const letters = [
            [0x3C,0x42,0x42,0x7E,0x42,0x42,0x00,0x00],
            [0x7C,0x42,0x7C,0x42,0x42,0x7C,0x00,0x00],
            [0x3C,0x42,0x40,0x40,0x42,0x3C,0x00,0x00],
            [0x78,0x44,0x42,0x42,0x44,0x78,0x00,0x00],
            [0x7E,0x40,0x7C,0x40,0x40,0x7E,0x00,0x00],
            [0x7E,0x40,0x7C,0x40,0x40,0x40,0x00,0x00],
            [0x3C,0x42,0x40,0x4E,0x42,0x3C,0x00,0x00],
            [0x42,0x42,0x7E,0x42,0x42,0x42,0x00,0x00],
            [0x3E,0x08,0x08,0x08,0x08,0x3E,0x00,0x00],
            [0x02,0x02,0x02,0x42,0x42,0x3C,0x00,0x00],
            [0x44,0x48,0x70,0x48,0x44,0x42,0x00,0x00],
            [0x40,0x40,0x40,0x40,0x40,0x7E,0x00,0x00],
            [0x42,0x66,0x5A,0x42,0x42,0x42,0x00,0x00],
            [0x42,0x62,0x52,0x4A,0x46,0x42,0x00,0x00],
            [0x3C,0x42,0x42,0x42,0x42,0x3C,0x00,0x00],
            [0x7C,0x42,0x42,0x7C,0x40,0x40,0x00,0x00],
            [0x3C,0x42,0x42,0x52,0x4A,0x3C,0x00,0x00],
            [0x7C,0x42,0x42,0x7C,0x44,0x42,0x00,0x00],
            [0x3C,0x40,0x3C,0x02,0x42,0x3C,0x00,0x00],
            [0x7F,0x08,0x08,0x08,0x08,0x08,0x00,0x00],
            [0x42,0x42,0x42,0x42,0x42,0x3C,0x00,0x00],
            [0x42,0x42,0x42,0x42,0x24,0x18,0x00,0x00],
            [0x42,0x42,0x42,0x5A,0x66,0x42,0x00,0x00],
            [0x42,0x24,0x18,0x18,0x24,0x42,0x00,0x00],
            [0x41,0x22,0x14,0x08,0x08,0x08,0x00,0x00],
            [0x7E,0x04,0x08,0x10,0x20,0x7E,0x00,0x00],
        ];
        for (let i = 0; i < 26; i++) chars.set(0x26 + i, letters[i]);

        // Special characters
        chars.set(0x1B, [0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00]); // .
        chars.set(0x0F, [0x3C,0x42,0x04,0x08,0x00,0x08,0x00,0x00]); // ?
        chars.set(0x15, [0x00,0x08,0x08,0x3E,0x08,0x08,0x00,0x00]); // +
        chars.set(0x16, [0x00,0x00,0x00,0x3E,0x00,0x00,0x00,0x00]); // -

        return chars;
    }

    setupHandlers() {
        const self = this;
        this.cpu.onPrintChar = (c) => self.printChar(c);
        this.cpu.onRomCall = (addr) => self.handleRomCall(addr);
    }

    setupKeyboard() {
        // Keyboard is now handled by index.html's input buffering system
        // This prevents duplicate key handling
    }

    getKey() {
        return this.keyBuffer.length > 0 ? this.keyBuffer.shift() : 0xFF;
    }

    handleRomCall(addr) {
        if (addr === 0x0A2A) { // ROM_CLS
            this.clearDisplay();
            return true;
        }
        return true; // Ignore unknown ROM calls
    }

    printChar(char) {
        const displayStart = this.getDisplayStart();
        let dfcc = this.cpu.rw(0x400E);
        if (dfcc < displayStart) dfcc = displayStart + 1;

        if (char === 0x76) {
            const offset = dfcc - displayStart;
            const row = Math.floor(offset / 33);
            dfcc = displayStart + (row + 1) * 33 + 1;
        } else {
            this.cpu.wb(dfcc, char);
            dfcc++;
        }
        this.cpu.ww(0x400E, dfcc);
    }

    clearDisplay() {
        const displayStart = this.getDisplayStart();
        let addr = displayStart + 1;
        for (let row = 0; row < 24; row++) {
            for (let col = 0; col < 32; col++) {
                this.cpu.wb(addr++, 0x00);
            }
            addr++; // Skip newline
        }
        this.cpu.ww(0x400E, displayStart + 1);
    }

    initSystemVars() {
        // Default display file location (will be overwritten by loadPFile)
        const defaultDisplayStart = 0x4469;
        this.cpu.ww(0x400C, defaultDisplayStart);
        this.cpu.ww(0x400E, defaultDisplayStart + 1);
        this.cpu.wb(0x4025, 0xFF);

        // Initialize display file
        let addr = defaultDisplayStart;
        this.cpu.wb(addr++, 0x76);
        for (let row = 0; row < 24; row++) {
            for (let col = 0; col < 32; col++) this.cpu.wb(addr++, 0x00);
            this.cpu.wb(addr++, 0x76);
        }
    }

    loadPFile(data) {
        const bytes = new Uint8Array(data);
        for (let i = 0; i < bytes.length; i++) {
            this.cpu.wb(0x4009 + i, bytes[i]);
        }
    }

    render() {
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        const displayStart = this.getDisplayStart();
        let addr = displayStart;

        // Skip initial newline if present
        if (this.cpu.rb(addr) === 0x76) addr++;

        for (let row = 0; row < 24; row++) {
            for (let col = 0; col < 32; col++) {
                const char = this.cpu.rb(addr);
                if (char === 0x76) break; // End of row
                this.drawChar(col, row, char);
                addr++;
            }
            // Find next newline
            while (this.cpu.rb(addr) !== 0x76 && addr < displayStart + 0x400) addr++;
            addr++; // Skip newline
        }
    }

    drawChar(col, row, code) {
        const inverse = (code & 0x80) !== 0;
        let bitmap = this.charset.get(code & 0x7F);
        if (!bitmap) bitmap = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF];

        const x = col * this.charWidth * this.scale;
        const y = row * this.charHeight * this.scale;

        for (let py = 0; py < 8; py++) {
            let bits = bitmap[py];
            if (inverse) bits = (~bits) & 0xFF;
            for (let px = 0; px < 8; px++) {
                if (bits & (0x80 >> px)) {
                    this.ctx.fillStyle = '#000000';
                    this.ctx.fillRect(x + px * this.scale, y + py * this.scale, this.scale, this.scale);
                }
            }
        }
    }
}

if (typeof window !== 'undefined') window.ZX81 = ZX81;
