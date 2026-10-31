# Roadmap

Planned work, not implemented features. The manual describes what exists;
[docs/benchmark.md](docs/benchmark.md) records what was measured. Each item
says where the engine stands today, so the first step is clear.

## Contents

- [Distribution](#distribution): one executable from pure Python, the
  standard library, tree shaking
- [Sandboxed runtime](#sandboxed-runtime): runtime policy, metering, virtual
  file systems, host functions, inspection, snapshots, replay, Pi codemode
- [Platforms](#platforms): WebAssembly and the edge, Android and iOS, bare
  metal
- [Development](#development): hot module reload
- [Long-term maintenance](#long-term-maintenance): memory safety,
  refactoring, performance, tracking CPython
- [Performance](#performance)

## Distribution

### `spyc build`: one executable from pure Python

`spyc` already bundles: it follows a program's imports, embeds every module it
reaches in one C file, and keeps import semantics and byte-for-byte
reproducible output ([docs/build.md](docs/build.md)). The user still runs the
C compiler. Add `spyc build`, which writes that C file, compiles it with
`spy.c` (and `spy-std.c` when needed) and leaves one executable, with no
Python file shipped beside it.

- Package resources: data files a package reads with
  `importlib.resources` or relative to `__file__`, declared on the command
  line or found next to the package, embedded and served read-only through
  the virtual file system below.
- Deterministic builds: the executable, not only the C file, is the same
  bytes for the same inputs and compiler. Fixed flags, no timestamps or
  absolute paths, and a build manifest recording the inputs' hashes.
- Standard modules the program imports are bundled from the standard layer
  as a local module is, instead of being registered by hand with `-M`.

### Standard library coverage

The standard layer (`spy-std.c`) has `sys` and `gc`; the rest of
the standard library is out of scope today. Cover it in steps, so that both
`spy` (at run time) and `spyc` (at build time) load the same modules:

1. Pure-Python modules, ported from CPython 3.15 with as few edits as
   possible, each edit marked, so that tracking upstream is a diff and not a
   rewrite. A script reports which upstream modules changed since the pinned
   commit.
2. Modules whose C implementation needs only the C library (`math`, `_struct`,
   `binascii`, `_bisect`, `_heapq` and the like), written against `spy.h`.
3. Modules whose C implementation needs the CPython C API. These need a
   compatibility layer over `spy.h`, the same effort the Cython baseline
   ([docs/testing/cython.md](docs/testing/cython.md)) points to.

Modules that need the operating system (`os`, `socket`, `subprocess`) go
through the runtime policy of the next section, never around it. Each module
is optional at build time, and native extension packages bundle as their
Python modules do.

Goal: broad compatibility with the CPython 3.15 standard library, measured by
running its own test modules, and reported as passed, failed and skipped
separately, as the Cython baseline is.

### Module tree shaking

The bundle already contains only the modules a program reaches. Once the
standard library is bundled, that set grows through imports no program path
uses. Remove modules only reached from guarded imports the program never takes
or from code a flag disables, and leave out the engine's own unused native
modules, with `--analyze` reporting what each removal saved. Statement-level
shaking stays a non-goal: it changes behavior ([docs/build.md](docs/build.md)
section 8).

## Sandboxed runtime

A layer outside the language core that lets an AI agent, or any host, run
untrusted Python safely. The core keeps executing the language; the layer
decides what the code may reach. Today a context reaches files only through
`spy_mount`, has a step limit, and the Python and JavaScript bindings bound
memory and wall time from outside the engine. The manual says plainly that
this is not yet an isolation boundary; this section is what makes it one.

### Runtime policy API

Capability-native Python: code reaches nothing unless the host granted it.
One policy object per context, set by the host and fixed once code runs,
with fine-grained grants for:

- modules, including which standard and native modules may be imported;
- files, by path, with read, write and create separately;
- network, by host, port and protocol;
- host tools, the functions the host defines.

A denied operation raises `PermissionError` in Python and is reported to the
host. The policy is the same in C, in the Python binding and in the
JavaScript binding, and is tested by programs that try to escape it.

### Fuel and resource metering

Budgets the engine itself enforces, per context and per call: instructions
(the step limit, made to cover native builtins too), wall and CPU time,
memory (inside the engine, not only in the bindings' allocator), and output
bytes. Exhausting one raises an exception the program cannot catch and leaves
the context reusable.

### Virtual file system

`open` and the module loader read through one file system interface instead
of host paths: memory-backed, read-only, overlay (writes go to an upper layer
over a read-only base) and transactional (changes commit or roll back as one).
Overlays make parallel agents cheap: each edits its own copy of a source tree
and the host merges, keeps or discards the result. `spy_mount` becomes one
backend among these.

### Host function ABI

`spy_define` exposes C functions, and the bindings expose Python and
JavaScript functions over their own protocols. Unify them: one description of
a host function (name, parameters, keyword arguments, types, async or not,
which policy grant it needs) from which each binding generates the Python
signature, argument conversion and documentation, so a tool written once is
offered the same way from C, Python and JavaScript.

### Embedded inspector

Trace execution, allocations, policy violations and imports, as structured
events the host subscribes to, with cost only when a subscriber is attached.
This is also the event stream that record and replay and the agent tooling
below consume.

### Snapshot, fork and resume

Save a context and resume it later, or fork it into several that continue
independently: agent checkpointing, speculative execution, branching
evaluation and durable workflows.

A snapshot of the interpreter's memory is not a snapshot of the outside
world. Pure Python state (values, frames, generators, coroutines) can be
serialized. Open file descriptors, native objects and effects already sent
to the host cannot. A context is snapshotable when everything it holds is
in the first group; anything else makes the snapshot fail with the reason,
unless the host supplies a way to reopen or recreate it. Code that only
does safe operations must always be forkable.

### Deterministic execution and replay

`spy --record trace` writes every nondeterministic input the program
consumed (host function results, file reads, time, random seeds, input
lines) and `spy replay trace` runs the program again with those inputs, so
the same run reproduces exactly, for debugging an agent's run after the
fact and for tests.

A terminal recorder such as asciinema is not a substitute: it records what
the program printed, not what it read, so it can show a run but not rerun
it. Recording at the host boundary is cheap once the policy layer and the
inspector route every external input through one place, and it is the same
mechanism snapshots need to describe host effects. Do it after those two.

### Codemode plugin for the Pi agent

A codemode plugin for the Pi coding agent: the model writes Python, which
runs in a Small Python context instead of QuickJS, with the tools Pi exposes
offered as host functions. It ships with a default runtime policy, metering
and a virtual file system, so its guardrails are stricter than a bare
JavaScript sandbox's, and it is the first user of the layer above.

## Platforms

### WebAssembly and the edge

The JavaScript package already runs the engine compiled to WebAssembly, in a
worker thread, on Node.js and in cross-origin isolated browsers. Remaining:
a build without `SharedArrayBuffer` and threads, for pages that are not
cross-origin isolated and for edge runtimes such as Cloudflare Workers; a
WASI build; and `spyc build --target wasm`, which produces one module for a
bundled program.

### Android and iOS

Build `libspy.a` for both, with the file system and output services mapped to
the app sandbox, and an example app for each. iOS forbids generating machine
code at run time, which an interpreter does not need.

### Game Platforms

Wire Small Python into game toolchains such as Godot and Unity. Because it
comes without a standard library, Python code can call the engine's APIs
just as C# or GDScript do.

### Bare metal

Run on microcontrollers such as the ESP32 and on Raspberry Pi boards without
an operating system: build without a POSIX host (file access already raises
`OSError` there), let the host supply the allocator, set a fixed memory
budget, and measure the smallest usable configuration in flash and RAM.

## Development

### Hot module reload

Replace a module's code while the program runs and keep selected state: the
host or the module marks what survives (for example a game's world state),
functions and classes are rebound, and live instances move to the new class.
For game developers it means editing code and seeing the result in the next
frame. It builds on the import system's loader and on the virtual file
system's change notifications.

## Long-term maintenance

Work that is never finished, done alongside every item above rather than
after it.

### Memory safety of the C code

Everything is C, so every tool and every program it produces must be
memory safe, not only the engine. `make sanitize` runs the C API tests, the
specification suite and the bundler tests under AddressSanitizer,
UndefinedBehaviorSanitizer and, on Linux, LeakSanitizer; `fuzz/` has
libFuzzer targets for evaluation and compilation. Continue with:

- every executable in the repository, `spyc` and `spy-worker` included,
  freeing what it allocates, so leak checks stay meaningful and a tool can
  later become a library;
- fuzzing run continuously, with targets for the bundler, the module loader,
  the wire protocol of the bindings and, once they exist, the policy and
  snapshot formats;
- MemorySanitizer and ThreadSanitizer where they apply, and a static
  analyzer in CI;
- an ownership test for each new C API function, as the existing ones have.

A memory-safety bug in the sandboxed runtime is a sandbox escape, so this
work gates that section.

### Refactoring

Keep the code small as it grows: rewrite a part once a better shape is
clear, remove what no longer earns its place, and keep `spy.c` readable as
one file. A refactor changes no behavior and is measured as a performance
change is.

### Performance

The [Performance](#performance) section below lists the current structural
work. Beyond it, every change keeps its benchmark numbers and the benchmark
report is refreshed before each release.

### Tracking CPython

The target is CPython 3.15, pinned as the development oracle. Follow its
patch releases, then move to 3.16 when it is released: update PLS-315 (or
write its successor), the specification tests and the TLA+ models, and the
ported standard-library modules, with a script that reports what changed
upstream since the pinned commit.

## Performance

The goal is to come as close to CPython's performance as the design allows.
At 0.4.0 ([docs/benchmark.md](docs/benchmark.md)) spy runs `loop`, `bigint`,
`dicts` and `classes` faster than CPython 3.15, is within 3% on `generators`,
`nbody` and `sort`, and is 12 to 13% slower on `strings` and `fib`.
Values already come in three sizes, and arrays for locals and calls without
C recursion were tried and measured slower
([docs/optimization.md](docs/optimization.md#tried-and-left-out)). Profiles
are flat, so the remaining work is structural. Each step must keep `make
test`, the spec suite, the TLA+ models and the sanitizer runs green, and its
commit reports before and after timings.

### Toward bytecode

Ordinary code is evaluated by walking the syntax tree; generators run on an
instruction list that hands every expression that cannot suspend back to the
walker. Move node kinds onto machine instructions one at a time, each only
once it measures faster than the walker, then revisit locals in slots and
calls without C recursion, which pay only once a machine step costs well
under a walker node. The plan and its measurements are in
[docs/optimization.md](docs/optimization.md#toward-bytecode).

Expected gain: two to three times on interpreter-bound programs.

### Benchmark suite

[docs/benchmark.md](docs/benchmark.md) measures ten core-language programs.
Extend it with standard-library workloads (JSON, regular expressions, I/O) as
those modules arrive, larger programs alongside the micro-benchmarks, and a
regression check in CI that flags a slowdown before it is merged.
