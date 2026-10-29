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

The standard layer (`spy-std.c`) has `sys`, `gc` and `weakref`; the rest of
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

## Performance

The goal is to come as close to CPython's performance as the design allows.
spy is up to 2.4 times slower than CPython 3.15 on the core-language
benchmarks. Profiles of `fib`, `classes`, `generators` and `nbody` show the
time spread across the evaluator rather than in one operation, so the
remaining work is structural. Each step must keep `make test`, the spec
suite, the TLA+ models and the sanitizer runs green, and its commit reports
before and after timings.

### Benchmark suite

[docs/benchmark.md](docs/benchmark.md) measures ten core-language programs.
Extend it with standard-library workloads (JSON, regular expressions, I/O) as
those modules arrive, larger programs alongside the micro-benchmarks, and a
regression check in CI that flags a slowdown before it is merged.

### Function locals in an array

A call now builds a map value for its locals, keyed by symbol, and a local
read checks a cached entry position before falling back to a lookup. Store a
plain function's locals in an array indexed by symbol number instead, and
build a dictionary only when `locals()`, a frame object or a traceback asks
for one: optimized locals are already snapshots. Cells, `del`, generator
suspension, `exec` with explicit locals and frame introspection must keep
their current behavior.

Expected gain: 20 to 30 percent on call-heavy programs (`fib`, `classes`,
`generators`).

Measured so far: a fresh environment already places parameters first and
then the other locals in symbol order, and each name node caches its entry
position, so reads are nearly array reads. The cost is in building and
releasing the environment value per call: in `fib(32)`, call setup and
teardown take about a fifth of the time and name resolution about a sixth.
Writing entries directly instead of through `map_append` gained nothing; the
win needs the environment itself to stop being a full map value per call.

### Compiled dispatch

Ordinary code is evaluated by `eval`, a switch over node kinds called
recursively, with a stack-depth probe and step bookkeeping per node. Compile
each body once into a form that dispatches directly: first a handler chosen
per node at compile time, then possibly a register bytecode. The generator
machine already runs an instruction list that borrows tree nodes; suspended
bodies must keep heap-owned operand and cleanup stacks visible to the cycle
collector, and instructions must keep borrowing nodes from the retained
source unit.

Expected gain: two to three times on interpreter-bound programs. Largest and
riskiest change; measure it separately from the steps above.

First stage done: nodes marked `F_OPERATOR` at compile time (arithmetic, a
single comparison or an index on literal or name operands) skip dispatch
when `tick` has only the line to record, which took `fib` down 9 percent and
`nbody` 10. Extending the operands to attributes of plain instances helped
`classes` (6 percent) but slowed `nbody` and `fib` by 2 to 5 percent through
code layout, so it was left out. Any handler added to `eval` must keep its
stack frame small: `eval` sits on every level of Python recursion, and the
recursion spec test runs within 4 MiB of native stack under ASan.

### Smaller values

Every value has one size, 216 bytes, large enough for a dictionary, class or
instance. An int needs about 48. This is why `sort` and `dicts` use two to
three times CPython's memory. Allocate each value at the size its type needs;
the tuple cache, the spare-value list and every in-place retyping of a value
must follow.

### Considered and set aside

- Leaving ints, floats and strings off the context's list of all values, as
  CPython leaves them untracked: the list also backs the live-value count
  that the C API reports, object walks and shutdown, so it is not only a
  collector detail.
- Inlining the reference-count release: measured twice, no gain beyond noise.
