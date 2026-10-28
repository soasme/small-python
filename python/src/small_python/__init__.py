"""Run Small Python, a small embeddable Python engine, from CPython.

Each Runtime runs the engine in its own worker process, so nothing the engine
does can crash or take over this one.

    import small_python

    with small_python.Runtime(timeout=5) as rt:
        @rt.function
        def greet(name):
            return f"hello {name}"

        rt.eval("greet('spy')")  # 'hello spy'
"""
from importlib import metadata as _metadata

from ._runtime import WORKER as _WORKER, Error, Object, Runtime, Timeout, WorkerError

__all__ = ["Error", "Object", "Runtime", "SPY_VERSION", "Timeout", "WorkerError"]

try:
    __version__ = _metadata.version("small-python")
except _metadata.PackageNotFoundError:  # imported from a build tree, not installed
    __version__ = "0+unknown"


def __getattr__(name):
    # The engine version, asked of the bundled worker on first use.
    if name == "SPY_VERSION":
        import subprocess
        global SPY_VERSION
        SPY_VERSION = subprocess.run([_WORKER, "--version"], capture_output=True, text=True,
                                     check=True, env={}).stdout.strip()
        return SPY_VERSION
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
