# Threads

Python threads come from `_thread`, the first module of the standard library
in `stdlib/`. They are **virtual threads**:

- They all run on the host's system thread, the one that calls the engine.
- A thread switches only where it would block: waiting for a lock that is
  held, or joining a thread that has not ended. Nothing preempts a thread.

The module is Python (`stdlib/_thread.py`) with a C wrapper (`stdlib/_thread.c`).
The core has no thread support of its own, and the module needs none.

## 1 The module

`_thread` has CPython 3.15's interface for what `threading` needs:

- `start_new_thread` (and `start_new`), plus `start_joinable_thread` with its
  `_ThreadHandle`;
- `allocate_lock` (and `allocate`), `lock` (`LockType`) and `RLock`;
- `get_ident`, `get_native_id`, `_count`, `stack_size`, `exit` (and
  `exit_thread`);
- `error`, `TIMEOUT_MAX`, `daemon_threads_allowed`, `_get_main_thread_ident`,
  `_is_main_interpreter`, `_make_thread_handle` and `_shutdown`.

Its messages are CPython's, and `tests/thread_probe.py` checks them against
the pinned CPython.

Not provided yet: `interrupt_main`, `_local`, `set_name` and `_get_name`,
`_excepthook` and `_ExceptHookArgs`, and `_NAME_MAXLEN`. `threading` is not
shipped. CPython's `threading.py` falls back to Python code for `_local` and
for the excepthook.

Locks and `RLock`s are Python classes, so `dir()` of one also lists their
private fields. `get_native_id()` returns the thread's ident, since every
thread shares one system thread. `stack_size()` is stored and checked, but
no stack is allocated.

When an exception leaves a thread's function, it goes to
`sys.unraisablehook` with "Exception ignored in thread started by" and the
function. `SystemExit` ends the thread silently.

## 2 Switching

- **Starting** a thread queues it. It runs only once the running thread
  blocks. Queued threads start in the order they were started.
- **Blocking.** A thread that would block runs the first queued thread on
  top of itself, within its own call. When that thread ends, the blocked
  thread checks again, and repeats while threads remain queued. It goes on
  once the lock is free (taking it) or the joined thread has ended.
- **Nothing left to run.** A thread that would still block with no thread
  queued cannot be helped by any other thread:
  - a thread below it resumes only when this one ends;
  - an ended or never-started thread cannot release anything.

  So a timed wait (`acquire(True, t)`, `join(t)`) returns at once as timed
  out. A wait for ever raises `RuntimeError: cannot block: no other thread
  can run until this one ends`.
- **Resuming.** A thread under others resumes when the threads above it
  have ended. Threads that wait for each other therefore resume last first.
- **The host's call** returns when the main thread's code does. Threads
  still queued then never start. `_shutdown` (which `threading` calls at
  exit) joins the threads that are not daemons.

This is a long way from CPython's preempted threads:

- **No time slices.** A thread that never blocks keeps running, so a busy
  loop waiting for a flag that another thread sets never ends. Use a lock.
- **Nested resumption.** Two threads that hand a lock back and forth fail.
  The second one to block is above the first and cannot wait for it, so
  its wait raises. A producer that waits for a consumer it started fails
  the same way. Fan-out work joined by its starter, locks around critical
  sections, and waits that later threads satisfy all work as under CPython.
  `tests/thread_virtual.py` checks each case.
- **Cost of depth.** A thread running on top of others adds its frames to
  theirs. Its recursion depth counts theirs, and `sys._getframe()` walks on
  into the thread below, as from a callback. A thread that runs while the
  thread below it is in an `except` block sees that block's
  `sys.exception()` until it handles one of its own.
- **Determinism.** The order of a program's threads depends only on the
  program, never on timing.

## 3 Linking

`stdlib/_thread.c` is one source in the native-module form (manual 3.4.9),
and needs only the C library.

- **Static.** `make` builds `stdlib/lib_thread.a`. A host links it and
  registers it with `spy_new_module(c, "_thread", spy_init__thread)`, which
  `stdlib/spy-stdlib.h` declares. The `spy` command links it this way.
  `spyc` takes `stdlib/_thread.c` or `stdlib/lib_thread.a` as a C or archive
  module.
- **Dynamic.** `make` builds `stdlib/_thread.so`. A host loads it with
  `spy_std_load_native(c, "_thread", path)`. A host that searches beside a
  program's sources, as the `spy` command does, finds `_thread.so` there.

The Python source is embedded in `stdlib/_thread-source.h`, which
`tools/build_intrinsics.py` generates from `stdlib/_thread.py`. Ordinary
builds use the checked-in header. The C wrapper uses only `malloc`,
`strlen` and `memcpy`; the WebAssembly worker does not link the module.

## 4 Evidence

- **`tests/std.py`** runs two checks:
  - `tests/thread_probe.py` under `spy` and under the pinned CPython 3.15,
    requiring the same output. It covers the module's names and messages,
    lock and `RLock` semantics, threads that start, end, raise and are
    joined, a contended counter, a lock passed to a waiting thread, a timed
    wait, and `_shutdown`.
  - `tests/thread_virtual.py` under `spy` alone, for what section 2 says
    differs from CPython: start order, no preemption, idents, nested waits
    resuming last first, the `RuntimeError` of a wait nothing can end, and
    a thread that cannot wait for the one below it.
- **`tests/threads`** loads `stdlib/_thread.so` into four contexts on four
  system threads at once. Each context runs virtual threads and is freed
  with one still queued.
- **`tests/tla/SpyThreads.tla`** models the scheduler. TLC checks four
  properties, and deadlock checking with `Termination` checks that the
  host's call always returns:
  - only the thread on top runs, and `_current` names it;
  - a queued thread has not started;
  - a wait ends only when its condition holds or nothing is left to run;
  - the lock goes to the thread whose wait took it.
- **[benchmark.md](benchmark.md)** records what a thread and a lock cost.

## 5 Left out

- **Switching with frames below.** Every Python call in spy recurses in C,
  so a blocked thread cannot set its frames aside for another thread to
  run and resume later. It can only run others on top of itself.
  - That needs calls without C recursion (*Toward bytecode* in
    [optimization.md](optimization.md)). Then a thread whose frames since
    its start are all Python can be suspended like a generator, and threads
    switch wherever they block.
  - Calls from C into Python (a sort key, `__eq__`) would still raise when
    they block. C11 cannot switch C stacks portably.
- **Host functions that answer later.** A host function that waits, such as
  a network request or a model's tool, blocks every thread. Letting it hand
  back a pending result, which a waiting thread blocks on, would let
  threads wait for several host functions at once.
- **Parallelism.** All threads share one system thread. Separate contexts
  already run in parallel.

## 6 Sources

The design follows the virtual threads Mark Shannon proposed for CPython
("Add Virtual Threads to Python", discuss.python.org, 2025):

- threads with no new syntax;
- switches only at well-defined points, with no preemption;
- an exception, instead of a hang, where a switch would need to set C
  frames aside.

It also follows PEP 219 (Stackless Python), which keeps Python frames off
the C stack so that threads can switch. The module's interface and messages
are CPython's `Modules/_threadmodule.c`.
