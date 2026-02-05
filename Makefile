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

.PHONY: all build test clean

all: build test

build: $(PFILE)

$(BIN): $(SRC)
	$(ASM) --bin $(SRC) $(BIN)
	@echo "Assembled: $$(wc -c < $(BIN)) bytes"

$(PFILE): $(BIN) tools/make_p_file.py
	$(PYTHON) tools/make_p_file.py $(BIN) $(PFILE)

test: $(BIN)
	@echo "=== Basic Tests ==="
	$(PYTHON) test_harness.py
	@echo ""
	@echo "=== Comprehensive Test Suite ==="
	$(PYTHON) tests/test_chess.py

clean:
	rm -f $(BIN) $(PFILE)
