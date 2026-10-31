# Metering

Design for the budgets the engine itself enforces on a context: work, memory
and time. It is the first part of the [sandboxed runtime](../ROADMAP.md#sandboxed-runtime).
Section 1 describes what existed at 0.4.0; section 6 says which steps are
done since.

A budget answers one question for the host: will this call come back, and
how much will it have taken? It does not decide what code may reach, which
is the runtime policy's job.

## 1 Where it stands

`spy_set_step_limit` counts evaluated nodes and some native work. The
`spy-worker` process adds a memory limit by renaming the engine's `malloc`
family to a counting allocator at compile time, and the bindings enforce a
timeout by killing the worker. A probe against `libspy.a` (Apple M2, `-O2`,
step limit 1,000,000) shows what that leaves open:

| Program | Result |
| --- | --- |
| `while True: pass` | stopped |
| `x = sum(range(10**8))` | stopped: iterator steps are counted |
| `x = sorted(range(10**7))` | stopped |
| `s = 'a' * 10**8` | completes: 100 MB, no step counted |
| `x = [0] * 10**8` | completes: 800 MB, no step counted |
| `x = 7 ** 3000000` | completes after 0.95 s within the limit |

Four further problems:

- **Cost.** A context with any step limit leaves `tick`'s fast path, so
  every node goes through `tick_full`. A program of `fib(27)` and a
  3,000,000-iteration loop takes 0.091 s unlimited and 0.142 s with a
  limit it never reaches: 56% slower. A sandbox pays most.
- **Refill.** The count is reset only by `spy_eval` and `spy_exec`, not by
  `spy_call`. After an evaluation exhausts it, every `spy_call` fails at
  once; without one, a host can make 999 calls of `def g(): return 1`
  under a limit of 1,000 and then none.
- **Memory is outside the engine.** Only the worker counts memory, through
  a build-time rename that `tests/oom.c` repeats for another purpose. An
  embedder linking `libspy.a`, as the Rust and Go crates do, has no memory
  limit, and an exhausted allocation raises a `MemoryError` the program can
  catch and continue past.
- **A timeout loses the runtime.** The worker is killed, so every value and
  global in it is gone, and the host must start a new one.

What does work: exhausting the step limit is already sticky. Once the
count passes the limit every node fails, so an `except BaseException:`
handler or a `finally` body fails at its first statement and the program
cannot continue. The design below keeps that and makes it the rule for
every budget.

## 2 Goals

1. A host can bound the work, the memory and the time of every call into a
   context, and no program can lift or evade a bound.
2. A stop leaves the context usable: the next call runs normally.
3. A context without budgets runs as fast as before, and one with budgets
   within noise of it.
4. Every native operation whose work grows with its operands is metered;
   the test suite and the fuzzers find one that is not.

Out of scope: rolling back what a program did before it was stopped (that
is snapshots), the C stack (already bounded by the recursion limit and the
stack guard), and work done inside host functions, which is the host's.

## 3 Design

### 3.1 The stop rule

A context is *stopped* when a budget runs out or the host interrupts it.
While stopped, every step and every unit of native work fails with the
stop's exception, so no handler, `finally` body, `__exit__` or generator
cleanup runs past its first step, and native code that swallows an
exception (`hasattr`, a comparison inside a dictionary lookup) meets the
stop again at its next unit. Unwinding still builds the traceback; it
needs at most one entry per frame, bounded by the recursion limit.

The outermost call into the engine returns the error. The next outermost
call clears the stop and refills the budgets. An *outermost call* is a
call of `spy_eval`, `spy_eval_interactive`, `spy_exec`, `spy_exec_module`,
`spy_call` or `spy_call_keywords` made while no other is active; a host
function that calls back into the engine shares its caller's budget.
Other API functions that may run Python code through a special method,
such as `spy_repr`, spend what the last outermost call left. Inside the
engine, calls go through a private `call`, so a public function always
means the host.

Finalizers, weak-reference callbacks and generator cleanups that become
due while stopped stay queued and run at the first statement boundary of
the next outermost call, under its budget. They are not dropped and do not fail.

The host learns why a call failed from the context, not from the error
type: a program can raise `RuntimeError("execution step limit exceeded")`
itself.

### 3.2 Steps

A step is a unit of work with a bounded cost. The engine spends steps at
the points through which all unbounded work passes:

- one per Python function call, including calls made from native code
  (`__init__`, `sorted` keys, comparison callbacks), and one per 8 nodes
  of the body the frame runs: a module, class or function body, and of a
  class body again when the class is built;
- one per iteration of a `for` or `while` loop, per item of a
  comprehension or generator expression, and per item a native loop takes
  from an iterator;
- in native code, in proportion to what an operation produces or visits:
  one per 64 bytes a block of 4 KiB or more grows by, one per mapping
  lookup of `str.translate`, one per 8 digits of float formatting, one
  per 64 elements, digits or
  bytes compared, searched, hashed or moved (per 16 entries for hash
  lookups), and for an algorithm worse than linear (multiplication,
  division, base conversion, substring search), one per 1024 digit
  products or bytes compared in its inner loop;
- in the parser, one per 64 bytes of source, so `exec` of a large string
  is metered like any other text.

Straight-line code runs at most once between two steps, so nodes are not
counted as they run; charging a body's length when its frame is entered
bounds a call of a long function or `exec` of a long code object. A step's
cost on the reference machine should stay under one microsecond: a budget
of 1,000,000 steps returns within about a second.

Allocation is where most native work shows: repetition, `join`,
`replace`, formatting widths, copies and shifts all produce what they
cost, so the allocator spends their steps (3.3) and none of them needs its
own. Operations that only read, comparisons, searches, hashing, and
predicates such as `isidentifier`, spend where they loop. Work of bounded
size, such as a comparison of two existing strings, may spend after the
fact; work that can grow faster than its operands spends before or during
it.

The count is one countdown in the context, `fuel`, spent through one
inline function, `spend`; an outermost call sets it to the limit, or to
`SIZE_MAX` without one. Calls and loop passes already test for a trace
function at the points where a step is spent. One flag, `watch`, set
while a trace or profile function or a step limit is present, replaces
those tests, so the step costs nothing without a limit. The step test
left `tick`, so a limited context runs on the same fast path as an
unlimited one, and a spent budget still fails every tick. The scattered
`c->step_limit && ++c->steps > c->step_limit` tests became `spend` calls,
and a bulk copy of a list or tuple spends its length at once.

The interrupt callback (3.4) is polled as QuickJS polls its interrupt
handler, at calls and backward jumps: when `fuel` has fallen 4,096 steps
past the last poll, a Python call, an item a native loop takes from an
iterator, or the statement after a loop pass asks the host. A loop pass
only marks its frame not quiet, so the next `tick` takes its slow path
and polls there; `spend` keeps a slow path that always stops, which
compiles to a tail call. A version whose `spend` refilled the countdown
from a reserve and continued cost 0.1 to 0.4% of the instructions of
every benchmark program, as did a poll called from the loop pass itself;
the interrupt now costs no more than a step limit.

### 3.3 Memory

The engine counts the bytes it holds and refuses an allocation that would
take the count past the limit, which stops the context with `MemoryError`.
Unlike steps, memory is a level, not a spending: it is not refilled per
call, and a call starting above the limit stops at its first allocation.

Every engine allocation goes through `mem_malloc`, `mem_realloc` and
`mem_free`, over one function, `mem_block`. A block carries a header
holding its size and its context, so a free needs neither. While watched,
a block of 4 KiB or more spends a step per 64 bytes it grows by; a smaller
one costs no more than the step that asked for it. Value pools are counted whole (16 KiB
each) when taken from and returned to the system. Memory that crosses the
host boundary stays on plain `malloc` and `free`: sources from the module
loader, lines from `input()`, and paths from `realpath`, which a mount
copies into engine memory.

The header costs glibc about 45 instructions an allocation, more than the
benchmark programs can absorb. As values already wait in spare lists,
blocks have room for a multiple of 16 bytes, and released blocks of up to
256 bytes wait in the context for the next allocation of their size, as
pymalloc keeps its small blocks; programs that allocate many small blocks
got faster, not slower. Waiting blocks are not counted as held.

While stopped, allocations are not refused: unwinding needs them and is
bounded, and native code cannot run on because every unit of its work
fails (3.1).

This removed the worker's renaming of `malloc`, `calloc`, `realloc`,
`free`, `realpath` and the pool functions, and its counting allocator: the
worker sets the limit through the API instead. `tests/oom.c` keeps its
renaming; it injects failures rather than counting.

### 3.4 Time

The engine reads no clock. The host installs an interrupt callback, which
the engine calls at the first call, statement or native iteration after
every 4,096 steps (3.2); a nonzero return stops the context. A single
native operation, such as one multiplication, does not poll; its steps
bound its time. A host reads its own clock there, so wall time, CPU time and a
cancel button are the same mechanism, and the engine stays free of clocks
and threads, as bare metal needs. This is QuickJS's
`JS_SetInterruptHandler`.

The worker uses it for the bindings' `timeout`: the operation stops, the
worker reports it, and the runtime stays usable. The worker's clock stops
while it waits for the parent, so host functions are not counted. Killing
the worker remains as the backstop for a worker that does not answer
within a grace period of one second, which only a single native operation
of that length, a metering bug or a hanging host function can cause.

### 3.5 Output

There is no output budget. Output already passes through the host's
`SPYWrite` callback, which can count bytes and refuse a write; it is
metered there, by the code that knows where the bytes go.

### 3.6 Interface

```c
/* Steps for each outermost call; zero means unlimited. */
void spy_set_step_limit(SPYContext *, size_t);
/* Bytes the engine may hold; zero means unlimited. */
void spy_set_memory_limit(SPYContext *, size_t);
size_t spy_memory_used(const SPYContext *);
/* Polled after every 4096 steps; nonzero stops the context. */
typedef int (*SPYInterrupt)(void *);
void spy_set_interrupt(SPYContext *, SPYInterrupt, void *);
/* Why the last outermost call stopped, or zero. */
enum { SPY_STOP_STEPS = 1, SPY_STOP_MEMORY, SPY_STOP_INTERRUPT };
int spy_stopped(const SPYContext *);
```

`spy_set_step_limit` keeps its name; its unit changes from nodes to steps.
Budgets are set only through the C API. No primitive in `_spy` reads or
changes them, since any program can import `_spy` where the standard
layer is registered.

The exception keeps today's classes: `RuntimeError` ("execution step limit
exceeded", "execution interrupted") and `MemoryError` ("memory limit
exceeded"), with the file and line of the step that stopped.

### 3.7 The standard

PLS-315 is not changed. A stop is the host ending an evaluation, as ending
the process would, not an operation of the language; conformance item 5
(storage exhaustion raises the specified exception) still holds for an
allocation the system refuses. The manual documents budgets with the rest
of the C API.

## 4 Bindings

The worker protocol gains no message; an error reply gains the stop
reason, `stop`, and `INIT` the `timeout` option. `step_limit` and
`memory_limit` map to the setters, and `timeout` to an interrupt callback
reading a monotonic clock. In the Python, Rust, JavaScript and Go packages
a stop raises the existing `Timeout` or `Error`, with the runtime still
open ([packaging/protocol.md](packaging/protocol.md) §10).

## 5 Evidence

- **C API tests** (`tests/api.c`), one group per budget: the program is
  stopped; `except BaseException` and `finally` bodies do not run; the next
  call succeeds; `spy_call` refills; a host function calling back shares
  the budget; `spy_stopped` is zero when the program raises the same
  exception itself; `spy_memory_used` returns to its baseline after a
  stopped program's values are collected; queued finalizers run in the
  next call.
- **Metering probe** (`tests/metering.c`): the table of section 1 grew
  into a list of adversarial programs, one or more for every family of
  native operation (repetition, `join`, search, `count`, `replace`,
  formatting widths, integer power, division and conversion, sorting,
  comparison and hashing of large containers, moving list elements, long
  bodies, `exec` of large source). Most repeat one operation forever; under
  a budget of 1,000,000 steps each must be stopped within its time, not
  completed or interrupted by its watchdog, an interrupt callback. The
  probe reports the slowest, about 1 s on the reference machine.
- **Fuzzing**: every target runs under a step limit that ends it far
  within libFuzzer's `-timeout=10`, which `make fuzz` no longer ignores, so
  any unmetered operation is a finding; each one becomes a probe program.
  The eval and compile targets also run under a memory limit.
- **Performance**: no benchmark program slower than before, with and
  without a limit, measured as every change is (`docs/optimization.md`).
  The 56% cost of a limit in section 1 should disappear.
- **Bindings**: the timeout tests check that the runtime survives a timeout.

## 6 Order of work

Each step is one commit that keeps every suite green.

1. Done: `spend` replaces the step count; outermost calls refill; the
   limit leaves `tick`. This fixed the refill bug and the 56% cost of a
   limit, with no benchmark program slower.
2. Done: the stop rule, with a stopped flag, `spy_stopped`, and finalizers
   queued while stopped.
3. Done: `mem_block` and the memory limit, with the worker's renaming
   removed; allocation spends steps, and native operations that only read
   spend where they loop, each family with its probe programs. Allocation
   came first since it meters most native work at once. Every benchmark
   program is as fast or faster.
4. Done: the interrupt callback, polled at calls, native iterations and
   statements after loop passes, and the metering probe in `make test`
   with an interrupt as its watchdog. An interrupt costs no more than a
   step limit.
5. Done: the worker's timeout uses the interrupt, error replies carry the
   stop reason, and the four packages keep a timed-out runtime open; the
   manual names what metering covers and what it does not.

## 7 Borrowed

- QuickJS: `JS_SetMemoryLimit` and the malloc state counting every block,
  `JS_SetInterruptHandler` polled on a countdown, and uncatchable errors.
- Wasmtime: fuel, counted down inline and checked at function entries
  and loop headers.
- CPython: the eval breaker, one word tested on the hot path for all
  pending work.
