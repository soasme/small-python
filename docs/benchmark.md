# Benchmarks

Engine: 0.4.0. This report compares wall time
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
| spy | 0.4.0 | `make`, Apple Clang 17, `-O2` | 1.5 MB |
| CPython 3.15 | 3.15.0 (the pinned oracle) | `configure --without-ensurepip`, `-O3`, no PGO/LTO | 6.3 MB, plus `Lib/` |
| CPython 3.14 | 3.14.3 | Homebrew bottle | Homebrew framework |
| PyPy | 8.0.1, Python 3.11.17 | Homebrew bottle, JIT | 33 MB `libpypy3.11-c` |
| RustPython | 0.6.1, commit `8c6c94b` | `cargo build --release`, rustc 1.99.1 | 42 MB |
| PocketPy | 2.2.1, commit `d2b7236` | its `build.sh`: `clang -O2 -DNDEBUG` | 0.6 MB |
| Monty | 1.4.0, commit `f3fb8e9` | `cargo build --release -p monty-runtime`, rustc 1.99.1 | 25 MB |
| MicroPython | 1.29.0, unix port | Homebrew bottle, `-X heapsize=512M` | 0.7 MB |

The spy, CPython, PyPy and MicroPython columns were measured at 0.4.0 in
one run of `bench/compare.py` with CPython 3.15 as the reference; an
earlier run of spy and CPython 3.15 on the same tree agreed within 2.4%.
PocketPy, RustPython and Monty were not rebuilt for this release; their
columns come from the run at `ea4d579` on the same machine, when CPython
3.15's medians were within 4% of the column below.

MicroPython's default heap cannot hold `dicts` and `sort`, so every program
runs with a 512 MiB heap. That raises its reported memory on programs that
allocate heavily (`nbody`, `strings`).

## Results

### Wall time

Median of the runs; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 2.6 ms | 10.9 ms | 18.7 ms | 16.9 ms | 27.8 ms | 2.9 ms | 4.0 ms | 3.0 ms |
| fib | 34.5 ms | 30.5 ms | 42.8 ms | 27.3 ms | 99.1 ms | 38.7 ms | 65.2 ms | 37.8 ms |
| loop | 159 ms | 395 ms | 380 ms | 25.7 ms | 634 ms | 218 ms | 368 ms | 228 ms |
| nbody | 239 ms | 236 ms | 307 ms | 42.7 ms | 701 ms | 377 ms | 735 ms | 640 ms |
| strings | 125 ms | 112 ms | 114 ms | 51.7 ms | 244 ms | 133 ms | 218 ms | 427 ms |
| dicts | 69.5 ms | 92.0 ms | 96.4 ms | 49.2 ms | 171 ms | 72.5 ms | 328 ms | 41.44 s |
| sort | 134 ms | 131 ms | 143 ms | 218 ms | 260 ms | 409 ms | 175 ms | 279 ms |
| classes | 94.2 ms | 99.8 ms | 116 ms | 24.1 ms | 299 ms | 140 ms | 345 ms | 136 ms |
| generators | 111 ms | 111 ms | 121 ms | 39.6 ms | 292 ms | 141 ms | error | 108 ms |
| bigint | 6.7 ms | 12.4 ms | 20.0 ms | 19.1 ms | 29.3 ms | wrong | 4.9 ms | 14.5 ms |

### Peak memory

Largest peak resident set size of the runs, in MiB; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 2.9 | 13.7 | 14.6 | 29.1 | 31.6 | 3.5 | 9.9 | 7.6 |
| fib | 3.0 | 13.7 | 14.5 | 32.3 | 31.9 | 3.5 | 10.1 | 7.6 |
| loop | 2.9 | 13.5 | 14.6 | 31.3 | 31.7 | 3.5 | 10.1 | 7.6 |
| nbody | 3.4 | 14.0 | 15.0 | 32.2 | 32.0 | 14.9 | 10.8 | 434.8 |
| strings | 3.2 | 13.8 | 14.7 | 32.0 | 31.9 | 21.2 | 11.2 | 76.9 |
| dicts | 47.6 | 46.2 | 46.9 | 70.8 | 82.9 | 19.2 | 30.1 | 36.7 |
| sort | 80.5 | 37.3 | 38.2 | 48.3 | 90.3 | 229.2 | 42.2 | 89.5 |
| classes | 3.1 | 13.8 | 14.7 | 32.0 | 31.9 | 30.2 | 10.8 | 25.9 |
| generators | 3.0 | 13.8 | 14.6 | 32.0 | 31.9 | 3.5 | — | 7.6 |
| bigint | 3.3 | 13.8 | 14.6 | 31.7 | 32.0 | — | 11.1 | 8.6 |

### Failures

- **Monty, `generators`**: rejected at parse time with `NotImplementedError`;
  Monty does not implement `yield`.
- **PocketPy, `bigint`**: prints `1 0 0 0`. PocketPy documents its integers as
  signed 64-bit rather than arbitrary precision; the factorial overflows.

## Reading the results

**Start-up and memory.** spy starts a process, runs `print` and exits in
2.6 ms and stays under 4 MiB for every program that does not build large
containers. PocketPy and MicroPython, the other two engines built for
embedding, start in about the same time. On `sort` spy uses about twice
CPython's memory and on `dicts` about the same. Values are carved from
16 KiB pools in three sizes: 96 bytes for a number, 112 for a string or
bytes with room for 16 bytes of text, and 208 for every other kind (a
container, class or instance), so 100,000 integers cost about 9 MiB.

**Throughput.** In the same run, spy was faster than CPython 3.15 on
`loop` (0.40 times its time), `bigint` (0.54), `dicts` (0.76) and
`classes` (0.94), the same on `generators`, within 3% on `nbody` and
`sort`, and 12 to 13% slower on `strings` and `fib`. spy has no
bytecode compiler and no JIT. Ordinary code is evaluated by walking the
syntax tree (`eval` in `spy.c`); suspendable bodies run on an instruction
list that still points into the tree. Syntax nodes cache what can be
reused between evaluations: a literal's value, a name's hash and the entry
it was last found in, whether an operator's operands can be read without
evaluation, and how a class's instances answer an attribute read, an
assignment or a method call. [optimization.md](optimization.md) records
each change behind these numbers.

- `loop` and `bigint` run in about half CPython's time, `dicts` in three
  quarters. `loop` does a few operations per iteration on small integers,
  which spy keeps inline in the value and reads without evaluating the
  operand nodes. Big integers divide with Knuth's algorithm D and multiply
  with Karatsuba above 40 32-bit digits. A dictionary removal leaves a
  hole in the entry array rather than shifting the entries after it.
- `classes`, `generators`, `nbody` and `sort` are within 6% of CPython
  either way; `sort` merges natural runs.
- `fib` and `strings` are the furthest behind. `fib` is almost all calls,
  and each call still binds its arguments into a fresh environment and
  recurses in C; `strings` spends its time across the evaluator rather than
  in one operation.

These are implementation gaps, not language choices. MicroPython's 41 s on
`dicts` comes from its own implementation and was not investigated.

## Embedding lifecycle

`make bench` measures the embedding path without a process: it creates a
context, executes `print('Hello, world!')` with output discarded, and frees
the context, 20,000 times. On the build above it reports **192 µs of CPU time
per lifecycle** (three runs: 192.36, 190.97, 192.23 µs), down from 257 µs
at 0.3.0. The Mach-O `__TEXT` segment of `spy` is 1,343,488 bytes and the
executable 1,457,536 bytes.

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
