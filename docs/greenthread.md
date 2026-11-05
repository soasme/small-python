# Green threads

This file is a proposal. Nothing in it is implemented. It describes how one
context could run several Python threads on one operating-system thread,
switching between them inside the engine, and what that would cost. The
TLA+ model `tests/tla/SpyGreenThreads.tla` checks the scheduler it
describes.

## 1 Purpose

Python programs use threads for two things: to wait for several slow
operations at once, and to compute in parallel. Green threads give the
first without the second. They need no operating-system threads, no
atomic operations and no locks inside the engine, so they work where the
engine runs today: in WebAssembly without `SharedArrayBuffer`, on edge
runtimes without threads, on bare metal, and inside a sandboxed worker.

The case that matters most is a host whose functions are slow: a model's
tools, network requests, a database. Ordinary threaded code such as

```python
from threading import Thread
results = [None] * len(urls)
def get(i, url):
    results[i] = fetch(url)          # a host function
threads = [Thread(target=get, args=(i, u)) for i, u in enumerate(urls)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

then issues every `fetch` before the first one answers, without `async`
and `await` spreading through the program. The same threads can be
snapshotted while they wait, which a host call blocking the C stack does
not allow (ROADMAP, *Snapshot, fork and resume*).

## 2 Today

- A context runs one thread of Python code. Python code cannot start a
  thread: the core has no `_thread` or `threading`.
- Every host service (`SPYWrite`, `SPYReadLine`, the module loader, native
  functions) is a synchronous C call: while it runs, the context waits.
- Generators, coroutines and asynchronous generators run on an instruction
  machine whose operand and block stacks are heap-owned, so they suspend at
  `yield` and `await` without holding the C stack. Everything else is a
  C frame: a Python call recurses through `call` and `eval`, guarded by
  `deeper`, and C calls back into Python for `__init__` from a class call,
  special methods called by operators, `__next__` in a `for` loop, sort
  keys, comparison and hash callbacks inside containers, descriptors,
  `__del__` and host callbacks.
- `watch` is the one word the interpreter's calls and loop passes test.
  When it is set they take a slow path (`watched_call`, `watched_pass`)
  that spends steps and polls the interrupt; when it is clear they pay
  nothing more.

A thread can only be suspended where nothing on the C stack belongs to it.
Today that is nowhere outside a generator's own frame.

## 3 Design

### 3.1 Parked and pinned threads

Every thread's Python frames live on the heap, in its own frame stack.
A thread is **parked** when all it holds is on the heap; it can stop and
resume at any instruction boundary, and it resumes above whatever the C
stack holds. A thread is **pinned** while C code sits between its frames:
a native function that called Python, a sort key, a `__eq__` called by a
dictionary. Its C frames stay on the C stack, and it can resume only by a
C return into them.

C11 cannot switch or copy C stacks, so the engine keeps one C stack and
one rule: **a pinned thread runs only from the top of the C stack.** When
a pinned thread waits, other threads run above its C frames; it resumes
when they have parked again. A pinned thread is never preempted, because a
preemption would bury it under another thread's frames for no reason the
program gave.

### 3.2 Heap frames for ordinary calls

Pinning is rare only if ordinary calls do not recurse in C. That is step 3
of *Toward bytecode* in [optimization.md](optimization.md): a call to a
Python function pushes a frame and the machine loop continues; a return
pops it. Its prototype passes every spec test but has not yet measured
faster than the walker, so green threads wait for it. Without it every
thread is pinned at every call, and the scheduler can only nest threads.
That deadlocks most programs: a producer that waits for its consumer, and
lies under it on the C stack, cannot resume while the consumer waits for
the next item.

After flat calls, the C re-entries that matter most move onto the
machine, in this order, each measured like any optimization:

1. `__init__` and `__new__` from a class call;
2. special methods that operator instructions call (`__add__`, `__eq__`,
   `__getitem__`, ...), `__iter__` and `__next__` in `for`, `__enter__`
   and `__exit__` in `with`;
3. descriptors and `__getattr__` in attribute access;
4. builtins that take callbacks (`sorted` and `list.sort` keys, `map`,
   `filter`, `min` and `max` keys), rewritten as resumable natives: the
   native's state lives in a heap object and the callback's result is
   delivered to a continuation function, so no C frame waits for it.

What remains pinned: hash and equality callbacks inside dictionary and set
operations, `__del__`, weak reference callbacks, `repr` recursion, and
host callbacks into the engine.

### 3.3 Thread state

A thread owns the fields that today belong to the one thread of a
context: the pending error and its traceback, the frame stack
(`frames`, `py_depth`, `eval_env`), the handled and inherited exceptions,
`repr_stack`, the recursion depth and the trace and profile functions.
A switch saves them into the outgoing thread and loads the incoming one's.
Only one thread runs at a time, so the interpreter's hot paths keep reading
the context's fields as they do now, and reference counts, allocator lists,
lazy caches and the class lookup cache need no change.

The step budget, memory and output limits, the interrupt, the module cache
and the collector stay per context: a thread is not a sandbox.

### 3.4 Switching

A thread stops running when it:

- finishes, or raises out of its function (the exception is reported as an
  unraisable one and the thread ends);
- waits: on a lock, on another thread's end, or on the host (3.5);
- is preempted: while two or more threads are alive, `watch` is set, and
  at a call or loop pass a parked thread that has spent its slice of steps
  yields. The slice is counted in steps, not time, so a run with the same
  inputs switches at the same places and replays exactly.

A single thread pays nothing: `watch` is clear while only one thread is
alive, as it is today. A switch is never taken inside a C operation, so
every builtin operation (`list.append`, a dictionary store, `x[i] = v`) is
atomic with respect to other threads, and a generator resumed from two
threads still raises "generator already executing".

The scheduler chooses among the ready parked threads and, when the top of
the C stack is a ready pinned thread, that one. It prefers the top of the
stack, which keeps buried threads rare, and otherwise runs threads in the
order they became ready.

### 3.5 Waiting for the host

A native function that starts a slow host operation returns
`spy_wait(c, ticket)` instead of a value. The calling thread waits; when
the host calls `spy_settle(c, ticket, value)` (or `spy_settle_raise` with
an exception), that value becomes the call's result. A parked thread waits
on the heap; a pinned one waits in place while other threads run above it.

When no thread can run and some ticket is outstanding, the engine calls the
host's idle callback, which blocks until it can settle at least one ticket.
Timed waits (`acquire(timeout=...)`, a sleep) are tickets the host settles
when the time passes; the engine has no clock. A host without an idle
callback cannot defer results, and `spy_wait` fails with RuntimeError.

The existing synchronous services stay as they are: a native that does not
call `spy_wait`, `print`, `input` and the loader block the whole context.

### 3.6 When nothing can run

When no thread can run and no ticket is outstanding, no thread will ever
run again. Instead of hanging the host, the wait on top of the C stack
(or the outermost thread's, when the stack holds no pinned thread) raises
RuntimeError:

- "deadlock: no thread can run" when every unfinished thread waits;
- "a ready thread is pinned under another thread's native call" when a
  ready thread lies under another thread's C frames.

The second is spy's own limit, where CPython would continue. It can only
happen when a thread blocks inside a C callback (the model checks this):
for example, a sort key waits for a lock, and the thread holding it
releases it from inside its own sort key and then waits there for the
first thread.

### 3.7 The outermost call

The thread that runs `spy_eval`, `spy_exec` or `spy_call` is the outermost
thread. The call returns once that thread has finished and no other
thread's C frames remain on the stack. Other threads stay parked in the
context and run again during the next outermost call; the host decides
when to make one, as it does today. `spy_context_free` releases parked
threads without running their `finally` blocks.

A stop (step budget, memory or output limit, interrupt) ends the outermost
call, as now; parked threads keep their state.

### 3.8 Collection

An unfinished thread is a root: its frame stack is traced as a suspended
generator's is, and a thread waiting on an unreachable lock is never
collected. A finished thread releases its frames. Finalizers and weak
reference callbacks run at the next statement boundary of whichever thread
is running.

### 3.9 Interface

`spy.h` gains `spy_wait`, `spy_settle`, `spy_settle_raise`,
`spy_set_idle` and a limit, `SPY_LIMIT_SWITCH`, the steps of a slice.
`spy_init_primitives` gains what a host module cannot be written without:
start a thread, a lock (acquire with an optional ticket for the timeout,
release, locked), wait for a thread, the current thread's identifier, and
yield. A `_thread` module in the standard layer (`spy-std.c`) presents
them as CPython's; it is a new library module and is added only once the
user asks for it. `threading` is CPython's pure-Python module over
`_thread`, and stays outside the core.

The language standard gains a clause in Annex B for threads as a host
hook: when a switch may happen, the atomicity of builtin operations, and
the RuntimeError of 3.6.

## 4 Verification

- **The scheduler model.** `tests/tla/SpyGreenThreads.tla` models parked
  and pinned threads, locks with direct hand-off, host tickets, the
  RuntimeError of 3.6 and the outermost call's return. TLC checks that a
  running pinned thread is always on top of the C stack, so its C returns
  land in its own frames; that no waiter sits on a free lock; that a
  thread lies under another's C frames only because it waited while
  pinned; and that the scheduler never stops without either running a
  thread, waiting for the host, raising or returning. Each check fails
  when the rule behind it is removed: resuming a thread under the top,
  freeing a lock that has waiters, preempting a pinned thread, or leaving
  out the RuntimeError.
- **Spec tests** for every message and switch point of the Annex B
  clause, run on spy and, where CPython's `_thread` agrees, on the oracle.
- **Ownership and sanitizers.** Threads that end, raise, wait forever and
  are freed with their context, under AddressSanitizer and the
  allocation-failure tests (`tests/oom`); a fuzz target that starts and
  joins threads from generated programs.
- **Determinism.** The same program and inputs give the same output for
  every slice length, and the same switch points across runs.
- **Measurement.** A single-threaded program must not slow down: every
  step is measured against the commit before it, as in
  [optimization.md](optimization.md). A switch and a host wait are
  measured on their own and reported in [benchmark.md](benchmark.md).

## 5 Order

1. Flat calls (3.2), already planned for speed; nothing here starts before
   they land without a slowdown.
2. The thread state and switching (3.3, 3.4), with locks and the model's
   rules, behind the primitives. Preemption comes with it.
3. Host tickets (3.5) and the idle callback, in C and then in the
   JavaScript, Python, Go, Java and Rust bindings.
4. The C re-entries of 3.2, one at a time, each only when it measures no
   slower.
5. `_thread`, when it is asked for.

Steps 1 to 3 already serve the case of section 1. Step 4 narrows the
RuntimeError of 3.6.

## 6 Left out

- **Switching C stacks.** Copying a thread's C stack aside, or giving each
  thread its own with `ucontext`, `setjmp` and `longjmp` or assembly, would
  remove pinning altogether. None of it is C11: `ucontext` has left POSIX,
  and jumping into another stack is undefined behavior. The engine stays
  portable C.
- **One operating-system thread per green thread, taking turns under one
  lock.** It needs threads, which the targets of section 1 lack, costs a
  system call per switch, and its switch points depend on timing, so runs
  cannot be replayed.
- **Cooperative switching only.** Without preemption, a thread that loops
  without waiting starves the others, which Python programs written for
  threads do not expect. Preemption costs a single thread nothing (3.4).
- **Parallel threads.** Running threads at once on several processor cores
  in one context needs atomic reference counts, locked containers and a
  collector that stops every thread. Green threads share their thread
  state (3.3) and Python interface (3.9) with that design, so programs
  written for one run on the other, but they do not depend on it.
  Separate contexts already run in parallel.

## 7 Sources

Parked and pinned threads follow the distinction between virtual threads
and pinned carriers in Java's Project Loom, and between soft and hard
switching in Stackless Python. Resumable natives follow the continuation
functions of Lua 5.2's `lua_callk`. Step-counted preemption follows
Erlang's reductions.
