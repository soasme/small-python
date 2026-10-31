# Limits and safety

A runtime starts with very little: builtins, the standard modules if
`std=True`, and nothing from the host. That makes it a good place to run
scripts, rules, plugins, or generated code that should only touch what you
pass in. Read the limits below before relying on it for code you do not trust.

## What code in a runtime can reach

| Resource | Default | How to grant it |
|---|---|---|
| Your Python objects and modules | None | `define`, `register_module`, `rt[name] = ...` |
| Imports | Builtin and registered modules only | `register_module`, `loader=` |
| Files | None: `open()` raises `PermissionError` | `mount(directory, read_only=...)` |
| Printed output | Host `sys.stdout` | `output=` |
| Standard input | None: `input()` raises `EOFError` | a host function |
| Network, processes, environment, clock | None | a host function |

Every host function you define is part of what the code can do, with your
process's full privileges. Keep them narrow: validate arguments, and prefer a
function that does one thing (`read_report(name)`) over a general one
(`open_any_file(path)`). Values you pass in are copies or engine objects, never
references to your CPython objects, so engine code cannot reach your objects
through attributes of the values it is given. A callable you pass in is the
exception: the engine can call it with any arguments.

## Bounding execution

| Limit | Argument | When exceeded | Runtime survives |
|---|---|---|---|
| Steps | `step_limit=n` | `RuntimeError` in the engine | yes |
| Memory | `memory_limit=bytes` | `MemoryError` in the engine | yes |
| Recursion | engine's own | `RecursionError` in the engine | yes |
| Time | `timeout=seconds` | `Timeout` raised | yes |
| Message size | `message_limit=bytes` | the value is refused | yes |

`step_limit` counts calls, loop passes, allocation and native work in
proportion to what it reads ([docs/metering.md](../../docs/metering.md)).
Each `eval`, `exec` or `call()` gets the whole budget. A spent step or
memory budget stops the operation: the program cannot catch the error, and
the runtime goes on.

`timeout` is wall-clock time per operation spent in the worker. Time inside
your host functions, `output`, and `loader` is yours and does not count.
The engine stops the operation as it stops a spent step budget, and the
runtime goes on. A worker that does not stop within a further second, which
only a single native operation of that length or a bug can cause, is
terminated and the runtime's state is lost.

```python
from small_python import Error, Runtime, Timeout

with Runtime(step_limit=1_000_000, memory_limit=64 << 20, timeout=5) as rt:
    try:
        rt.exec("while True:\n    pass")
    except Error as e:
        print(e)   # RuntimeError: execution step limit exceeded
```

## Isolation

Each runtime runs the engine in its own `spy-worker` process, speaking a
message protocol over pipes. If the engine crashes, whether from a bug or from
code that exploits one, the worker dies and the runtime raises `WorkerError`;
your process continues. Your process treats the worker as hostile: it checks
every message, terminates the worker at the first malformed one, and never
evaluates anything the worker sends.

The worker starts with an empty environment, the root directory as working
directory, no open files but its pipes and stderr, and in its own process
group. It exits when your process exits. Separate runtimes are separate
processes and cannot affect each other.

Before it runs any engine code, the worker also locks itself down with the
operating system's sandbox, so that even a worker taken over by an exploit
cannot reach more than the engine could:

- **Linux**: no new privileges; Landlock (kernel 5.13+) limits files to your
  mounted directories, read-only where you asked, and blocks TCP (6.7+);
  seccomp (x86_64 and aarch64) refuses every system call the engine does not
  make, such as starting processes or opening sockets.
- **macOS**: a sandbox profile that denies everything except reading file
  metadata and using your mounted directories.
- **Windows**: none. The engine has no `open()` there and `mount` raises
  `Error` of type `OSError`, but a worker taken over by an exploit runs with
  your privileges.

Because of this, mount directories before running code: `mount` after the
first `eval`, `exec`, or `call` raises `Error` of type `PermissionError`.
A kernel without Landlock or seccomp gets the layers it has; on other systems,
including Windows, run hostile code inside a container or VM as well.

## Threads

A runtime belongs to one thread at a time: while an operation runs, calls from
any other thread raise `RuntimeError`. Separate runtimes are independent and
may be used from different threads at once.

## Interrupting

Ctrl-C reaches your process, not the worker. A `KeyboardInterrupt` that
arrives while a runtime waits for its worker terminates the worker and
propagates; the runtime is then closed. A `KeyboardInterrupt` raised inside a
host function is an ordinary host exception and reaches engine code.
