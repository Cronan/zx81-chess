# ZX81 1K Chess - Build System
#
# Requires:
#   - pasmo (Z80 assembler)
#   - python3
#
# Targets:
#   make          - Build chess.bin and chess.p
#   make test     - Run the test harness
#   make clean    - Remove built files
#   make all      - Build and test

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
	$(PYTHON) test_harness.py

clean:
	rm -f $(BIN) $(PFILE)
