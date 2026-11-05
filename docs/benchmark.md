# Benchmarks

Engine: `main` at `e982005`, 0.8.0. This report compares wall time
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
| spy | `e982005`, 0.8.0 | `make`, Apple Clang 17, `-O2` | 1.5 MB |
| CPython 3.15 | 3.15.2 (the pinned oracle) | `configure --without-ensurepip`, `-O3`, no PGO/LTO | 6.3 MB, plus `Lib/` |
| CPython 3.14 | 3.14.3 | Homebrew bottle | Homebrew framework |
| PyPy | 8.0.1, Python 3.11.17 | Homebrew bottle, JIT | 33 MB `libpypy3.11-c` |
| RustPython | 0.6.1, commit `8c6c94b` | `cargo build --release`, rustc 1.99.1 | 42 MB |
| PocketPy | 2.2.1, commit `d2b7236` | its `build.sh`: `clang -O2 -DNDEBUG` | 0.6 MB |
| Monty | 1.4.0, commit `f3fb8e9` | `cargo build --release -p monty-runtime`, rustc 1.99.1 | 25 MB |
| MicroPython | 1.29.0, unix port | Homebrew bottle, `-X heapsize=512M` | 0.7 MB |

The spy, CPython 3.15, CPython 3.14, PyPy and MicroPython columns are the
median, cell by cell, of three runs of `bench/compare.py` at `e982005`,
with CPython 3.15.2 as the reference; memory is the largest of the three.
Two other runs were discarded: in them every engine was slower together
(up to 45% in one), which is the machine, not an engine. Across the three
runs most cells varied by at most 4% of their median; the widest were
CPython 3.15's `bigint` (12.7–16.1 ms), CPython 3.14's `classes`
(101–116 ms), and spy's `dicts` (69.2–77.5 ms), `classes` (90.5–101 ms) and
`bigint` (6.8–7.6 ms). Run alternately against 0.7.0, ten rounds each,
spy 0.8.0 took +0.9% on `classes`, +0.9% on `fib` and −0.3% on `bigint`.
PocketPy, RustPython and Monty are not built on this machine and were not
re-measured; their columns come from the run at `ea4d579` on the same
machine, with CPython 3.15.0 as the reference.

MicroPython's default heap cannot hold `dicts` and `sort`, so every program
runs with a 512 MiB heap. That raises its reported memory on programs that
allocate heavily (`nbody`, `strings`).

## Results

### Wall time

Median of the runs; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 2.6 ms | 11.2 ms | 19.4 ms | 17.5 ms | 27.8 ms | 2.9 ms | 4.0 ms | 3.1 ms |
| fib | 32.1 ms | 31.0 ms | 43.5 ms | 29.8 ms | 99.1 ms | 38.7 ms | 65.2 ms | 38.3 ms |
| loop | 153 ms | 398 ms | 393 ms | 25.5 ms | 634 ms | 218 ms | 368 ms | 232 ms |
| nbody | 217 ms | 237 ms | 310 ms | 43.2 ms | 701 ms | 377 ms | 735 ms | 642 ms |
| strings | 104 ms | 115 ms | 115 ms | 53.1 ms | 244 ms | 133 ms | 218 ms | 420 ms |
| dicts | 70.1 ms | 95.1 ms | 96.9 ms | 49.9 ms | 171 ms | 72.5 ms | 328 ms | 42.35 s |
| sort | 35.8 ms | 133 ms | 145 ms | 220 ms | 260 ms | 409 ms | 175 ms | 281 ms |
| classes | 91.6 ms | 101 ms | 102 ms | 22.0 ms | 299 ms | 140 ms | 345 ms | 130 ms |
| generators | 97.4 ms | 113 ms | 122 ms | 40.5 ms | 292 ms | 141 ms | error | 110 ms |
| bigint | 6.8 ms | 13.2 ms | 22.2 ms | 20.5 ms | 29.3 ms | wrong | 4.9 ms | 15.5 ms |

### Peak memory

Largest peak resident set size of the runs, in MiB; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 2.9 | 13.0 | 14.5 | 29.1 | 31.6 | 3.5 | 9.9 | 7.6 |
| fib | 3.0 | 13.1 | 14.6 | 32.3 | 31.9 | 3.5 | 10.1 | 7.6 |
| loop | 2.9 | 13.1 | 14.6 | 31.3 | 31.7 | 3.5 | 10.1 | 7.6 |
| nbody | 3.4 | 13.5 | 15.0 | 32.2 | 32.0 | 14.9 | 10.8 | 434.8 |
| strings | 3.1 | 13.1 | 14.7 | 32.0 | 31.9 | 21.2 | 11.2 | 76.9 |
| dicts | 50.0 | 45.5 | 46.9 | 76.1 | 82.9 | 19.2 | 30.1 | 36.7 |
| sort | 51.7 | 36.6 | 38.3 | 48.3 | 90.3 | 229.2 | 42.2 | 89.5 |
| classes | 3.1 | 13.1 | 14.7 | 32.0 | 31.9 | 30.2 | 10.8 | 25.9 |
| generators | 3.1 | 13.1 | 14.6 | 32.0 | 31.9 | 3.5 | — | 7.6 |
| bigint | 3.2 | 13.1 | 14.7 | 31.7 | 32.0 | — | 11.1 | 8.6 |

### Failures

- **Monty, `generators`**: rejected at parse time with `NotImplementedError`;
  Monty does not implement `yield`.
- **PocketPy, `bigint`**: prints `1 0 0 0`. PocketPy documents its integers as
  signed 64-bit rather than arbitrary precision; the factorial overflows.

## Reading the results

**Start-up and memory.** spy starts a process, runs `print` and exits in
2.6 ms and stays under 4 MiB for every program that does not build large
containers. PocketPy and MicroPython, the other two engines built for
embedding, start in about the same time. On `sort` spy uses about 1.4
times CPython's memory and on `dicts` 10% more. Values are carved from
16 KiB pools in three sizes: 96 bytes for a number, 112 for a string or
bytes with room for 16 bytes of text or a tuple of up to three items, and
208 for every other kind (a container, class or instance, which holds a
longer tuple's first 15 items), so 100,000 integers cost about 9 MiB.
Other engine memory (list items, dictionary entries, long text) comes
in blocks with a 16-byte header that records their size, so a context can
count and limit what it holds; that header added about 5% to `dicts` and
`sort` since 0.4.0.

**Throughput.** spy took 0.27 times CPython 3.15.2's time on `sort`,
0.40 on `loop`, 0.53 on `bigint`, 0.75 on `dicts`, 0.87 on `generators`,
0.89 on `classes` and 0.91 on `strings` and `nbody`, and took 4% longer
on `fib`. Against 0.6.0, `sort` fell from 127 to 35.6 ms. Built at
eight code layouts and timed alternately against `35cc21f`, the commit
before cycles were collected automatically, `dicts` measured 2.2% slower,
`strings` 1.4% and `loop` 1.0%; about 1.4% of `dicts` is the automatic
collection. spy has no
bytecode compiler and no JIT. Ordinary code is evaluated by walking the
syntax tree (`eval` in `spy.c`); suspendable bodies run on an instruction
list that still points into the tree. Syntax nodes cache what can be
reused between evaluations: a literal's value, a name's hash and the entry
it was last found in, whether an operator's operands can be read without
evaluation, and how a class's instances answer an attribute read, an
assignment or a method call. [optimization.md](optimization.md) records
each change behind these numbers.

- `sort` runs in about a quarter of CPython's time, `loop` in two fifths,
  `bigint` in half and `dicts` in three quarters. `sort` packs keys of
  one kind into an array of machine numbers: ints, floats without a NaN
  and pairs of ints whose spans fit together sort by radix, other keys by
  a merge of natural runs that compares without branching; tuples of
  numbers stay out of the cycle collector's list. `loop` does a few operations per iteration on small integers,
  which spy keeps inline in the value and reads without evaluating the
  operand nodes. Big integers divide with Knuth's algorithm D and multiply
  with Karatsuba above 40 32-bit digits. A dictionary removal leaves a
  hole in the entry array rather than shifting the entries after it.
- `strings`, `generators`, `nbody` and `classes` are 9–13% faster than
  CPython.
- `fib` is the furthest behind. It is almost all calls, and each call
  still binds its arguments into an environment and recurses in C:
  about 46 ns a call against CPython's 31.

These are implementation gaps, not language choices. MicroPython's 41 s on
`dicts` comes from its own implementation and was not investigated.

## Embedding lifecycle

`make bench` measures the embedding path without a process: it creates a
context, executes `print('Hello, world!')` with output discarded, and frees
the context, 20,000 times. On the build above it reports **202 µs of CPU time
per lifecycle** at 0.8.0, down from 257 µs at 0.3.0; 0.6.0 measured 191 µs.
Run alternately with 0.7.0 four times on the same day, 0.8.0 took
221–238 µs and 0.7.0 200–249 µs: the machine, not the engine, moved. The 186 µs reported for 0.5.0 was the machine, not the engine:
run alternately on the same day, 0.5.0 (`f1f274d`) took 188.86–190.60 µs
and 0.6.0 189.12–190.13 µs, and `sort` 129.8 and 129.4 ms. At 0.8.0 the
Mach-O `__TEXT` segment of `spy` is 1,409,024 bytes and the executable
1,526,608 bytes.

## Programs built with spyc

`spyc` is measured for what it costs a user: the time a build takes and the
program it builds. `python3 bench/spyc.py` (part of `make bench`) builds
`bench/programs/startup.py` seven times each way and times the median, then
alternates `spy startup.py` with the built program over ten rounds of 30
runs and reports the median of the round medians. Every run's output must
match `spy`'s. Measured at 0.8.0 on the platform above with `make` (Apple
Clang 17, `-O2`); spyc runs `cc -O2`:

| Measure | Result |
| --- | ---: |
| Build, executable (default) | 64.5 ms |
| Build, C only (`-e`) | 2.9 ms |
| Start-up, `spy startup.py` | 2.70 ms (rounds 2.63–2.80) |
| Start-up, the spyc-built program | 2.67 ms (rounds 2.63–2.86) |
| Size of the spyc-built program | 1,475,912 bytes (`spy`: 1,526,608) |

The build is the C compiler's time: spyc itself takes 2.9 ms. The built
program starts as fast as `spy` running the source, within noise. After
0.6.0 the same measures were 58.8 ms, 2.7 ms, 2.49 ms and 2.46 ms; on the
day of the 0.8.0 run, 0.7.0's `spy startup.py` took 2.66 ms run
alternately with 0.8.0's 2.63 ms, so the start-up difference is the
machine's. It is smaller than `spy` because it
links only the core (`libspy.a`), not the standard layer or the command's
host. Compiling the 176 KB bundle of `examples/flappy` takes 51 ms at `-O0`
and 53 ms at `-O2`, so `-O2` costs a bundle little.

## Native modules

`python3 bench/native.py [BASELINE_SPY]` (part of `make bench`) measures
what native modules cost a user: building `examples/fib.c` into `fib.so`,
importing it against importing the same function written in Python, and
importing 200 source modules, which shows the probe for `NAME.so` that each
source import now makes. Each import runs in a fresh process; the script alternates
the programs over ten rounds of 30 runs and reports the median of the round
medians, and every run's output must match. Given a `spy` built without
native modules, the 200-module program also runs on it. Measured on the
platform above (macOS 26.5.1, Apple Clang 17, `make`, `-O2`), with `main` at
`3c1c113` as the baseline:

| Measure | Result |
| --- | ---: |
| Build `fib.so` (`cc -O2`) | 68.2 ms |
| Size of `fib.so` | 33,400 bytes |
| Import `fib.so` and call it | 3.21 ms (rounds 3.18–3.95) |
| Import `fib.py` and call it | 3.09 ms (rounds 3.00–3.45) |
| Import 200 `.py` modules | 6.30 ms (rounds 6.20–7.12) |
| The same on the baseline | 6.01 ms (rounds 5.98–6.44) |

At 0.8.0, without a baseline: building `fib.so` 50.8 ms, importing it
2.90 ms (rounds 2.84–3.08), importing `fib.py` 2.76 ms (2.72–3.03), and
200 `.py` modules 6.08 ms (6.00–6.67).

Opening a library costs about 0.1 ms over parsing a small source. Every
source import now makes one more failed `stat`, for `NAME.so`, about 1.4 µs
on this macOS; CPython's search, which finds an extension module before a
source, needs it. Nothing else changes: the embedding lifecycle measured
184.4–185.1 µs against the baseline's 183.6–185.4 µs, run alternately, and
the programs of the table above, each built at eight code layouts and
averaged, stayed within 1% of the baseline (startup −0.6%, `fib` +0.3%,
`generators` +0.2% over 30 runs). `spy` grows by 320 bytes, to 1,510,064;
its `__TEXT` segment is unchanged.

## The JavaScript package

`node bench/javascript.mjs` measures what each transport of the JavaScript
package ([packaging/javascript.md](packaging/javascript.md) section 2.1)
costs a user: creating a runtime, a call from Python to a synchronous host
function and back (5,000 calls), an `eval("1")` round trip (2,000), and
`fib(25)` in the engine. The transports alternate over eight rounds and the
medians are reported. Measured on the platform above with Node.js 25.6.1 and
`spy-worker.wasm` built by wasi-sdk 34 (`-O2`), twice:

| Measure | Worker, shared inbox | Worker, JSPI | Same thread, JSPI |
| --- | ---: | ---: | ---: |
| Create a runtime | 16.4–17.1 ms | 16.4–16.8 ms | 0.74–0.84 ms |
| Host call round trip | 13.3–13.5 µs | 15.4–15.5 µs | 2.8–3.4 µs |
| `eval` round trip | 14.9–15.1 µs | 16.8–17.4 µs | 4.1–4.4 µs |
| `fib(25)` | 16.0 ms | 15.9–16.6 ms | 16.0 ms |

Starting a Worker is most of a runtime's creation. Inside a Worker, JSPI
costs about 2 µs a round trip over the inbox (a posted message against an
`Atomics` notification); on the same thread there is no thread to cross.
The engine computes at the same speed on every transport.

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
