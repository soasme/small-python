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

`Runtime(step_limit=n)` stops evaluation after about `n` steps (evaluated
syntax nodes plus loop and iterator work) with a `RuntimeError`. The count
restarts at each `eval` or `exec`; calls made with `call()` or through an
`Object` add to the current count. Zero, the default, means no limit.

```python
from small_python import Error, Runtime

with Runtime(step_limit=1_000_000) as rt:
    try:
        rt.exec("while True:\n    pass")
    except Error as e:
        print(e)   # RuntimeError: execution step limit exceeded
```

The step limit is not a memory quota or a wall-clock timeout, and it does not
interrupt a host function while it runs. Code can still allocate large values
(`'x' * 10**9`) in few steps.

## Not an isolation boundary

Small Python is experimental. The engine runs in your process, and a bug in it
(or in a host function) can crash or compromise that process. Do not treat a
runtime as a security sandbox for hostile code. For code that may be
malicious, also run it in a separate process with OS-level limits: a
container, `seccomp`/`sandbox-exec`, `resource.setrlimit` for memory and CPU
time, and a timeout enforced by the parent.

## Threads

A runtime must not be used from two threads at once. While a host function
runs, the binding refuses calls into its runtime from other threads with
`RuntimeError`; other overlapping use is not detected. Separate runtimes are
independent and may be used from different threads, one thread each.

## Interrupting

The engine does not check for signals, so Ctrl-C does not stop a running
`eval` until it calls a host function or finishes. Use `step_limit` to bound
code that may not finish. A `KeyboardInterrupt` raised in a host function
propagates to your code.
