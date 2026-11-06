# Roadmap

Planned work, not implemented features. The manual describes what exists;
[docs/benchmark.md](docs/benchmark.md) records what was measured. Each item
says where the engine stands today, so the first step is clear.

## Contents

- [Embeddable library](#embeddable-library): a stable ABI at 1.0, build
  options, context density, thin bindings, a portability matrix, an API
  reference
- [Distribution](#distribution): what one executable still lacks, the
  standard library, tree shaking
- [Sandboxed runtime](#sandboxed-runtime): runtime policy, virtual file
  systems, host functions, threads that switch anywhere they block,
  inspection, snapshots,
  replay, Pi codemode
- [Platforms](#platforms): WebAssembly and the edge, Android and iOS, bare
  metal
- [Development](#development): hot module reload
- [Long-term maintenance](#long-term-maintenance): memory safety,
  refactoring, performance, tracking CPython
- [Performance](#performance)
- [Done](#done)

## Embeddable library

`libspy.a` is the product; `spy` and `spyc` are its first hosts. libghostty
shows the path (a reusable terminal core that Ghostty's own app only
demonstrates): it was adopted once embedders could rely on a stable ABI,
trim the build, run many instances cheaply and bind from their own
language. Most other sections depend on this one being solid.

### Stable C API and ABI from 0.8 to 1.0

The rules are in place ([manual 3.4.8](docs/manual.md#348-stability)):
`spy_version()` reports the library's version next to the header's
`SPY_VERSION`, every declaration in `spy.h` states its ownership and errors,
and `make check-api` compiles the last release's declarations against the
current header and compares `libspy.a`'s exports with it. 0.8.0 makes the
last incompatible changes planned (`spy_type` reports only the data types a
host converts and `SPY_OBJECT`; limits are set through `spy_set_limit`
alone), and every release from it to 1.0.0 stays compatible with it.
Remaining: release 0.8.0, then declare the API and ABI stable at 1.0.0.

### Build options

Embedders want a smaller library with less attack surface. Let a build
leave out host-facing parts the core does not need: `open` and `spy_mount`,
metering, the host output callback and the generated intrinsics that only
the standard layer uses. The language cannot shrink this way. Arbitrary
integers, Unicode and exceptions are PLS-315 requirements. Only the default
build claims conformance, and CI builds every option so that none rots.
`--analyze` in `spyc` reports what each option saves.

### Context density

Contexts are independent and share no global state, so one process can host
many. Measure what that costs: the memory of an empty context and of one
that has run a small program, and a density benchmark that runs thousands
of active contexts on a fixed machine and reports throughput and resident
memory. Then shrink the empty context (lazy builtin tables, interned
strings shared read-only between contexts, smaller initial heaps) until the
benchmark stops improving. This is what the sandboxed runtime is priced by:
one context per agent call.

Past that point, start a context from a prebuilt image instead of building
it: the builtins, and the intrinsics module that today runs once per context
on first use, set up at build time and copied in. djs creates a VM this way
in about 40 µs in wasm, and its Pi adapter keeps the image taken after Pi's
prelude, so a codemode script starts in 1.0 ms against QuickJS's 3.9 ms. It
needs the snapshot format below. Memory figures for this work compare
distributions over runs with the heap layout perturbed, not single runs:
where the allocator places a growing heap can move one run's peak by
megabytes.

### Thin bindings

Go, Java, JavaScript, Python and Rust bindings exist. Keep each a thin layer over
`spy.h` or the worker protocol ([docs/packaging/protocol.md](docs/packaging/protocol.md)),
so that a binding is days of work and not a second implementation. Add new
ones only when a real host asks for it. Swift and .NET are the likely next
ones. A binding
lets a program use its host language's packages instead of a Python
standard library ported here (see the note under
[Standard library coverage](#standard-library-coverage)).

### Portability matrix

CI tests Linux and macOS on x86-64 and arm64, and on Windows builds the
release archive, the Python package and the Java artifacts with MinGW-w64
GCC. Build and test `libspy.a` on FreeBSD, Android, iOS, WASI and a
freestanding target with no C library beyond what the host supplies. MSVC
is out of reach while it lacks C11 complex numbers, which `complex` is
built on.
Supporting a platform starts with a green build here, before the
platform's own items below.

### API reference

[docs/api.md](docs/api.md) is generated from `spy.h` (`make
api-reference`), checked current by `make check-api`, and installed with the
manual. Remaining: publish it as a web page with each release.

## Distribution

### `spyc`: what one executable still lacks

`spyc` follows a program's imports, embeds every module it reaches, compiles
`NAME.c` modules in, links `libNAME.a` archive modules, and leaves one
executable, with import semantics kept and the generated C file
byte-for-byte reproducible ([docs/build.md](docs/build.md)). Remaining:

- Package resources: data files a package reads with
  `importlib.resources` or relative to `__file__`, declared on the command
  line or found next to the package, embedded and served read-only through
  the virtual file system below.
- Deterministic executables: the executable, not only the C file, is the
  same bytes for the same inputs and compiler. Fixed flags, no timestamps or
  absolute paths, and a build manifest recording the inputs' hashes.
- Standard modules the program imports are bundled from the standard layer
  as a local module is, instead of being registered by hand with `-M`.

### Standard library coverage

The standard layer (`spy-std.c`) has `sys`, and `stdlib/` the C modules,
each linked into a host or loaded as a shared library: `_thread` so far. Cover it in steps, so that both
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

// Note at 2026-10-31: This is a very large chunk of work and hard to track
with upstream. Ideally I want small-python to have a simple interface in each
language so that it can call those packages in that language eco-system
rather than build it in this project, considering it's one-man's side project.

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
`spy_mount`, and the engine enforces a step limit, a memory limit and a host
interrupt callback ([docs/metering.md](docs/metering.md)). The manual says
plainly that this is not yet an isolation boundary; this section is what
makes it one.

### Runtime policy API

`spy_set_policy` installs a callback asked before each sensitive action
(`open`, `import`, `exec`, `input`, `dlopen`), hosts ask it about their own
actions with `spy_policy_check`, and every binding and the worker protocol
forward it ([manual 3.4.6](docs/manual.md#346-host-services-and-limits)). A callback answers one event at
a time; what is missing is the policy it would enforce. Capability-native
Python: code reaches nothing unless the host granted it. One policy object
per context, set by the host and fixed once code runs, with fine-grained
grants for:

- modules, including which standard and native modules may be imported;
- files, by path, with read, write and create separately;
- network, by host, port and protocol;
- host tools, the functions the host defines.

A denied operation raises `PermissionError` in Python and is reported to the
host. The policy is the same in C, in the Python binding and in the
JavaScript binding, and is tested by programs that try to escape it.

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

Values that cross the boundary go through one compact binary encoding, with
a table so that repeated dictionary keys are sent once, measured against
JSON as the baseline it has to beat (djs's wire format is 1.4 to 9 times
faster than `JSON.stringify` plus `JSON.parse` in wasm).

### Threads that switch anywhere they block

`_thread` ([docs/threads.md](docs/threads.md)) runs virtual threads on the
host's system thread. A thread that blocks runs other threads on top of
itself, so it resumes only when the threads above it end, and a wait that
needs a thread below it raises `RuntimeError`. Two threads that hand a lock
back and forth fail so. Once calls no longer recurse in C (*Toward bytecode*
in [docs/optimization.md](docs/optimization.md)), a thread with only Python
frames since its start can set them aside and resume later, so threads
switch wherever they block.
Calls from C into Python (a sort key, `__eq__`) still raise there. Then let
host functions answer later, so that threads wait for several slow host
functions (a model's tools, network requests) at once.

### Embedded inspector

Trace execution, allocations, policy violations and imports, as structured
events the host subscribes to, with cost only when a subscriber is attached.
This is also the event stream that record and replay and the agent tooling
below consume.

### Snapshot, fork and resume

Save a context and resume it later, or fork it into several that continue
independently: agent checkpointing, speculative execution, branching
evaluation and durable workflows. A snapshot is taken when the context is
idle, between top-level operations, so no frame is running: the engine
does not pause inside a call (see
[WebAssembly and the edge](#webassembly-and-the-edge) for host calls that
wait without blocking a thread).

A snapshot of the interpreter's memory is not a snapshot of the outside
world. Pure Python state (values, frames, generators, coroutines) can be
serialized. Open file descriptors, native objects and effects already sent
to the host cannot. A context is snapshotable when everything it holds is
in the first group; anything else makes the snapshot fail with the reason,
unless the host supplies a way to reopen or recreate it. Code that only
does safe operations must always be forkable.

Values hold real pointers, so a snapshot cannot be a copy of memory as it
is in djs. The cycle collector already traces every live value; the same
trace can write the graph out and read it back. Around that, borrow djs's
container: a header with the engine's build hash, so that an image loads
only into the build that wrote it; the image compressed with zstd against a
reference image both sides can rebuild (the prebuilt base image, or the one
taken after a codemode prelude), which brings a session waiting on a tool
from about 550 KB down to 2 to 9 KB in djs; and journal replay, not a
version-independent format, for durability across engine versions.

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

Make determinism a tested property, not only a recording. Every source of
nondeterminism is a host input: the clock, randomness, and weak references,
which a deterministic mode makes either always strong or absent. Python adds
one source that JavaScript lacks: `id`, the default `__hash__` and so the
iteration order of sets of plain objects all come from addresses today. A
deterministic mode derives them from an allocation counter instead. A
canonical hash of the live graph, independent of when the collector last
ran, is recorded in the trace at each idle point and at the end, so a
replay that diverges is caught where it diverges. The tests then compare
those hashes across step-budget slicings, across snapshot and restore, and
between native and wasm builds.

### Codemode plugin for the Pi agent

A codemode plugin for the Pi coding agent: the model writes Python, which
runs in a Small Python context instead of QuickJS, with the tools Pi exposes
offered as host functions. It ships with a default runtime policy, metering
and a virtual file system, so its guardrails are stricter than a bare
JavaScript sandbox's, and it is the first user of the layer above.

Pi keeps everything engine-specific in one module, `src/runtime/vm.ts`
(the `startVm` contract and its message protocol). djs replaces only that
module and runs Pi's own codemode test suite on a copy of the package; the
plugin can be accepted the same way, with every failing test explained.
Next to it, a corpus of Python codemode scripts written by models, with
fake tool results and redacted as djs's harvested corpus is, serves as
both a regression suite and the benchmark for this use.

## Platforms

### WebAssembly and the edge

The JavaScript package runs the engine compiled to WebAssembly in a Worker
thread, or with `worker: false` on the calling thread, on Node.js and in
browsers. The engine waits for its host only in one import, `read`; with
JavaScript Promise Integration (JSPI, WebAssembly stack switching), `read`
is an async function, so the engine's whole stack, C frames included, is
suspended until a message arrives while the event loop runs on. A host call
from any Python code, inside a sort key or `__eq__` too, then waits on a
promise without `SharedArrayBuffer`, and without threads for edge runtimes
such as Cloudflare Workers. The engine did not change: it does not pause on
its own, so ordinary calls keep their speed. Where JSPI is missing, the
package keeps the `SharedArrayBuffer` inbox
([docs/packaging/javascript.md](docs/packaging/javascript.md) section 2.1).

Remaining: a test on Cloudflare Workers and in browsers (only Node.js runs
in CI); a WASI build; and `spyc --target wasm`, which produces one module
for a bundled program.

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
UndefinedBehaviorSanitizer and, on Linux, LeakSanitizer, and also under
MemorySanitizer and ThreadSanitizer; `tests/oom` fails each allocation in
turn; `fuzz/` has libFuzzer targets for evaluation, compilation, `spyc`
and allocation failure. Continue with:

- every executable in the repository, `spyc` and `spy-worker` included,
  freeing what it allocates, so leak checks stay meaningful and a tool can
  later become a library;
- fuzzing run continuously, with targets for the module loader, the wire
  protocol of the bindings and, once they exist, the policy and snapshot
  formats;
- a static analyzer in CI;
- an ownership test for each new C API function, as the existing ones have;
- a GC stress mode that runs the specification suite with a collection at
  every point where one may happen, so a value missing from the collector's
  trace fails a test instead of waiting for an unlucky schedule. Once
  snapshots exist, a second mode snapshots and restores the context every
  *N* steps. In both, the output must not change.

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
At 0.7.0 ([docs/benchmark.md](docs/benchmark.md)) spy runs every benchmark
program faster than CPython 3.15 except `fib`, which takes 4% longer: it is
almost all calls, and each call binds an environment and recurses in C.
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
under a walker node. They are weighed on speed alone: host calls wait
through JSPI ([WebAssembly and the edge](#webassembly-and-the-edge)) and
snapshots are taken at idle points, so neither needs them. The plan and its measurements are in
[docs/optimization.md](docs/optimization.md#toward-bytecode).

Expected gain: two to three times on interpreter-bound programs.

### Benchmark suite

[docs/benchmark.md](docs/benchmark.md) measures ten core-language programs.
Extend it with standard-library workloads (JSON, regular expressions, I/O) as
those modules arrive, larger programs alongside the micro-benchmarks, and a
regression check in CI that flags a slowdown before it is merged.

Size gets the same treatment: CI records the gzip size of `libspy.a` and the
wasm module as a ceiling that may only fall. A change that raises it says
what the extra size buys.

## Done

- [x] Metering: step limit, memory limit and interrupt callback inside the
  engine ([docs/metering.md](docs/metering.md))
- [x] MemorySanitizer, ThreadSanitizer, allocation-failure tests, `spyc`
  fuzzer
- [x] API reference generated from `spy.h`; `make check-api`
- [x] `spyc` bundles a program's imports into one C file
- [x] Go and Rust bindings
- [x] Values from pools in three size classes
- [x] Java binding; TLA+ models of every package
- [x] `spyc` writes an executable and compiles C modules in
- [x] JavaScript package without `SharedArrayBuffer` or a Worker, through JSPI
- [x] `_thread` in `stdlib/`, static or shared: virtual threads
- [x] Native modules: `spy`, the in-process bindings and every worker
  package through the protocol's `NATIVE`
- [x] Policy callback (`spy_set_policy`, `spy_policy_check`)
- [x] Automatic cycle collection; the `gc` module removed
- [x] Last incompatible C API changes before 1.0 (0.6.0)
