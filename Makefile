# ZX81 1K Chess - Build System
#
# Requires:
#   - pasmo (Z80 assembler)
#   - python3
#
# Targets:
#   make          - Build and test
#   make build    - Build chess.bin and chess.p
#   make test     - Run all tests (basic + comprehensive)
#   make clean    - Remove built files

ASM = pasmo
PYTHON = python3

SRC = src/chess.asm
BIN = chess.bin
PFILE = chess.p

# Hard ceiling for the assembled binary. The game must never grow
# past this; free bytes elsewhere before adding anything new.
MAXSIZE ?= 984

.PHONY: all build test diff-test clean

all: build test

build: $(PFILE) hexdump.txt

$(BIN): $(SRC)
	$(ASM) --bin $(SRC) $(BIN)
	@actual=$$(wc -c < $(BIN)); \
	echo "Assembled: $$actual bytes (limit $(MAXSIZE))"; \
	if [ $$actual -gt $(MAXSIZE) ]; then \
		echo "FAIL: $(BIN) is $$actual bytes, exceeds $(MAXSIZE)-byte limit"; \
		rm -f $(BIN); \
		exit 1; \
	fi

$(PFILE): $(BIN) tools/make_p_file.py
	$(PYTHON) tools/make_p_file.py $(BIN) $(PFILE)

# hexdump.txt is generated - never edit it by hand
hexdump.txt: $(BIN) tools/make_hexdump.py
	$(PYTHON) tools/make_hexdump.py $(BIN) hexdump.txt

test: $(PFILE)
	@echo "=== Basic Tests ==="
	$(PYTHON) test_harness.py
	@echo ""
	@echo "=== Comprehensive Test Suite ==="
	$(PYTHON) tests/test_chess.py
	@echo ""
	@echo "=== JS Emulator Tests ==="
	node play/test_js_emulator.js
	@echo ""
	@echo "=== Cross-Emulator Differential Tests ==="
	$(PYTHON) tools/diff_test.py

diff-test: $(PFILE)
	$(PYTHON) tools/diff_test.py

clean:
	rm -f $(BIN) $(PFILE)
