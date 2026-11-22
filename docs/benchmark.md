# Benchmarks

Engine: `main` at `03bbf52`, 0.9.0. This report compares wall time
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
    "spy=bin/spy" "MicroPython=micropython -X heapsize=512M" ...
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
| spy | `03bbf52`, 0.9.0 | `make`, Apple Clang 17, `-O2` | 1.7 MB |
| CPython 3.15 | 3.15.2 (the pinned oracle) | `configure --without-ensurepip`, `-O3`, no PGO/LTO | 6.3 MB, plus `Lib/` |
| CPython 3.14 | 3.14.3 | Homebrew bottle | Homebrew framework |
| PyPy | 8.0.1, Python 3.11.17 | Homebrew bottle, JIT | 33 MB `libpypy3.11-c` |
| RustPython | 0.6.1, commit `8c6c94b` | `cargo build --release`, rustc 1.99.1 | 42 MB |
| PocketPy | 2.2.1, commit `d2b7236` | its `build.sh`: `clang -O2 -DNDEBUG` | 0.6 MB |
| Monty | 1.4.0, commit `f3fb8e9` | `cargo build --release -p monty-runtime`, rustc 1.99.1 | 25 MB |
| MicroPython | 1.29.0, unix port | Homebrew bottle, `-X heapsize=512M` | 0.7 MB |

The spy, CPython 3.15, CPython 3.14 and MicroPython columns are the
median, cell by cell, of three runs of `bench/compare.py` at `03bbf52`,
with CPython 3.15.2 as the reference; memory is the largest of the three.
Across the three runs every cell varied by at most 3% of its median but
spy's `bigint` (6.4–8.4 ms, the first run's) and CPython 3.14's `bigint`
(19.5–23.1 ms). Run alternately against 0.8.0 (`c012664`) on the same day,
spy 0.9.0 took −17% on `loop`, −22% on `generators`, −10% on `fib`, −7% on
`classes` and −1% on `strings`, with `nbody` unchanged; its peak memory
is 0.1–0.3 MiB higher on every program, the larger executable's pages.
PyPy is no longer installed on this machine; its column comes from the run
at `e982005`. PocketPy, RustPython and Monty are not built on this machine
and were not re-measured; their columns come from the run at `ea4d579` on
the same machine, with CPython 3.15.0 as the reference.

MicroPython's default heap cannot hold `dicts` and `sort`, so every program
runs with a 512 MiB heap. That raises its reported memory on programs that
allocate heavily (`nbody`, `strings`).

## Results

### Wall time

Median of the runs; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 2.5 ms | 10.6 ms | 18.3 ms | 17.5 ms | 27.8 ms | 2.9 ms | 4.0 ms | 3.0 ms |
| fib | 28.5 ms | 29.7 ms | 41.8 ms | 29.8 ms | 99.1 ms | 38.7 ms | 65.2 ms | 37.4 ms |
| loop | 121 ms | 381 ms | 378 ms | 25.5 ms | 634 ms | 218 ms | 368 ms | 227 ms |
| nbody | 213 ms | 233 ms | 303 ms | 43.2 ms | 701 ms | 377 ms | 735 ms | 640 ms |
| strings | 101 ms | 111 ms | 111 ms | 53.1 ms | 244 ms | 133 ms | 218 ms | 417 ms |
| dicts | 64.1 ms | 91.1 ms | 92.6 ms | 49.9 ms | 171 ms | 72.5 ms | 328 ms | 41.01 s |
| sort | 33.2 ms | 126 ms | 138 ms | 220 ms | 260 ms | 409 ms | 175 ms | 276 ms |
| classes | 81.8 ms | 97.1 ms | 97.0 ms | 22.0 ms | 299 ms | 140 ms | 345 ms | 132 ms |
| generators | 72.3 ms | 108 ms | 117 ms | 40.5 ms | 292 ms | 141 ms | error | 107 ms |
| bigint | 6.5 ms | 12.1 ms | 19.6 ms | 20.5 ms | 29.3 ms | wrong | 4.9 ms | 14.9 ms |

### Peak memory

Largest peak resident set size of the runs, in MiB; lower is better.

| Program | spy | CPython 3.15 | CPython 3.14 | PyPy | RustPython | PocketPy | Monty | MicroPython |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| startup | 3.0 | 13.0 | 14.5 | 29.1 | 31.6 | 3.5 | 9.9 | 7.6 |
| fib | 3.1 | 13.0 | 14.6 | 32.3 | 31.9 | 3.5 | 10.1 | 7.6 |
| loop | 3.1 | 13.0 | 14.6 | 31.3 | 31.7 | 3.5 | 10.1 | 7.6 |
| nbody | 3.5 | 13.5 | 15.0 | 32.2 | 32.0 | 14.9 | 10.8 | 434.8 |
| strings | 3.3 | 13.1 | 14.6 | 32.0 | 31.9 | 21.2 | 11.2 | 76.9 |
| dicts | 50.2 | 45.4 | 46.9 | 76.1 | 82.9 | 19.2 | 30.1 | 36.7 |
| sort | 51.9 | 36.6 | 38.2 | 48.3 | 90.3 | 229.2 | 42.2 | 89.5 |
| classes | 3.3 | 13.1 | 14.6 | 32.0 | 31.9 | 30.2 | 10.8 | 25.9 |
| generators | 3.2 | 13.1 | 14.6 | 32.0 | 31.9 | 3.5 | — | 7.6 |
| bigint | 3.4 | 13.0 | 14.5 | 31.7 | 32.0 | — | 11.1 | 8.6 |

### Failures

- **Monty, `generators`**: rejected at parse time with `NotImplementedError`;
  Monty does not implement `yield`.
- **PocketPy, `bigint`**: prints `1 0 0 0`. PocketPy documents its integers as
  signed 64-bit rather than arbitrary precision; the factorial overflows.

## Reading the results

**Start-up and memory.** spy starts a process, runs `print` and exits in
2.5 ms and stays under 4 MiB for every program that does not build large
containers. PocketPy and MicroPython, the other two engines built for
embedding, start in about the same time. On `sort` spy uses about 1.4
times CPython's memory and on `dicts` 11% more. Values are carved from
16 KiB pools in three sizes: 96 bytes for a number, 112 for a string or
bytes with room for 16 bytes of text or a tuple of up to three items, and
208 for every other kind (a container, class or instance, which holds a
longer tuple's first 15 items), so 100,000 integers cost about 9 MiB.
Other engine memory (list items, dictionary entries, long text) comes
in blocks with a 16-byte header that records their size, so a context can
count and limit what it holds; that header added about 5% to `dicts` and
`sort` since 0.4.0.

**Throughput.** spy took 0.26 times CPython 3.15.2's time on `sort`,
0.32 on `loop`, 0.54 on `bigint`, 0.67 on `generators`, 0.70 on `dicts`,
0.84 on `classes`, 0.91 on `strings`, 0.92 on `nbody` and 0.96 on `fib`:
it is faster than CPython on every program. Against 0.6.0, `sort` fell
from 127 to 33.2 ms. spy has no JIT. A function body that calls or
loops, and a module's or class's body, run on an instruction list (the
machine) whose steps point into the syntax tree, so a Python call or a
special method a step reaches runs as another machine rather than
recursing in C; other code is evaluated by walking the tree (`eval` in
`spy.c`). Syntax nodes cache what can be
reused between evaluations: a literal's value, a name's hash and the entry
it was last found in, whether an operator's operands can be read without
evaluation, and how a class's instances answer an attribute read, an
assignment or a method call. [optimization.md](optimization.md) records
each change behind these numbers.

- `sort` runs in about a quarter of CPython's time, `loop` in a third,
  `bigint` in half and `generators` and `dicts` in two thirds. `sort` packs keys of
  one kind into an array of machine numbers: ints, floats without a NaN
  and pairs of ints whose spans fit together sort by radix, other keys by
  a merge of natural runs that compares without branching; tuples of
  numbers stay out of the cycle collector's list. `loop` does a few operations per iteration on small integers,
  which spy keeps inline in the value and reads without evaluating the
  operand nodes. Big integers divide with Knuth's algorithm D and multiply
  with Karatsuba above 40 32-bit digits. A dictionary removal leaves a
  hole in the entry array rather than shifting the entries after it.
- `classes`, `strings` and `nbody` are 8–16% faster than CPython.
- `fib` is the closest, 4% faster only by its quicker start-up. It is
  almost all calls, and each call still binds its arguments into an
  environment: start-up aside, about 41 ns a call against CPython's 30.
  This is an implementation gap, not a language choice.

MicroPython's 41 s on
`dicts` comes from its own implementation and was not investigated.

## Embedding lifecycle

`make bench` measures the embedding path without a process: it creates a
context, executes `print('Hello, world!')` with output discarded, and frees
the context, 20,000 times. On the build above it reports **186 µs of CPU time
per lifecycle** at 0.9.0, down from 257 µs at 0.3.0. Run alternately with
0.8.0 three times on the same day, 0.9.0 took 185.7–187.1 µs and 0.8.0
196.3–198.6 µs (0.8.0's report gave 202 µs; earlier same-day runs showed the
machine moving such numbers by up to 10%). At 0.9.0 the Mach-O `__TEXT`
segment of `spy` is 1,671,168 bytes and the executable 1,799,264 bytes,
up from 1,409,024 and 1,526,608 at 0.8.0: the machine paths that keep
Python calls off the C stack.

## Programs built with spyc

`spyc` is measured for what it costs a user: the time a build takes and the
program it builds. `python3 bench/spyc.py` (part of `make bench`) builds
`bench/programs/startup.py` seven times each way and times the median, then
alternates `spy startup.py` with the built program over ten rounds of 30
runs and reports the median of the round medians. Every run's output must
match `spy`'s. Measured at 0.9.0 on the platform above with `make` (Apple
Clang 17, `-O2`); spyc runs `cc -O2`:

| Measure | Result |
| --- | ---: |
| Build, executable (default) | 64.0 ms |
| Build, C only (`-e`) | 2.8 ms |
| Start-up, `spy startup.py` | 2.63 ms (rounds 2.55–2.64) |
| Start-up, the spyc-built program | 2.58 ms (rounds 2.56–3.07) |
| Size of the spyc-built program | 1,765,064 bytes (`spy`: 1,799,264) |

The build is the C compiler's time: spyc itself takes 2.8 ms. The built
program starts as fast as `spy` running the source, within noise. After
0.6.0 the same measures were 58.8 ms, 2.7 ms, 2.49 ms and 2.46 ms, and
after 0.8.0 64.5 ms, 2.9 ms, 2.70 ms and 2.67 ms; on the day of the 0.8.0
run, 0.7.0's `spy startup.py` took 2.66 ms run alternately with 0.8.0's
2.63 ms, so such start-up differences are the machine's. The built
program is smaller than `spy` because it links only the core (`libspy.a`), not the standard layer or the command's
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
200 `.py` modules 6.08 ms (6.00–6.67). At 0.9.0: 48.3 ms, 2.82 ms
(2.79–3.07), 2.69 ms (2.64–2.71) and 5.94 ms (5.90–6.14).

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

### Compiler migration measurements

`make bench/compiler` builds a development benchmark using the public C API.
It measures two operations independently, using C11 `clock()` CPU time:

- `compile`: call the `compile` builtin and release its returned code object.
- `execute`: call `exec` repeatedly with one compiled code object and one
  namespace. Compilation and a warmup execution precede the timer.

Both exclude process launch, source-file I/O, context creation and shutdown.
The output callback discards Python output. Each workload checks its result;
a syntax error, runtime error, failed assertion or invalid timing aborts the
comparison. Compilation generates every body's instructions, the
module's too, during the parse, but still from a syntax tree, so its
timing does not yet represent a one-pass source-to-bytecode compiler.

Build the same harness against each revision's library, then run:

```sh
cc -O2 -std=c11 -Wall -Wextra -Wpedantic bench/compiler.c /path/to/old/libspy.a -lm -o /tmp/compiler-before
make bench/compiler
python3 bench/compiler.py before=/tmp/compiler-before after=bench/compiler \
    --rounds 9 --iterations 1000 --report /tmp/compiler-comparison.json
```

The driver alternates engine order every round and prints median CPU
microseconds per operation. The JSON retains every sample. These measurements
complement the end-to-end wall times above; neither replaces the other.
See [compiler-migration.md](compiler-migration.md) for the unfinished migration
and its validation requirements.

#### Constant operands checkpoint, 2026-11-22

Before: `2b03b143`. After: `spy.c` SHA-256
`73d2241240c493469ac5e6bcf9b261b506e4c08cef53a0012c0a7b66087f2ade`.
Apple M2, 8 GiB RAM, Darwin 25.5.0 arm64; Apple Clang 17.0.0,
`-O2 -std=c11 -Wall -Wextra -Wpedantic`. Linux verification was paused for
the measurements. Both CLI executables are 2,453,440 bytes.

Nine alternating rounds, 1,000 operations per sample; CPU microseconds:

| Workload | Phase | Before | After |
| --- | --- | ---: | ---: |
| definitions | compile and release | 94.88 | 94.50 |
| definitions | execute compiled code | 27.87 | 26.89 |
| constants | compile and release | 10.16 | 10.03 |
| constants | execute compiled code | 48.19 | 47.47 |
| closures | compile and release | 6.59 | 6.57 |
| closures | execute compiled code | 64.71 | 64.93 |
| branches | compile and release | 7.05 | 7.01 |
| branches | execute compiled code | 7.07 | 7.02 |

The programs in `bench/programs` were also run using `bench/compare.py`'s
`run` function, alternating the two CLIs for seven rounds per program
(30 for startup). Every output matched the pinned CPython 3.15.2 oracle.
Median wall milliseconds, including process launch, parsing and shutdown:

| Program | Before | After |
| --- | ---: | ---: |
| bigint | 7.765 | 8.036 |
| classes | 93.097 | 91.047 |
| dicts | 78.491 | 78.681 |
| fib | 29.735 | 29.819 |
| generators | 81.684 | 82.499 |
| loop | 137.744 | 137.928 |
| nbody | 259.446 | 258.464 |
| sort | 37.392 | 37.443 |
| startup | 2.660 | 2.664 |
| strings | 110.271 | 107.847 |

These results do not establish a general speedup. Compile medians changed
by less than 1.5%; end-to-end changes range from 2.2% faster to 3.5% slower,
including a slower bigint program. This checkpoint still constructs and
walks syntax trees. The larger compiler migration remains unmeasured.

[Raw samples and source fingerprints](compiler-benchmark.json) include
peak resident memory for each CLI run. The inherited Python intrinsics were
not moved into C: `intrinsics.py` SHA-256 is
`f6d361745ae9c5e8c943b0a7ba651d72ff17e0cb5eb92a65b80fe03f2e742809`,
`spy-intrinsics.h` is
`5b5217e27cef756c0b049b96f65dceb84f64c3b3b49f8f45f2facd3e35681904`,
and `spy-unicode.h` is
`2e5202343207dc7472bf643be387a6708d000197dbb905b67a2a59f8475fb960`.

#### Scope properties during parsing, 2026-11-22

Before: `e01f2494`. After: `spy.c` SHA-256
`945d59f661a1117bcc3fa29ac157ec77aac2f32d7293d07addad6f387ced7ea9`.
Apple M2, 8 GiB RAM, Darwin 25.5.0 arm64; Apple Clang 17.0.0,
`-O2 -std=c11 -Wall -Wextra -Wpedantic -Werror`. Verification jobs were
idle during these measurements. CLI size changed from 2,453,440 to
2,453,376 bytes.

The parser now records generator classification, valued-return locations
and namespace writes, removing their later tree walks. The compiler still
builds trees for binding analysis and instruction generation. These are
measurements of that intermediate compiler, not a completed single-pass
implementation.

Nine alternating rounds, 1,000 operations per sample, using
`bench/compiler.py`; median CPU microseconds:

| Workload | Phase | Before | After |
| --- | --- | ---: | ---: |
| definitions | compile and release | 94.14 | 93.26 |
| definitions | execute compiled code | 26.84 | 26.95 |
| function_body | compile and release | 73.80 | 72.34 |
| function_body | execute compiled code | 3.34 | 3.34 |
| namespace | compile and release | 63.37 | 62.33 |
| namespace | execute compiled code | 14.27 | 14.34 |
| constants | compile and release | 10.02 | 9.92 |
| constants | execute compiled code | 45.69 | 46.33 |
| closures | compile and release | 6.20 | 6.12 |
| closures | execute compiled code | 61.48 | 61.02 |
| branches | compile and release | 6.57 | 6.51 |
| branches | execute compiled code | 6.62 | 6.63 |

Compile medians fell 0.9–2.0% across these workloads. Execution differences
were small and mixed; this is not evidence of a general runtime speedup.

The end-to-end comparison used `bench/compare.py`'s `run` function, with
two warmups per engine and 15 alternating rounds per program (30 for
startup). Each result matched the pinned CPython 3.15.2 oracle. Median wall
milliseconds include process launch, parsing, execution and shutdown:

| Program | Before | After |
| --- | ---: | ---: |
| bigint | 6.695 | 6.719 |
| classes | 94.009 | 94.853 |
| dicts | 82.002 | 81.681 |
| fib | 30.313 | 30.242 |
| generators | 78.061 | 77.795 |
| loop | 131.642 | 132.961 |
| nbody | 255.431 | 255.951 |
| sort | 38.846 | 38.878 |
| startup | 2.739 | 2.721 |
| strings | 112.704 | 112.861 |

Changes range from 0.7% faster to 1.0% slower. An initial comparison without
warmups had large first-launch outliers; it is not used to establish a
performance difference. [Raw samples and source fingerprints](compiler-scope-benchmark.json)
include every measured CPU and wall sample, per-process peak memory, and
both inherited intrinsics fingerprints. The intrinsics implementation is
unchanged.

### Other implementations

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
