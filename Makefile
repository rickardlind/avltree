TESTS     ?=
HEIGHTS   ?= 5-20
TRIES     ?= 5
SEED      ?=
REPORTS   ?= fill insert delete
OUTPUT    ?= .
UNIT      ?= us

.PHONY: help tests extension tables clean distclean

help:
	@echo "Targets:"
	@echo "  make tests     - Run tests"
	@echo "  make extension - Build C extension"
	@echo "  make tables    - Print tables from test output"
	@echo "  make graphs    - Create SVG graphs test output"
	@echo "  make clean     - Remove temporary files"
	@echo "  make distclean - Remove all output"
	@echo ""
	@echo "Variables:"
	@echo "  TESTS          - Specify tests to run (default: all)"
	@echo "  HEIGHTS        - List or range of tree heights to test (default: $(HEIGHTS))"
	@echo "  TRIES          - Number of tries per count (default: $(TRIES))"
	@echo "  SEED           - Random number generator seed (default: none)"
	@echo "  REPORTS        - List of reports for tables and graphs targets (default: $(REPORTS))"


tests: extension
	@mkdir -p $(OUTPUT)
	HEIGHTS=$(HEIGHTS) TRIES=$(TRIES) SEED=$(SEED) OUTPUT=$(OUTPUT) ./tests.py $(TESTS)

extension: cavltree.so

tables: $(REPORTS:%=$(OUTPUT)/%.json)
	@for f in $+; do \
		./stats.py --result $$f --type table --unit $(UNIT); \
	done

graphs: $(REPORTS:%=$(OUTPUT)/%.svg)

clean:
	@rm -rf *.o *.so __pycache__

distclean: clean
	@rm -f $(OUTPUT)/*.json $(OUTPUT)/*.svg
	@rmdir -p $(OUTPUT) 2>/dev/null || true

cavltree.so: cavltree.c
	python3 setup.py build_ext
	mv cavltree.*.so $@

$(OUTPUT)/%.svg: $(OUTPUT)/%.json
	./stats.py --result $< --output $@ --type graph --unit $(UNIT)
