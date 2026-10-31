# Metering

Design for the budgets the engine itself enforces on a context: work, memory
and time. It is the first part of the [sandboxed runtime](../ROADMAP.md#sandboxed-runtime)
and is not implemented yet; section 1 describes what exists at 0.4.0.

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
3. A context without budgets runs as fast as today, and one with budgets
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
  (`__init__`, `sorted` keys, comparison callbacks);
- one per iteration of a `for` or `while` loop and per item of a
  comprehension or generator expression;
- in native code, in proportion to what an operation visits or produces:
  one per element, per 32-bit digit, or per 64 bytes of text, and for an
  algorithm worse than linear (schoolbook multiplication, substring
  search), in proportion to its inner loop;
- in the parser, one per 64 bytes of source, so `exec` of a large string
  is metered like any other text.

Straight-line code is bounded by its own length, so nodes are no longer
counted. A step's cost on the reference machine should stay under one
microsecond: a budget of 1,000,000 steps returns within about a second.

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

The interrupt callback (3.4) will extend `spend`'s slow path into a
`refuel` that calls the host and sets the countdown to the smaller of the
remaining budget and the interrupt period.

### 3.3 Memory

The engine counts the bytes it holds and refuses an allocation that would
take the count past the limit, which stops the context with `MemoryError`.
Unlike steps, memory is a level, not a spending: it is not refilled per
call, and a call starting above the limit stops at its first allocation.

Every engine allocation goes through one pair, `mem_alloc(c, n)` and
`mem_free(p)`, with `mem_realloc` beside them. A block carries a header
holding its size and its context, as the worker's counting allocator
already does, so a free needs neither. Value pools are counted whole
(16 KiB each) when taken from and returned to the system. Memory that
crosses the host boundary stays on plain `malloc` and `free`: sources from
the module loader, lines from `input()`, and paths from `realpath`.

While stopped, allocations are not refused: unwinding needs them and is
bounded, and native code cannot run on because every unit of its work
fails (3.1).

This removes the worker's renaming of `malloc`, `calloc`, `realloc`,
`free`, `realpath` and the pool functions, and its counting allocator: the
worker sets the limit through the API instead. `tests/oom.c` keeps its
renaming; it injects failures rather than counting.

### 3.4 Time

The engine reads no clock. The host installs an interrupt callback, which
`refuel` calls at least once every 4,096 steps; a nonzero return stops the
context. A host reads its own clock there, so wall time, CPU time and a
cancel button are the same mechanism, and the engine stays free of clocks
and threads, as bare metal needs. This is QuickJS's
`JS_SetInterruptHandler`.

The worker uses it for the bindings' `timeout`: the operation stops, the
worker reports it, and the runtime stays usable. Killing the worker
remains as the backstop for a worker that does not answer within a grace
period, which only a metering bug or a hanging host function can cause.

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
/* Called at least every 4096 steps; nonzero stops the context. */
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
reason. `step_limit` and `memory_limit` map to the setters, and `timeout`
to an interrupt callback reading a monotonic clock. In the Python, Rust,
JavaScript and Go packages a stop raises the existing `Timeout` or `Error`,
with the runtime still open. [packaging/protocol.md](packaging/protocol.md)
and each package's document are updated in the same change.

## 5 Evidence

- **C API tests** (`tests/api.c`), one group per budget: the program is
  stopped; `except BaseException` and `finally` bodies do not run; the next
  call succeeds; `spy_call` refills; a host function calling back shares
  the budget; `spy_stopped` is zero when the program raises the same
  exception itself; `spy_memory_used` returns to its baseline after a
  stopped program's values are collected; queued finalizers run in the
  next call.
- **Metering probe**: the table of section 1 grows into a list of
  adversarial programs, one or more for every family of native operation
  (repetition, `join`, search, `count`, `replace`, formatting widths,
  integer power, division and conversion, sorting, comparison and hashing
  of large containers, `exec` of large source). Under a budget of 1,000,000
  steps each must be stopped, not completed. The probe reports the largest
  time per step, which [benchmark.md](benchmark.md) records with the rest.
- **Fuzzing**: the eval target already runs under a step limit. Running it
  with libFuzzer's `-timeout=2` turns any unmetered operation into a
  finding; each one becomes a probe program.
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
3. Native operations spend steps, one family at a time, each with its
   probe programs.
4. `mem_alloc` and the memory limit; the worker's renaming is removed.
5. The interrupt callback; the worker's timeout uses it.
6. Bindings and their documents; the manual's statement that the runtime
   is not an isolation boundary is revised only for what metering covers.

## 7 Borrowed

- QuickJS: `JS_SetMemoryLimit` and the malloc state counting every block,
  `JS_SetInterruptHandler` polled on a countdown, and uncatchable errors.
- Wasmtime: fuel, counted down inline and checked at function entries
  and loop headers.
- CPython: the eval breaker, one word tested on the hot path for all
  pending work.
