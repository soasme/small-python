CC = cc
AR = ar
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic
LDLIBS = -lm
PYTHON = python3
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

.PHONY: all test sanitize bench clean upstream test-cython cython-report install docs standard check-standard
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

$(OBJDIR)/cli.o $(OBJDIR)/spyc.o: host.h

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

install: all
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(PREFIX)/include" "$(DESTDIR)$(PREFIX)/lib" "$(DESTDIR)$(PREFIX)/share/doc/slimpy/standards" "$(DESTDIR)$(PREFIX)/share/doc/slimpy/testing"
	install -m755 spy spyc "$(DESTDIR)$(PREFIX)/bin"
	install -m644 spy.h "$(DESTDIR)$(PREFIX)/include"
	install -m644 libspy.a "$(DESTDIR)$(PREFIX)/lib"
	install -m644 docs/slimpy.md "$(DESTDIR)$(PREFIX)/share/doc/slimpy"
	install -m644 docs/standards/3_15.md "$(DESTDIR)$(PREFIX)/share/doc/slimpy/standards"
	install -m644 docs/testing/cython.md "$(DESTDIR)$(PREFIX)/share/doc/slimpy/testing"

docs:
	$(PYTHON) tools/check_docs.py

standard:
	uv run --no-project --with pypandoc-binary==1.17 --with Pygments==2.19.2 python tools/build_standard.py

check-standard:
	uv run --no-project --with pypandoc-binary==1.17 --with Pygments==2.19.2 python tools/build_standard.py --check

test: all tests/api
	./tests/api
	$(PYTHON) tests/conformance.py ./spy
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
