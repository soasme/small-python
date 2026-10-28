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

.PHONY: all test sanitize bench clean upstream test-cython cython-report cython-dynamic-report install docs oracle test-binding test-spec test-spec-oracle tla-tools test-tla test-tla-oracle tla-coverage libfuzzer
all: spy spyc libspy.a libspy-std.a

spy: $(OBJDIR)/cli.o $(OBJDIR)/spy-std.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

spyc: $(OBJDIR)/spyc.o
	$(CC) $(LDFLAGS) $^ -o $@

libspy.a: $(OBJDIR)/spy.o
	$(AR) rcs $@ $^

# The standard layer (sys, gc, weakref, ...), separate from the core like quickjs-libc.
libspy-std.a: $(OBJDIR)/spy-std.o
	$(AR) rcs $@ $^

$(OBJDIR)/%.o: %.c spy.h
	mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(OBJDIR)/cli.o $(OBJDIR)/spyc.o $(OBJDIR)/run-cython.o: host.h
$(OBJDIR)/spy.o: spy-unicode.h spy-intrinsics.h
$(OBJDIR)/spy-std.o $(OBJDIR)/cli.o $(OBJDIR)/run-cython.o $(OBJDIR)/tests/api.o: spy-std.h
$(OBJDIR)/spy-std.o: spy-std-modules.h

tests/api: $(OBJDIR)/tests/api.o $(OBJDIR)/spy-std.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

bench/lifecycle: $(OBJDIR)/bench/lifecycle.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

run-cython: $(OBJDIR)/run-cython.o $(OBJDIR)/spy-std.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

upstream:
	$(PYTHON) tests/fetch_upstream.py cython cpython

test-cython: run-cython
	$(PYTHON) tests/run_cython.py

cython-report: run-cython
	$(PYTHON) tests/run_cython.py --report-only

cython-dynamic-report: run-cython
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/run_cython.py --dynamic --report tests/results/cython-dynamic.json --report-only

# CPython is an out-of-tree development oracle for validating spec tests and
# TLA replays; it is never linked into the engine or required by a test.
oracle:
	$(PYTHON) tests/fetch_upstream.py cpython
	mkdir -p tests/upstream/cpython-build
	cd tests/upstream/cpython-build && ../cpython/configure --without-ensurepip
	$(MAKE) -C tests/upstream/cpython-build -j4

# Language reference tests (PLS-315) on spy; they need no other implementation.
test-spec: spy
	python3 tests/spec_coverage.py
	python3 tests/spec_runner.py ./spy --strict

# The same tests validated against the pinned CPython oracle as well.
test-spec-oracle: spy
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/spec_runner.py ./spy --strict --oracle $(CPYTHON)

# TLA+ tools 1.7.4 (TLC 2.19), pinned by checksum; TLC needs a Java runtime.
TLA_JAR = $(OBJDIR)/tla/tla2tools.jar
TLA_URL = https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar
TLA_SHA256 = 936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88
JAVA ?= java

tla-tools: $(TLA_JAR)
$(TLA_JAR):
	mkdir -p $(dir $@)
	curl -fsSL -o $@.tmp $(TLA_URL)
	echo "$(TLA_SHA256)  $@.tmp" | shasum -a 256 -c -
	mv $@.tmp $@

test-tla: spy $(TLA_JAR) tla-coverage
	python3 tests/tla_check.py ./spy --java $(JAVA) --jar $(abspath $(TLA_JAR))

# The replays validated against the pinned CPython oracle as well.
test-tla-oracle: spy $(TLA_JAR) tla-coverage
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/tla_check.py ./spy --java $(JAVA) --jar $(abspath $(TLA_JAR)) --oracle $(CPYTHON)

# Every section of docs/standards/3_15.md is mapped to the models covering it
# (tests/tla/coverage.txt) or to a stated exclusion; a TODO entry fails.
tla-coverage:
	python3 tests/tla_coverage.py

install: all
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(PREFIX)/include" "$(DESTDIR)$(PREFIX)/lib" "$(DESTDIR)$(PREFIX)/share/doc/smallpython/standards" "$(DESTDIR)$(PREFIX)/share/doc/smallpython/testing"
	install -m755 spy spyc "$(DESTDIR)$(PREFIX)/bin"
	install -m644 spy.h spy-std.h "$(DESTDIR)$(PREFIX)/include"
	install -m644 libspy.a libspy-std.a "$(DESTDIR)$(PREFIX)/lib"
	install -m644 docs/smallpython.md "$(DESTDIR)$(PREFIX)/share/doc/smallpython"
	install -m644 docs/standards/3_15.md "$(DESTDIR)$(PREFIX)/share/doc/smallpython/standards"
	install -m644 docs/testing/cython.md "$(DESTDIR)$(PREFIX)/share/doc/smallpython/testing"
	install -d "$(DESTDIR)$(PREFIX)/share/doc/smallpython/licenses"
	install -m644 docs/licenses/unicode.txt docs/licenses/python.txt "$(DESTDIR)$(PREFIX)/share/doc/smallpython/licenses"

docs:
	$(PYTHON) tools/check_docs.py

.PHONY: unicode-data check-unicode test-unicode intrinsics check-intrinsics
# The intrinsics header is checked in; regenerate it after editing intrinsics.py.
intrinsics:
	$(PYTHON) tools/build_intrinsics.py

check-intrinsics:
	$(PYTHON) tools/build_intrinsics.py --check

unicode-data:
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tools/build_unicode.py

check-unicode:
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tools/build_unicode.py --check

test-unicode: spy check-unicode
	$(CPYTHON) tests/unicode.py ./spy

test: all tests/api run-cython check-intrinsics
	./tests/api
	python3 tests/spec_coverage.py
	python3 tests/spec_runner.py ./spy --strict
	$(PYTHON) tests/files.py ./spy
	$(PYTHON) tests/executable.py

# The CPython binding (python/, the small-python package) builds with setuptools into .obj/binding.
test-binding:
	cd python && python3 setup.py -q build_ext --build-lib ../$(OBJDIR)/binding --build-temp ../$(OBJDIR)/binding-temp
	cp python/src/small_python/__init__.py python/src/small_python/_core.pyi python/src/small_python/py.typed $(OBJDIR)/binding/small_python/
	PYTHONPATH=$(OBJDIR)/binding python3 -m unittest discover -s python/tests

# libFuzzer targets, as QuickJS's fuzz/: run them as described in fuzz/README.
# Apple clang lacks libFuzzer; on macOS use FUZZ_CC=$$(brew --prefix llvm)/bin/clang.
FUZZ_CC ?= clang
FUZZ_CFLAGS = -O1 -g -std=c11 -I. -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address,undefined
LIB_FUZZING_ENGINE ?= -fsanitize=fuzzer,address,undefined
FUZZ_OBJS = $(OBJDIR)/fuzz/spy.o $(OBJDIR)/fuzz/spy-std.o $(OBJDIR)/fuzz/fuzz_common.o
FUZZERS = fuzz/fuzz_eval fuzz/fuzz_compile

libfuzzer: $(FUZZERS)

$(FUZZERS): fuzz/%: $(OBJDIR)/fuzz/%.o $(FUZZ_OBJS)
	$(FUZZ_CC) $^ $(LIB_FUZZING_ENGINE) $(LDLIBS) -o $@

$(OBJDIR)/fuzz/spy.o $(OBJDIR)/fuzz/spy-std.o: $(OBJDIR)/fuzz/%.o: %.c spy.h spy-std.h spy-unicode.h spy-intrinsics.h spy-std-modules.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(FUZZ_CFLAGS) -c $< -o $@

$(OBJDIR)/fuzz/fuzz_common.o $(OBJDIR)/fuzz/fuzz_eval.o $(OBJDIR)/fuzz/fuzz_compile.o: $(OBJDIR)/fuzz/%.o: fuzz/%.c fuzz/fuzz_common.h spy.h spy-std.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(FUZZ_CFLAGS) -c $< -o $@

bench: bench/lifecycle spy
	./bench/lifecycle
	size spy

sanitize:
	$(MAKE) clean
	# The native recursion guard measures the real stack, which ASan's fake frames hide.
	ASAN_OPTIONS=detect_stack_use_after_return=0 $(MAKE) CFLAGS='-O1 -g -std=c11 -Wall -Wextra -Wpedantic -fsanitize=$(SANITIZERS) -fno-omit-frame-pointer' LDFLAGS='-fsanitize=$(SANITIZERS)' test

clean:
	rm -f spy spyc run-cython *.o *.a tests/*.o tests/api bench/*.o bench/lifecycle $(FUZZERS)
	rm -rf $(OBJDIR)
