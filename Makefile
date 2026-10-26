CC = cc
AR = ar
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic
LDLIBS = -lm
CPYTHON = $(firstword $(wildcard tests/upstream/cpython-build/python.exe tests/upstream/cpython-build/python))
PYTHON = $(if $(CPYTHON),$(CPYTHON),python3)
SANITIZERS = address,undefined
PREFIX ?= /usr/local
DESTDIR ?=
OBJDIR = .obj

# Optional development/build settings, following the QuickJS Makefile style.
# CONFIG_LTO=y
# CONFIG_WERROR=y
ifdef CONFIG_LTO
CFLAGS += -flto
LDFLAGS += -flto
endif
ifdef CONFIG_WERROR
CFLAGS += -Werror
endif

.PHONY: all test sanitize bench clean upstream test-cython cython-report cython-dynamic-report install docs standard check-standard oracle test-cpython test-cpython-doctests cpython-report cpython-discover test-cpython-unittest cpython-unittest-report test-templates
all: spy spyc libspy.a

spy: $(OBJDIR)/cli.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

spyc: $(OBJDIR)/spyc.o
	$(CC) $(LDFLAGS) $^ -o $@

libspy.a: $(OBJDIR)/spy.o
	$(AR) rcs $@ $^

$(OBJDIR)/%.o: %.c spy.h
	mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(OBJDIR)/cli.o $(OBJDIR)/spyc.o $(OBJDIR)/run-cython.o: host.h
$(OBJDIR)/spy.o: spy-unicode.h spy-intrinsics.h

tests/api: $(OBJDIR)/tests/api.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

bench/lifecycle: $(OBJDIR)/bench/lifecycle.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

run-cython: $(OBJDIR)/run-cython.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

upstream:
	$(PYTHON) tests/fetch_upstream.py cython cpython

test-cython: run-cython
	$(PYTHON) tests/run_cython.py

cython-report: run-cython
	$(PYTHON) tests/run_cython.py --report-only

cython-dynamic-report: run-cython
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/run_cython.py --dynamic --report tests/results/cython-dynamic.json --report-only

# CPython is an out-of-tree development oracle, never linked into the engine.
oracle:
	$(PYTHON) tests/fetch_upstream.py cpython
	mkdir -p tests/upstream/cpython-build
	cd tests/upstream/cpython-build && ../cpython/configure --without-ensurepip
	$(MAKE) -C tests/upstream/cpython-build -j4

test-cpython-doctests: run-cython
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/cpython.py doctests

test-cpython-unittest: run-cython
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/cpython.py unittest

cpython-unittest-report: run-cython
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/cpython.py unittest --report-only

test-cpython: test-cpython-doctests test-cpython-unittest
	$(CPYTHON) tests/cpython.py discover

cpython-report: run-cython
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/cpython.py doctests --report-only

cpython-discover:
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/cpython.py discover --report-only

install: all
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(PREFIX)/include" "$(DESTDIR)$(PREFIX)/lib" "$(DESTDIR)$(PREFIX)/share/doc/slimpy/standards" "$(DESTDIR)$(PREFIX)/share/doc/slimpy/testing"
	install -m755 spy spyc "$(DESTDIR)$(PREFIX)/bin"
	install -m644 spy.h "$(DESTDIR)$(PREFIX)/include"
	install -m644 libspy.a "$(DESTDIR)$(PREFIX)/lib"
	install -m644 docs/slimpy.md "$(DESTDIR)$(PREFIX)/share/doc/slimpy"
	install -m644 docs/standards/3_15.md "$(DESTDIR)$(PREFIX)/share/doc/slimpy/standards"
	install -m644 docs/testing/cython.md docs/testing/cpython.md "$(DESTDIR)$(PREFIX)/share/doc/slimpy/testing"
	install -d "$(DESTDIR)$(PREFIX)/share/doc/slimpy/licenses"
	install -m644 docs/licenses/unicode.txt docs/licenses/python.txt "$(DESTDIR)$(PREFIX)/share/doc/slimpy/licenses"

docs:
	$(PYTHON) tools/check_docs.py

standard:
	uv run --no-project --with pypandoc-binary==1.17 --with Pygments==2.19.2 python tools/build_standard.py

check-standard:
	uv run --no-project --with pypandoc-binary==1.17 --with Pygments==2.19.2 python tools/build_standard.py --check

.PHONY: unicode-data check-unicode test-unicode test-async test-stringsearch intrinsics check-intrinsics
# The intrinsics header is checked in; regenerate it after editing intrinsics.py.
intrinsics:
	$(PYTHON) tools/build_intrinsics.py

check-intrinsics:
	$(PYTHON) tools/build_intrinsics.py --check

test-stringsearch: spy
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/stringsearch.py ./spy

test-async: spy
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/async.py ./spy

test-templates: spy
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/templates.py ./spy

unicode-data:
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tools/build_unicode.py

check-unicode:
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tools/build_unicode.py --check

test-unicode: spy check-unicode
	$(CPYTHON) tests/unicode.py ./spy
	$(CPYTHON) tests/identifiers.py ./spy

test: all tests/api run-cython check-intrinsics
	./tests/api
	$(PYTHON) tests/conformance.py ./spy
	$(PYTHON) tests/numbers.py ./spy
	$(PYTHON) tests/ranges.py ./spy
	$(PYTHON) tests/comparisons.py ./spy
	$(PYTHON) tests/arguments.py ./spy
	$(PYTHON) tests/construction.py ./spy
	$(PYTHON) tests/classcreation.py ./spy
	$(PYTHON) tests/hashing.py ./spy
	$(PYTHON) tests/mappingproxy.py ./spy
	$(PYTHON) tests/generator_metadata.py ./spy
	$(PYTHON) tests/rounding.py ./spy
	$(PYTHON) tests/strings.py ./spy
	$(PYTHON) tests/framework.py ./run-cython
	$(PYTHON) tests/executable.py

bench: bench/lifecycle spy
	./bench/lifecycle
	size spy

sanitize:
	$(MAKE) clean
	$(MAKE) CFLAGS='-O1 -g -std=c11 -Wall -Wextra -Wpedantic -fsanitize=$(SANITIZERS) -fno-omit-frame-pointer' LDFLAGS='-fsanitize=$(SANITIZERS)' test

clean:
	rm -f spy spyc run-cython *.o *.a tests/*.o tests/api bench/*.o bench/lifecycle
	rm -rf $(OBJDIR)
