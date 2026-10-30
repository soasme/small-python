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

.PHONY: all test sanitize bench clean upstream test-cython cython-report cython-dynamic-report install docs oracle test-binding test-javascript wasm test-spec test-spec-oracle test-build test-build-oracle tla-tools test-tla test-tla-oracle tla-coverage libfuzzer fuzz fuzz-replay coverage test-rust rust-vendor
all: spy spyc spy-worker libspy.a libspy-std.a

spy: $(OBJDIR)/cli.o $(OBJDIR)/spy-std.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

# The packages' worker (docs/packaging/protocol.md): spy-worker.c compiled
# once as the engine with counted allocations, once as the worker.
spy-worker: $(OBJDIR)/spy-worker.o $(OBJDIR)/spy-worker-engine.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

$(OBJDIR)/spy-worker.o: spy-worker.c spy.h spy-std.h
	mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(OBJDIR)/spy-worker-engine.o: spy-worker.c spy.c spy.h spy-std.c spy-std.h spy-std-modules.h spy-unicode.h spy-intrinsics.h
	mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -DSPY_WORKER_ENGINE -c $< -o $@

# The JavaScript package's worker: the same file for wasm32-wasip1, built
# with wasi-sdk (https://github.com/WebAssembly/wasi-sdk).
WASI_SDK ?= /opt/wasi-sdk
WASM_CC = $(WASI_SDK)/bin/clang --target=wasm32-wasip1 --sysroot=$(WASI_SDK)/share/wasi-sysroot
WASM_CFLAGS = -O2 -std=c11 -Wall -Wextra -Wno-tautological-constant-out-of-range-compare -Wno-unused-function
WASM_LDFLAGS = -Wl,--import-memory -Wl,--initial-memory=16777216 -Wl,-z,stack-size=8388608
javascript/spy-worker.wasm: spy-worker.c spy.c spy.h spy-std.c spy-std.h spy-std-modules.h spy-unicode.h spy-intrinsics.h
	mkdir -p $(OBJDIR)/wasm
	$(WASM_CC) $(WASM_CFLAGS) -DSPY_WORKER_ENGINE -c spy-worker.c -o $(OBJDIR)/wasm/engine.o
	$(WASM_CC) $(WASM_CFLAGS) -c spy-worker.c -o $(OBJDIR)/wasm/worker.o
	$(WASM_CC) $(WASM_LDFLAGS) $(OBJDIR)/wasm/engine.o $(OBJDIR)/wasm/worker.o -lm -o $@
	mkdir -p javascript/licenses
	cp LICENSE javascript/LICENSE
	cp docs/licenses/python.txt docs/licenses/unicode.txt docs/licenses/quickjs.txt javascript/licenses/

wasm: javascript/spy-worker.wasm

test-javascript: javascript/spy-worker.wasm
	cd javascript && node --test test/*.test.js

# spyc parses with the engine itself, as qjsc compiles with quickjs.c.
spyc: $(OBJDIR)/spyc.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

libspy.a: $(OBJDIR)/spy.o
	$(AR) rcs $@ $^

# The standard layer (sys and gc), separate from the core like quickjs-libc.
libspy-std.a: $(OBJDIR)/spy-std.o
	$(AR) rcs $@ $^

$(OBJDIR)/%.o: %.c spy.h
	mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(OBJDIR)/cli.o $(OBJDIR)/spyc.o $(OBJDIR)/run-cython.o $(OBJDIR)/tests/run-spec.o: host.h
$(OBJDIR)/spy.o $(OBJDIR)/spyc.o $(OBJDIR)/tests/oom.o: spy-unicode.h spy-intrinsics.h
$(OBJDIR)/spyc.o $(OBJDIR)/tests/oom.o: spy.c
$(OBJDIR)/spy-std.o $(OBJDIR)/cli.o $(OBJDIR)/run-cython.o $(OBJDIR)/tests/api.o $(OBJDIR)/tests/threads.o: spy-std.h
$(OBJDIR)/spy-std.o: spy-std-modules.h

tests/api: $(OBJDIR)/tests/api.o $(OBJDIR)/spy-std.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

# The conformance driver: the bare core, without the standard layer.
tests/run-spec: $(OBJDIR)/tests/run-spec.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

# Contexts on several threads at once, sharing nothing.
tests/threads: $(OBJDIR)/tests/threads.o $(OBJDIR)/spy-std.o $(OBJDIR)/spy.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -pthread -o $@

# Allocation failure: the engine compiled in, with a failing allocator.
tests/oom: $(OBJDIR)/tests/oom.o
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

# Language reference tests (PLS-315) on the bare core; they need no other implementation.
test-spec: tests/run-spec
	python3 tests/spec_coverage.py
	python3 tests/spec_runner.py tests/run-spec --strict

# The same tests validated against the pinned CPython oracle as well.
test-spec-oracle: tests/run-spec
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/spec_runner.py tests/run-spec --strict --oracle $(CPYTHON)

# The bundler tests (docs/build.md 10.2). The bundler is not written yet, so
# these fail. test-build-oracle also runs each test unbundled on the pinned
# CPython; tests/build_runner.py --oracle-only runs that phase alone.
test-build: spyc libspy.a libspy-std.a
	LDFLAGS='$(LDFLAGS)' python3 tests/build_runner.py ./spyc

test-build-oracle: spyc libspy.a libspy-std.a
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/build_runner.py ./spyc --oracle $(CPYTHON)

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

test-tla: tests/run-spec $(TLA_JAR) tla-coverage
	python3 tests/tla_check.py tests/run-spec --java $(JAVA) --jar $(abspath $(TLA_JAR))

# The replays validated against the pinned CPython oracle as well.
test-tla-oracle: tests/run-spec $(TLA_JAR) tla-coverage
	$(if $(CPYTHON),$(CPYTHON),$(error Missing pinned CPython oracle; run make oracle)) tests/tla_check.py tests/run-spec --java $(JAVA) --jar $(abspath $(TLA_JAR)) --oracle $(CPYTHON)

# Every section of docs/standards/3_15.md is mapped to the models covering it
# (tests/tla/coverage.txt) or to a stated exclusion; a TODO entry fails.
tla-coverage:
	python3 tests/tla_coverage.py

install: all
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(PREFIX)/include" "$(DESTDIR)$(PREFIX)/lib" "$(DESTDIR)$(PREFIX)/share/doc/smallpython/standards" "$(DESTDIR)$(PREFIX)/share/doc/smallpython/testing"
	install -m755 spy spyc "$(DESTDIR)$(PREFIX)/bin"
	install -m644 spy.h spy-std.h "$(DESTDIR)$(PREFIX)/include"
	install -m644 libspy.a libspy-std.a "$(DESTDIR)$(PREFIX)/lib"
	install -m644 docs/manual.md "$(DESTDIR)$(PREFIX)/share/doc/smallpython"
	install -m644 docs/standards/3_15.md "$(DESTDIR)$(PREFIX)/share/doc/smallpython/standards"
	install -m644 docs/testing/cython.md "$(DESTDIR)$(PREFIX)/share/doc/smallpython/testing"
	install -d "$(DESTDIR)$(PREFIX)/share/doc/smallpython/licenses"
	install -m644 docs/licenses/unicode.txt docs/licenses/python.txt docs/licenses/quickjs.txt "$(DESTDIR)$(PREFIX)/share/doc/smallpython/licenses"

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

test: all tests/api tests/oom tests/threads tests/run-spec run-cython check-intrinsics
	./tests/api
	./tests/oom
	./tests/threads
	python3 tests/spec_coverage.py
	python3 tests/spec_runner.py tests/run-spec --strict
	$(PYTHON) tests/files.py ./spy
	$(PYTHON) tests/std.py ./spy
	CFLAGS='$(CFLAGS)' LDFLAGS='$(LDFLAGS)' $(PYTHON) tests/executable.py
	LDFLAGS='$(LDFLAGS)' python3 tests/build_runner.py ./spyc

# The CPython binding (python/, the small-python package) builds with setuptools into .obj/binding.
test-binding: spy-worker
	mkdir -p $(OBJDIR)/binding
	cp -R python/src/small_python $(OBJDIR)/binding/
	cp spy-worker $(OBJDIR)/binding/small_python/
	PYTHONPATH=$(OBJDIR)/binding python3 -m unittest discover -s python/tests

# The Rust crates (rust/, docs/packaging/rust.md) compile the engine with cc themselves.
test-rust:
	cd rust && cargo test --workspace --all-features
	cd examples/todo && cargo test  # against small-python from crates.io

# A published small-python-src carries the sources and licenses in csrc/.
RUST_CSRC = rust/small-python-src/csrc
rust-vendor:
	mkdir -p $(RUST_CSRC)/licenses
	cp spy.c spy.h spy-std.c spy-std.h spy-std-modules.h spy-intrinsics.h spy-unicode.h spy-worker.c $(RUST_CSRC)/
	cp LICENSE docs/licenses/python.txt docs/licenses/unicode.txt $(RUST_CSRC)/licenses/

# libFuzzer targets, as QuickJS's fuzz/: run them as described in fuzz/README.
# Apple clang lacks libFuzzer; on macOS use FUZZ_CC=$$(brew --prefix llvm)/bin/clang.
FUZZ_CC ?= clang
FUZZ_CFLAGS = -O1 -g -std=c11 -I. -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address,undefined -fno-sanitize-recover=all
LIB_FUZZING_ENGINE ?= -fsanitize=fuzzer,address,undefined
FUZZ_OBJS = $(OBJDIR)/fuzz/spy.o $(OBJDIR)/fuzz/spy-std.o $(OBJDIR)/fuzz/fuzz_common.o
FUZZERS = fuzz/fuzz_eval fuzz/fuzz_compile fuzz/fuzz_spyc fuzz/fuzz_oom

libfuzzer: $(FUZZERS)

# Each fuzzer for FUZZ_SECONDS, seeded from the examples and language tests.
# The engine has no memory limit, so out-of-memory and slow inputs are not
# findings; any sanitizer report or crash is.
FUZZ_SECONDS ?= 60
FUZZ_CORPUS = $(OBJDIR)/fuzz/corpus
fuzz: $(FUZZERS)
	mkdir -p $(FUZZ_CORPUS)
	for f in examples/*.py tests/spec/*/*.py; do cp $$f $(FUZZ_CORPUS)/$$(echo $$f | tr / _); done
	for fuzzer in $(FUZZERS); do \
		./$$fuzzer -dict=fuzz/fuzz.dict -fork=2 -ignore_ooms=1 -ignore_timeouts=1 -timeout=10 -rss_limit_mb=2048 \
			-max_total_time=$(FUZZ_SECONDS) -artifact_prefix=$(OBJDIR)/fuzz/ $(FUZZ_CORPUS) || exit 1; \
	done

fuzz/fuzz_eval fuzz/fuzz_compile: fuzz/%: $(OBJDIR)/fuzz/%.o $(FUZZ_OBJS)
	$(FUZZ_CC) $^ $(LIB_FUZZING_ENGINE) $(LDLIBS) -o $@

# spyc and tests/oom include the engine, so their fuzzers do too.
fuzz/fuzz_spyc: fuzz/fuzz_spyc.c spyc.c host.h spy.c spy.h spy-unicode.h spy-intrinsics.h
	$(FUZZ_CC) $(FUZZ_CFLAGS) $< $(LIB_FUZZING_ENGINE) $(LDLIBS) -o $@

fuzz/fuzz_oom: fuzz/fuzz_oom.c tests/oom.c spy.c spy.h spy-unicode.h spy-intrinsics.h
	$(FUZZ_CC) $(FUZZ_CFLAGS) $< $(LIB_FUZZING_ENGINE) $(LDLIBS) -o $@


# The corpus make fuzz built, run once more by fuzz/replay.c under
# REPLAY_SANITIZERS: by default MemorySanitizer, which libFuzzer is not built
# with, for reads of uninitialized memory on every input the fuzzers kept.
REPLAY_SANITIZERS ?= memory
REPLAY_DIR = $(OBJDIR)/replay-$(REPLAY_SANITIZERS)
REPLAY_CFLAGS = -O1 -g -std=c11 -I. -fsanitize=$(REPLAY_SANITIZERS) -fno-sanitize-recover=all -fno-omit-frame-pointer
REPLAYS = $(REPLAY_DIR)/fuzz_eval $(REPLAY_DIR)/fuzz_compile $(REPLAY_DIR)/fuzz_spyc $(REPLAY_DIR)/fuzz_oom
fuzz-replay: $(REPLAYS)
	test -d $(FUZZ_CORPUS) || { echo "no corpus in $(FUZZ_CORPUS); run make fuzz"; exit 1; }
	for replay in $(REPLAYS); do find $(FUZZ_CORPUS) -type f -exec $$replay {} + || exit 1; done

$(REPLAY_DIR)/fuzz_eval $(REPLAY_DIR)/fuzz_compile: $(REPLAY_DIR)/%: fuzz/%.c fuzz/replay.c fuzz/fuzz_common.c fuzz/fuzz_common.h spy.c spy.h spy-std.c spy-std.h spy-unicode.h spy-intrinsics.h spy-std-modules.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(REPLAY_CFLAGS) fuzz/replay.c $< fuzz/fuzz_common.c spy.c spy-std.c $(LDLIBS) -o $@

$(REPLAY_DIR)/fuzz_spyc: fuzz/fuzz_spyc.c fuzz/replay.c spyc.c host.h spy.c spy.h spy-unicode.h spy-intrinsics.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(REPLAY_CFLAGS) fuzz/replay.c $< $(LDLIBS) -o $@

$(REPLAY_DIR)/fuzz_oom: fuzz/fuzz_oom.c fuzz/replay.c tests/oom.c spy.c spy.h spy-unicode.h spy-intrinsics.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(REPLAY_CFLAGS) fuzz/replay.c $< $(LDLIBS) -o $@

$(OBJDIR)/fuzz/spy.o $(OBJDIR)/fuzz/spy-std.o: $(OBJDIR)/fuzz/%.o: %.c spy.h spy-std.h spy-unicode.h spy-intrinsics.h spy-std-modules.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(FUZZ_CFLAGS) -c $< -o $@

$(OBJDIR)/fuzz/fuzz_common.o $(OBJDIR)/fuzz/fuzz_eval.o $(OBJDIR)/fuzz/fuzz_compile.o: $(OBJDIR)/fuzz/%.o: fuzz/%.c fuzz/fuzz_common.h spy.h spy-std.h
	mkdir -p $(dir $@)
	$(FUZZ_CC) $(FUZZ_CFLAGS) -c $< -o $@

bench: bench/lifecycle spy
	./bench/lifecycle
	size spy

# Every test, the packages' worker and generated programs included, under
# SANITIZERS: AddressSanitizer with leak checking and UndefinedBehaviorSanitizer
# by default, or SANITIZERS=memory with clang for reads of uninitialized
# memory. No report is recoverable, and every report lands in one file
# (tests/sanitize.c), which must stay empty.
SANITIZE_CFLAGS = -O1 -g -std=c11 -Wall -Wextra -Wpedantic -fsanitize=$(SANITIZERS) -fno-sanitize-recover=all -fno-omit-frame-pointer
SANITIZE_DIR = $(abspath $(OBJDIR))/sanitize
sanitize:
	$(MAKE) clean
	mkdir -p $(SANITIZE_DIR)
	$(CC) $(SANITIZE_CFLAGS) -DREPORT='"$(SANITIZE_DIR)/report"' -c tests/sanitize.c -o $(SANITIZE_DIR)/sanitize.o
	SPY_TEST_TIMEOUT=600 $(MAKE) CFLAGS='$(SANITIZE_CFLAGS)' LDFLAGS='-fsanitize=$(SANITIZERS) $(SANITIZE_DIR)/sanitize.o' test test-binding; \
	status=$$?; if [ -s $(SANITIZE_DIR)/report ]; then cat $(SANITIZE_DIR)/report; exit 1; fi; exit $$status

# Line and branch coverage of make test and the package tests, with clang:
# code no test executes is code no sanitizer run has checked. The profile
# path is compiled in, since the test runners clear the environment, and
# mapped at startup (%c), before the worker's sandbox forbids opening it.
COVERAGE_DIR = $(abspath $(OBJDIR))/coverage
COVERAGE_PROFILE = -fprofile-instr-generate=$(COVERAGE_DIR)/%c%4m.profraw
LLVM_PROFDATA ?= llvm-profdata
LLVM_COV ?= llvm-cov
coverage:
	$(MAKE) clean
	mkdir -p $(COVERAGE_DIR)
	$(MAKE) CC=clang CFLAGS='-O1 -g -std=c11 $(COVERAGE_PROFILE) -fcoverage-mapping -mllvm -runtime-counter-relocation' \
		LDFLAGS='$(COVERAGE_PROFILE)' test test-binding
	$(LLVM_PROFDATA) merge -o $(COVERAGE_DIR)/all.profdata $(COVERAGE_DIR)/*.profraw
	$(LLVM_COV) report -instr-profile=$(COVERAGE_DIR)/all.profdata ./spy -object ./spyc -object ./tests/run-spec \
		-object ./tests/api -object ./tests/oom -object ./spy-worker spy.c spyc.c spy-std.c cli.c spy-worker.c
	$(LLVM_COV) show -format=html -output-dir=$(COVERAGE_DIR)/html -instr-profile=$(COVERAGE_DIR)/all.profdata ./spy \
		-object ./spyc -object ./tests/run-spec -object ./tests/api -object ./tests/oom -object ./spy-worker spy.c spyc.c spy-std.c cli.c spy-worker.c
	@echo "Annotated sources: $(COVERAGE_DIR)/html/index.html"

clean:
	rm -f spy spyc spy-worker run-cython *.o *.a tests/*.o tests/api tests/oom tests/threads tests/run-spec bench/*.o bench/lifecycle $(FUZZERS)
	rm -rf $(OBJDIR)
