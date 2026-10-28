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
| Time | `timeout=seconds` | worker terminated, `Timeout` raised | no |
| Message size | `message_limit=bytes` | the value is refused | yes |

`step_limit` counts evaluated syntax nodes plus loop and iterator work. The
count restarts at each `eval` or `exec`; calls made with `call()` or through
an `Object` add to the current count. It does not count allocation:
`'x' * 10**9` takes few steps, which is what `memory_limit` is for.

`timeout` is wall-clock time per operation spent in the worker. Time inside
your host functions, `output`, and `loader` is yours and does not count.
Because a timeout kills the worker, the runtime's state is lost; prefer
`step_limit` for a recoverable bound and `timeout` as the backstop.

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

What the process boundary does not do yet is restrict the worker's operating
system privileges: a worker taken over by an exploit runs as your user. An OS
sandbox for the worker (seccomp and Landlock on Linux, the sandbox profile on
macOS) is planned. Until then, for code that may be malicious, also run your
program in a container or a dedicated low-privilege account.

## Threads

A runtime belongs to one thread at a time: while an operation runs, calls from
any other thread raise `RuntimeError`. Separate runtimes are independent and
may be used from different threads at once.

## Interrupting

Ctrl-C reaches your process, not the worker. A `KeyboardInterrupt` that
arrives while a runtime waits for its worker terminates the worker and
propagates; the runtime is then closed. A `KeyboardInterrupt` raised inside a
host function is an ordinary host exception and reaches engine code.
