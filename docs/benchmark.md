# Benchmarks

Engine: 0.1.0 development, commit `982f255`. This report compares wall time
and peak memory of small programs on several Python implementations. It
measures the current engine; it is not a compatibility claim.

## Scope

The programs exercise the **core language only**. None imports a module: no
standard library, no `sys`, no `time`. Every program is something any of the
engines below could run without its library, so the comparison is between
interpreters, not between their standard libraries. Library-heavy workloads
(JSON, regular expressions, I/O) are deliberately absent.

| Program | Exercises |
| --- | --- |
| `startup` | Process launch, engine start, `print`, shutdown |
| `fib` | Recursive calls, small-integer arithmetic (`fib(27)`) |
| `loop` | A `while` loop over module-level integers (3,000,000 iterations) |
| `nbody` | Floating-point arithmetic on nested lists (50,000 steps) |
| `strings` | `join`, `split`, `upper`, `replace`, f-strings, `dict.get` |
| `dicts` | Insertion, membership, lookup and `pop` on 200,000-key dictionaries |
| `sort` | `sorted` on integers, tuples and a `key` function (100,000 items) |
| `classes` | Instance creation, attribute access, method calls |
| `generators` | Generator functions and `yield from` |
| `bigint` | Arbitrary-precision multiplication, division and `str` (1399!) |

The sources are in [`bench/programs`](../bench/programs). Each program prints a
deterministic result.

## Method

```sh
python3 bench/compare.py "CPython 3.15=tests/upstream/cpython-build/python.exe" \
    "spy=./spy" "MicroPython=micropython -X heapsize=512M" ...
```

`bench/compare.py` runs each program as a fresh process: `startup` 30 times,
the others 5 times. It reports the median wall time and the largest peak
resident set size (`ru_maxrss` from `wait4`). The first engine is the
reference. Another engine's run is timed only when its standard output
matches the reference byte for byte. Standard error is discarded. A program
that exits with an error is reported as *error*, one that prints a different
result as *wrong*; neither is timed.

Wall time includes process start, parsing and compilation. For short
programs it is dominated by start-up, which favors small engines.

### Platform

Apple M2, 8 GiB, macOS 26.5.1 arm64. Runs were sequential on an otherwise
idle machine.

### Engines

| Engine | Version | Build | Executable |
| --- | --- | --- | --- |
| spy | commit `982f255` | `make`, Apple Clang 17, `-O2` | 1.8 MB |
| CPython 3.15 | 3.15.0 (the pinned oracle) | `configure --without-ensurepip`, `-O3`, no PGO/LTO | 6.3 MB, plus `Lib/` |
| CPython 3.14 | 3.14.3 | Homebrew bottle | Homebrew framework |
| PyPy | 8.0.1, Python 3.11.17 | Homebrew bottle, JIT | 33 MB `libpypy3.11-c` |
| RustPython | 0.6.1, commit `8c6c94b` | `cargo build --release`, rustc 1.99.1 | 42 MB |
| PocketPy | 2.2.1, commit `d2b7236` | its `build.sh`: `clang -O2 -DNDEBUG` | 0.6 MB |
| Monty | 1.4.0, commit `f3fb8e9` | `cargo build --release -p monty-runtime`, rustc 1.99.1 | 25 MB |
| MicroPython | 1.29.0, unix port | Homebrew bottle, `-X heapsize=512M` | 0.7 MB |

The spy column was measured at `982f255` in a run of `bench/compare.py`
with CPython 3.15 as the reference, which reproduced its earlier figures
within 7 ms (6%). The other engines' columns come from the first run, at
`ea4d579`, on the same machine; their builds have not changed.

MicroPython's default heap cannot hold `dicts` and `sort`, so every program
runs with a 512 MiB heap. That raises its reported memory on programs that
allocate heavily (`nbody`, `strings`).

## Results

### Wall time

Median of the runs; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 2.7 ms | 11.1 ms | 18.9 ms | 17.2 ms | 27.8 ms | 2.9 ms | 4.0 ms | 3.1 ms |
| fib | 94.6 ms | 30.5 ms | 43.6 ms | 27.5 ms | 99.1 ms | 38.7 ms | 65.2 ms | 38.3 ms |
| loop | 445 ms | 395 ms | 370 ms | 25.8 ms | 634 ms | 218 ms | 368 ms | 233 ms |
| nbody | 701 ms | 239 ms | 307 ms | 42.2 ms | 701 ms | 377 ms | 735 ms | 642 ms |
| strings | 339 ms | 114 ms | 114 ms | 52.7 ms | 244 ms | 133 ms | 218 ms | 418 ms |
| dicts | 1.82 s | 92.9 ms | 96.2 ms | 49.3 ms | 171 ms | 72.5 ms | 328 ms | 41.36 s |
| sort | 217 ms | 133 ms | 145 ms | 220 ms | 260 ms | 409 ms | 175 ms | 279 ms |
| classes | 274 ms | 98.4 ms | 99.4 ms | 23.2 ms | 299 ms | 140 ms | 345 ms | 134 ms |
| generators | 310 ms | 112 ms | 121 ms | 40.6 ms | 292 ms | 141 ms | error | 109 ms |
| bigint | 16.9 ms | 12.9 ms | 21.1 ms | 19.3 ms | 29.3 ms | wrong | 4.9 ms | 15.2 ms |

### Peak memory

Largest peak resident set size of the runs, in MiB; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 3.2 | 13.7 | 14.5 | 29.1 | 31.6 | 3.5 | 9.9 | 7.6 |
| fib | 3.4 | 13.5 | 14.6 | 32.3 | 31.9 | 3.5 | 10.1 | 7.6 |
| loop | 3.3 | 13.5 | 14.6 | 31.3 | 31.7 | 3.5 | 10.1 | 7.6 |
| nbody | 3.7 | 14.2 | 15.0 | 32.2 | 32.0 | 14.9 | 10.8 | 434.8 |
| strings | 4.0 | 13.8 | 14.6 | 32.0 | 31.9 | 21.2 | 11.2 | 76.9 |
| dicts | 100.6 | 46.2 | 46.9 | 70.8 | 82.9 | 19.2 | 30.1 | 36.7 |
| sort | 108.1 | 37.1 | 38.3 | 48.4 | 90.3 | 229.2 | 42.2 | 89.5 |
| classes | 3.5 | 13.8 | 14.7 | 32.0 | 31.9 | 30.2 | 10.8 | 25.9 |
| generators | 3.3 | 13.8 | 14.6 | 32.0 | 31.9 | 3.5 | — | 7.6 |
| bigint | 3.7 | 13.6 | 14.6 | 31.7 | 32.0 | — | 11.1 | 8.6 |

### Failures

- **Monty, `generators`**: rejected at parse time with `NotImplementedError`;
  Monty does not implement `yield`.
- **PocketPy, `bigint`**: prints `1 0 0 0`. PocketPy documents its integers as
  signed 64-bit rather than arbitrary precision; the factorial overflows.

## Reading the results

**Start-up and memory.** spy starts a process, runs `print` and exits in
2.8 ms, the fastest of the eight, and stays under 4 MiB for every program
that does not build large containers. PocketPy and MicroPython, the other
two engines built for embedding, are close behind. On `dicts` and `sort`
spy uses more memory than CPython: every spy value has the same size,
216 bytes on this build, large enough for its biggest kind (a dictionary,
class or instance), so 100,000 integers cost about 21 MiB.

**Throughput.** spy is 1.1 to 3.1 times slower than CPython 3.15 on the
interpreter-bound programs, and 20 times slower on `dicts`. spy has no
bytecode compiler. Ordinary code is evaluated by walking the syntax tree
(`eval` in `spy.c`); suspendable bodies run on an instruction list that
still points into the tree. Syntax nodes cache what can be reused between
evaluations: a literal's value, a name's hash and the entry it was last
found in, and how a class's instances answer an attribute read, an
assignment or a method call.

- `loop` (1.1 times), `bigint` (1.3 times) and `sort` (1.6 times) are
  closest. `loop` does a few operations per iteration on small integers;
  `bigint` and most of `sort` run in C.
- `classes`, `generators`, `nbody`, `strings` and `fib` (2.8 to 3.1
  times) spend their time across the evaluator rather than in one
  operation. Profiles show no single dominant cost.
- `dicts` pops 100,000 keys from a 205,000-key dictionary. Lookups use a
  hash index, but entries stay in one dense array, so a removal shifts the
  entries on its nearer side: most of its 1.82 seconds. The same program
  without the removals runs in 0.15 s.

These are implementation gaps, not language choices. MicroPython's 41 s on
`dicts` comes from its own implementation and was not investigated.

## Embedding lifecycle

`make bench` measures the embedding path without a process: it creates a
context, executes `print('Hello, world!')` with output discarded, and frees
the context, 20,000 times. On the build above it reports **257 µs of CPU time
per lifecycle** (three runs: 255.62, 256.63, 260.05 µs). The Mach-O `__TEXT`
segment of `spy` is 1,638,400 bytes.

## Reproducing

The comparison engines are not dependencies of this repository. On macOS:

```sh
brew install pypy3.11 micropython
git clone https://github.com/pocketpy/pocketpy
(cd pocketpy && python3 prebuild.py &&
 clang -std=c11 -O2 -Iinclude -DNDEBUG -o main $(find src -name '*.c') src2/main.c -lm)
git clone https://github.com/RustPython/RustPython
(cd RustPython && cargo build --release)
git clone https://github.com/pydantic/monty
(cd monty && cargo build --release -p monty-runtime)
```

RustPython and Monty need a recent Rust toolchain (1.99 was used). Then pass
every engine to `bench/compare.py` as `NAME=COMMAND`, the reference first.
The script prints the combined table that the two tables above were split
from.
