# Threads

Python threads come from `_thread`, the first module of the C standard
library in `stdlib/`. Each Python thread runs on a system thread of its own,
and the threads of one context take turns at it: one runs Python code at a
time, as in CPython with its global interpreter lock. The core supplies the
two things the module cannot be written without, a thread state and a switch
callback (section 5); everything else is in `stdlib/_thread.c`.

## 1 The module

`_thread` has CPython 3.15's interface for what `threading` needs:
`start_new_thread` (and `start_new`), `start_joinable_thread` with its
`_ThreadHandle`, `allocate_lock` (and `allocate`), `lock` (`LockType`),
`RLock`, `get_ident`, `get_native_id`, `_count`, `stack_size`, `exit` (and
`exit_thread`), `error`, `TIMEOUT_MAX`, `daemon_threads_allowed`,
`_get_main_thread_ident`, `_is_main_interpreter`, `_make_thread_handle` and
`_shutdown`. Its messages are CPython's, and `tests/thread_probe.py` checks
them against the pinned CPython.

Not provided yet: `interrupt_main`, `_local`, `set_name` and `_get_name`,
`_excepthook` and `_ExceptHookArgs`, `_NAME_MAXLEN`. `threading` is not
shipped; CPython's `threading.py` falls back to Python code for `_local` and
the excepthook. A lock and an `RLock` are Python classes over a native
primitive, so `dir()` of one also lists `_op` or its fields, and the least
`stack_size` is 32768 bytes on every platform.

An exception that leaves a thread's function goes to `sys.unraisablehook`
with "Exception ignored in thread started by" and the function; `SystemExit`
ends the thread silently.

## 2 Taking turns

The thread holding the context holds the **turn**. Turns are handed on in
the order threads asked for them: a thread draws a ticket and waits until
the module serves it, all under one mutex, so everything the last thread did
to the context happens before the next one runs (C11's and POSIX's
happens-before through a mutex).

- **Taking a turn** swaps the thread's state into the context
  (`spy_thread_swap`). **Giving it** swaps the state out and serves the next
  ticket.
- **A lock** that is free is taken at once. One that is held makes the
  thread give its turn, wait for the lock without it, take the lock, and
  then take a turn again behind the threads already waiting.
- **The switch.** While a started thread lives, the module sets the switch
  callback (`spy_set_switch`). The engine calls it after every 4096 steps or
  so; it gives the turn and takes it again when another thread waits and
  this one has held it for 5 ms, CPython's default switch interval.
- **A started thread** takes its first turn, calls its function, and at the
  end frees its state and serves the next ticket. The last one to end clears
  the switch.
- **The host's thread**, the one that imported the module, holds the turn
  whenever the host is outside the engine. Other threads run only during the
  host's calls: in the `spy` command, while the program runs.
- **Freeing the context** closes the module: every thread still waiting,
  for a lock or a turn, leaves its system thread without touching the
  context, whose memory goes with the context, and the module's own memory
  goes once no system thread of it remains.

Blocking host services keep the turn: `print`, `input`, the module loader
and a host function that waits block every thread of the context. A
deadlock between Python threads waits for ever, as under CPython.

## 3 What Python code sees

A switch happens only in the tick before the engine evaluates the next
expression or statement, where a finalizer may run anyway. A builtin
operation is never interleaved with another thread: `list.append`, a
dictionary store, `sorted` without a key, `x[i] = v`. Python code called
from a builtin (a sort key, `__eq__`) can be switched away from, as in
CPython.

The threads share the context's limits. The outermost call's step budget,
memory limit and output limit count every thread's work, and a stop or an
interrupt ends the outermost call while the other threads keep their state.
A thread state starts inside a call, so a started thread's calls never
refill the budget. Trace and profile functions are the context's, not each
thread's.

Each thread has its own recursion depth, C stack measure, pending
exception, handled exception (`sys.exception()`) and running frames. A
started thread's system stack is the engine's stack limit
(`SPY_LIMIT_STACK`) and a megabyte to spare, or `stack_size()` when that is
larger.

## 4 Linking

`stdlib/_thread.c` is one source in the native-module form (manual 3.4.9):

- **Static.** `make` builds `stdlib/lib_thread.a`. A host links it with
  `-pthread` and registers it with `spy_new_module(c, "_thread",
  spy_init__thread)`, declared in `stdlib/spy-stdlib.h`. The `spy` command
  links it so. `spyc` takes `stdlib/_thread.c` or `stdlib/lib_thread.a` as
  a C or archive module, with `-- -pthread` where the C library needs it.
- **Dynamic.** `make` builds `stdlib/_thread.so`, which a host loads with
  `spy_std_load_native(c, "_thread", path)`; a host that searches beside a
  program's sources, as the `spy` command does, finds `_thread.so` there.

Windows builds use the system's threads instead of POSIX ones. WebAssembly
builds have no `_thread`.

## 5 The core's part

```c
SPYThread *spy_thread_new(SPYContext *);
void spy_thread_swap(SPYContext *, SPYThread *);
void spy_thread_free(SPYContext *, SPYThread *);
void spy_set_switch(SPYContext *, SPYSwitch, void *);
```

A thread state holds the fields of `SPYContext` that belong to one thread:
the pending error with its message, filename, line and traceback, the
running frames and recursion depth, the handled and inherited exceptions,
the current environment, the C stack measure, `repr`'s recursion guard,
whether a trace function runs, and how deep in host calls the thread is.
`spy_thread_swap` exchanges them with the context's; reference counts,
allocator caches and lookup caches stay the context's, because one thread at
a time uses them. A state still held goes with the context.

The switch callback is polled with the interrupt. The poll only marks the
switch due; the next tick calls it, so a poll inside a builtin operation does
not interleave another thread. While no switch is set, the engine does no
more work than before: the callback is tested only on the slow path that
the interrupt and limits already take.

## 6 Evidence

- `tests/std.py` runs `tests/thread_probe.py` under `spy` and under the
  pinned CPython 3.15 and requires the same output: the module's names and
  messages, lock and `RLock` semantics, threads that start, end, raise and
  are joined, a contended counter, a thread that never waits, a timed wait
  and `_shutdown`.
- `tests/api` checks that a swap sets aside one thread's pending error and
  frames and brings them back, that a builtin operation finishes before the
  switch runs, and that a state left to the context is freed with it.
- `tests/threads` loads `stdlib/_thread.so` into four contexts at once, runs
  Python threads in each and frees each context while one of its threads
  still waits; under ThreadSanitizer it reports any context state a turn
  leaves unordered.
- `tests/tla/SpyThreads.tla` models the module's contract with its host:
  one thread at a time uses the context, holding the turn with its own state
  in it; the host holds the turn outside the engine; the switch is set
  exactly while a started thread lives; nothing touches the module once it
  is freed; and threads that release what they take run on until the
  context is freed.
- [benchmark.md](benchmark.md) records what a thread, a lock and a switch
  cost.

## 7 Left out

- **Threads without system threads.** WebAssembly without threads, edge
  runtimes and bare metal could still run Python threads if a thread could
  stop at any instruction with its frames on the heap. Python calls recurse
  in C today, so that waits for calls without C recursion (*Toward bytecode*
  in [optimization.md](optimization.md)); a thread inside C code that called
  Python (a sort key, `__eq__`) would still be pinned to the C stack. C11
  cannot switch C stacks portably.
- **Parallel threads in one context.** Running Python code on several cores
  at once needs atomic reference counts, a lock per container and a
  collector that stops every thread. Separate contexts already run in
  parallel.
- **Releasing the turn around host calls.** A host function that waits
  could give the turn while it waits, as CPython's I/O releases its lock.
  That needs an interface for host functions to do so safely; until then
  they block the context.

## 8 Sources

The turn follows CPython's global interpreter lock and its switch interval
(`sys.setswitchinterval`); the module's interface and messages are
CPython's `Modules/_threadmodule.c`. Tickets served in order are Lamport's
bakery algorithm.
