"""The parent side of the worker protocol: a Runtime owns one spy-worker
process, takes turns with it, runs host callbacks, and proxies engine values.
See docs/packaging/python.md."""
import os
import select
import signal
import subprocess
import sys
import threading
import time

from . import _wire as wire
from ._wire import Violation

WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spy-worker")


class Error(Exception):
    """An engine exception that escaped: type, message, exception, filename, lineno."""

    filename = None
    lineno = None

    def __init__(self, type=None, message=None, exception=None):
        super().__init__(type, message, exception)

    type = property(lambda self: self.args[0] if self.args else None)
    message = property(lambda self: self.args[1] if len(self.args) > 1 else None)
    exception = property(lambda self: self.args[2] if len(self.args) > 2 else None)

    def __str__(self):
        return f"{self.type}: {self.message}" if self.message else str(self.type)


class WorkerError(RuntimeError):
    """The worker was lost: it crashed, broke the protocol, or was terminated."""

    def __init__(self, message, returncode=None):
        super().__init__(message)
        self.returncode = returncode


class Timeout(WorkerError, TimeoutError):
    """An operation ran past the runtime's timeout; the worker was terminated."""


# Engine exceptions that Python protocols expect as their own (Object operations).
_PROTOCOL = {"TypeError": TypeError, "KeyError": KeyError, "IndexError": IndexError,
             "AttributeError": AttributeError, "StopIteration": StopIteration}


class Runtime:
    """An independent Small Python engine running in its own worker process.

    Keyword arguments: ``std`` registers the standard modules (sys, gc,
    weakref, ...); ``step_limit`` bounds evaluation steps (0 is unlimited);
    ``memory_limit`` bounds the engine's memory in bytes (0 is unlimited);
    ``timeout`` bounds the seconds one operation may run (None is unlimited);
    ``output`` receives printed text (default ``sys.stdout.write``);
    ``loader`` maps a module name to its source, or None when not found;
    ``message_limit`` bounds a protocol message in bytes.
    """

    def __init__(self, *, std=True, step_limit=0, memory_limit=0, timeout=None,
                 output=None, loader=None, message_limit=64 << 20):
        if hasattr(self, "_process"):
            raise RuntimeError("the runtime is already initialized")
        for name, limit in (("step_limit", step_limit), ("memory_limit", memory_limit)):
            if not isinstance(limit, int) or limit < 0:
                raise ValueError(f"{name} must be an int >= 0")
        if not isinstance(message_limit, int) or not 1 <= message_limit <= 0xFFFFFFFF:
            raise ValueError("message_limit must be an int from 1 to 2**32 - 1")
        if timeout is not None and not timeout > 0:
            raise ValueError("timeout must be positive or None")
        if (output is not None and not callable(output)) or (loader is not None and not callable(loader)):
            raise TypeError("output and loader must be callable or None")
        self._process = None
        self._lost = None
        self._closed = False
        self._timeout = timeout
        self._output = output
        self._loader = loader
        self._message_limit = message_limit
        self._functions = {}      # function id -> callable
        self._function_ids = {}   # id(callable) -> function id
        self._released = []       # handle ids of collected Objects, sent with the next message
        self._failure = None      # (token, exception) last raised into the engine
        self._tokens = 0
        self._mutex = threading.Lock()
        self._owner = None
        self._depth = 0
        self._callbacks = 0
        self._deadline = None
        try:
            self._process = subprocess.Popen(
                [WORKER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0,
                env={}, cwd="/", close_fds=True, start_new_session=True)
        except OSError as e:
            raise WorkerError(f"cannot start the worker: {e}") from e
        self._to = self._process.stdin.fileno()
        self._from = self._process.stdout.fileno()
        options = {"std": bool(std), "step_limit": step_limit, "memory_limit": memory_limit,
                   "message_limit": message_limit}
        self.version = self._run(wire.INIT, options)

    # Ownership: one thread at a time, and one top-level operation at a time.

    def _run(self, kind, *fields):
        if self._lost:
            raise WorkerError(str(self._lost), self._lost.returncode)
        if self._closed:
            raise RuntimeError("the runtime is closed")
        me = threading.get_ident()
        with self._mutex:
            if self._owner not in (None, me):
                raise RuntimeError("the runtime is in use by another thread")
            self._owner = me
            self._depth += 1
        try:
            if self._depth == 1 and self._timeout is not None:
                self._deadline = time.monotonic() + self._timeout
            return self._request(kind, fields)
        finally:
            self._depth -= 1
            if not self._depth:
                self._owner = None
                self._deadline = None

    def _request(self, kind, fields):
        data = wire.message(kind, fields, self._reference)
        if len(data) - 4 > self._message_limit:
            raise ValueError("message exceeds the limit")
        done = False
        try:
            self._send(data)
            reply, value = self._await_reply()
            done = True
        finally:
            if not done:
                self._lose(WorkerError("the worker was terminated while it was running"))
        if reply == wire.RAISE:
            raise self._engine_error(value)
        return value

    def _await_reply(self):
        while True:
            reader = self._receive()
            kind = reader.data[0]
            if kind in (wire.HOST, wire.LOAD, wire.OUTPUT):
                self._serve(kind, reader)
                continue
            if kind not in (wire.RESULT, wire.RAISE):
                raise self._violation(f"unexpected message kind {kind:#x}")
            value = self._decode(reader, 1)[0]
            if kind == wire.RAISE:
                self._check_error(value)
            return kind, value

    # The stream.

    def _send(self, data):
        if self._released:
            ids, self._released[:] = tuple(self._released), []
            self._write(wire.message(wire.RELEASE, (ids,), self._reference))
        self._write(data)

    def _write(self, data):
        view = memoryview(data)
        while view:
            self._wait(self._to, write=True)
            try:
                view = view[os.write(self._to, view):]
            except BrokenPipeError:
                raise self._exited() from None

    def _read(self, n):
        chunks = []
        while n:
            self._wait(self._from, write=False)
            chunk = os.read(self._from, min(n, 1 << 20))
            if not chunk:
                raise self._exited()
            chunks.append(chunk)
            n -= len(chunk)
        return b"".join(chunks)

    def _wait(self, fd, write):
        if self._deadline is None:
            return
        remaining = self._deadline - time.monotonic()
        ready = select.select([], [fd], [], max(remaining, 0)) if write else select.select([fd], [], [], max(remaining, 0))
        if not any(ready):
            raise self._lose(Timeout(f"the operation exceeded the timeout of {self._timeout} seconds"))

    def _receive(self):
        n = int.from_bytes(self._read(4), "little")
        if not 1 <= n <= self._message_limit:
            raise self._violation("message length out of range")
        return wire.Reader(self._read(n), self._obtain)

    def _decode(self, reader, count):
        try:
            values = [reader.value() for _ in range(count)]
            if reader.at != len(reader.data):
                raise Violation("trailing bytes in message")
        except Violation as e:
            raise self._violation(str(e)) from None
        reader.finish()
        return values

    # Losing the worker (protocol.md 8).

    def _violation(self, what):
        return self._lose(WorkerError(f"the worker broke the protocol: {what}"))

    def _exited(self):
        code = self._process.wait()
        how = f"was killed by {_signal_name(-code)}" if code < 0 else f"exited with status {code}"
        return self._lose(WorkerError(f"the worker {how}", code))

    def _lose(self, error):
        if self._lost is None:
            self._lost = error
            self._end()
        return self._lost

    def _end(self):
        process = self._process
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdin.close()
        process.stdout.close()
        self._functions.clear()
        self._function_ids.clear()
        self._released.clear()
        self._failure = None
        self._output = self._loader = None

    # Values.

    def _reference(self, value):
        if type(value) is Object:
            if object.__getattribute__(value, "_runtime") is not self:
                raise ValueError("the object belongs to another runtime")
            return wire.handle(object.__getattribute__(value, "_id"))
        if type(value) is _Named:
            return wire.function(self._function_id(value.function), value.name)
        if callable(value):
            name = getattr(value, "__name__", None)
            return wire.function(self._function_id(value), name if isinstance(name, str) else type(value).__name__)
        raise TypeError(f"cannot convert '{type(value).__name__}' to an engine value")

    def _function_id(self, function):
        key = id(function)
        fid = self._function_ids.get(key)
        if fid is None:
            fid = self._function_ids[key] = len(self._functions) + 1
            self._functions[fid] = function
        return fid

    def _obtain(self, id):
        return Object._new(self, id)

    # Errors from the engine.

    def _check_error(self, error):
        keys = {"type": str, "message": str, "filename": str, "line": int, "exception": (Object, type(None)),
                "token": int}
        if type(error) is not dict or error.keys() != keys.keys() or \
                not all(issubclass(type(error[k]), t) for k, t in keys.items()):
            raise self._violation("malformed error")

    def _engine_error(self, error):
        cause = None
        if self._failure and error["token"] == self._failure[0]:
            cause = self._failure[1]
        self._failure = None
        if cause is not None and not isinstance(cause, Exception):
            return cause
        result = Error(error["type"], error["message"], error["exception"])
        result.filename, result.lineno = error["filename"], error["line"]
        result.__cause__ = cause
        return result

    def _protocol_error(self, error, key=None):
        """For Object operations: the builtin exception Python protocols expect."""
        cls = _PROTOCOL.get(error.type) if isinstance(error, Error) else None
        if cls is None:
            return error
        if cls is KeyError and key is not None:
            return KeyError(key)
        return cls(error.message) if error.message else cls()

    # Host callbacks (worker requests).

    def _serve(self, kind, reader):
        if kind == wire.HOST:
            fid, args, kwargs = self._decode_fields(reader, 3)
            function = self._functions.get(fid) if type(fid) is int else None
            if function is None or type(args) is not tuple or type(kwargs) is not dict or \
                    not all(type(k) is str for k in kwargs):
                raise self._violation("malformed host call")
            run = lambda: function(*args, **kwargs)
        elif kind == wire.LOAD:
            (name,) = self._decode_fields(reader, 1)
            if type(name) is not str:
                raise self._violation("malformed load")
            run = lambda: self._load(name)
        else:
            (text,) = self._decode_fields(reader, 1)
            if type(text) is not str:
                raise self._violation("malformed output")
            run = lambda: self._write_output(text)
        started = time.monotonic()
        self._callbacks += 1
        try:
            result = run()
            reply = wire.message(wire.RESULT, (result,), self._reference)
        except BaseException as e:
            if self._lost:
                raise
            reply = wire.message(wire.RAISE, (self._failure_of(e),), self._reference)
        finally:
            self._callbacks -= 1
            if self._deadline is not None:
                self._deadline += time.monotonic() - started
        if len(reply) - 4 > self._message_limit:
            reply = wire.message(wire.RAISE, (self._failure_of(ValueError("message exceeds the limit")),),
                                 self._reference)
        self._send(reply)

    def _decode_fields(self, reader, count):
        try:
            return self._decode(reader, count)
        except WorkerError:
            raise
        except Exception as e:
            raise self._violation(f"unconvertible request: {e}") from None

    def _load(self, name):
        if self._loader is None:
            return None
        source = self._loader(name)
        if source is not None and not isinstance(source, str):
            raise TypeError("a loader must return str or None")
        return source

    def _write_output(self, text):
        # A failure is reported here; the engine's print raises its own OSError.
        try:
            if self._output is not None:
                self._output(text)
            elif sys.stdout is not None:
                sys.stdout.write(text)
        except Exception as e:
            sys.unraisablehook(_Unraisable(e, self._output))
            raise

    def _failure_of(self, exception):
        self._tokens += 1
        self._failure = (self._tokens, exception)
        if isinstance(exception, Error) and type(exception.exception) is Object and \
                object.__getattribute__(exception.exception, "_runtime") is self:
            return {"raise": exception.exception, "token": self._tokens}
        try:
            wire.message(wire.RESULT, (exception.args,), self._reference)
            args = exception.args
        except Exception:
            args = None
        return {"classes": tuple(c.__name__ for c in type(exception).__mro__), "args": args,
                "message": str(exception), "token": self._tokens}

    # The public API.

    def _no_callback(self, what):
        if self._callbacks and self._owner == threading.get_ident():
            raise RuntimeError(f"cannot {what} while a host function of this runtime is running")

    def eval(self, source, filename="<string>"):
        """Run source and return the value of its last expression statement."""
        self._no_callback("evaluate source")
        return self._run(wire.EVAL, _source(source), _str(filename))

    def exec(self, source, filename="<string>"):
        """Run source for its effects."""
        self._no_callback("evaluate source")
        self._run(wire.EXEC, _source(source), _str(filename))

    def call(self, function, /, *args, **kwargs):
        """Call a global name, an Object, or a callable, and return the result."""
        return self._run(wire.CALL, function, args, kwargs)

    def __getitem__(self, name):
        try:
            return self._run(wire.GET, _name(name))
        except Error as e:
            if e.type == "NameError":
                raise KeyError(name) from None
            raise

    def __setitem__(self, name, value):
        self._run(wire.SET, _name(name), value)

    def __delitem__(self, name):
        try:
            self._run(wire.DELETE, _name(name))
        except Error as e:
            if e.type == "KeyError":
                raise KeyError(name) from None
            raise

    def define(self, name, function):
        """Bind a Python callable as the global ``name``; returns it."""
        if not callable(function):
            raise TypeError("define() needs a callable")
        self._run(wire.SET, _name(name), _Named(function, name))
        return function

    def function(self, func=None, *, name=None):
        """Decorator binding a Python callable as a global host function."""
        def bind(func):
            return self.define(name or func.__name__, func)
        return bind(func) if func is not None else bind

    def register_module(self, name, members=None, source=None):
        """Make ``import name`` create a module from members, then source."""
        if members is not None and (not isinstance(members, dict) or not all(isinstance(k, str) for k in members)):
            raise TypeError("members must be a dict with str keys")
        if source is not None and not isinstance(source, str):
            raise TypeError("source must be a str")
        self._run(wire.MODULE, _name(name), members, source)

    def mount(self, directory, path=None, *, read_only=False):
        """Let the engine's open() reach a host directory at an engine path."""
        directory = os.path.realpath(os.fsdecode(directory))
        if not os.path.isdir(directory):
            raise Error("OSError", f"cannot mount '{directory}': Not a directory")
        if path is None:
            path = directory
        self._run(wire.MOUNT, directory, _str(path), bool(read_only))

    def collect(self):
        """Run the engine's cycle collector; returns the number of values freed."""
        return self._run(wire.COLLECT)

    @property
    def closed(self):
        return self._closed or self._lost is not None

    def close(self):
        """End the worker and drop every host reference. Idempotent."""
        if self._closed or self._process is None:
            self._closed = True
            return
        self._no_callback("close the runtime")
        if self._owner not in (None, threading.get_ident()):
            raise RuntimeError("the runtime is in use by another thread")
        self._closed = True
        if self._lost is None:
            process = self._process
            process.stdin.close()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
            self._end()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        if getattr(self, "_process", None) is not None and not self._closed and self._lost is None:
            self._closed = True
            self._end()


class Object:
    """An engine value held by the worker, operated on by message."""

    __slots__ = ("_runtime", "_id")

    @classmethod
    def _new(cls, runtime, id):
        self = object.__new__(cls)
        object.__setattr__(self, "_runtime", runtime)
        object.__setattr__(self, "_id", id)
        return self

    def __init__(self, *args, **kwargs):
        raise TypeError("Object values come from a Runtime")

    def __del__(self):
        runtime = object.__getattribute__(self, "_runtime")
        if not runtime.closed:
            runtime._released.append(object.__getattribute__(self, "_id"))

    def _op(self, op, *operands, key=None):
        runtime = object.__getattribute__(self, "_runtime")
        try:
            return runtime._run(wire.OP, op, self, *operands)
        except Error as e:
            raise runtime._protocol_error(e, key) from None

    def __getattribute__(self, name):
        try:
            return Object._op(self, 1, name)
        except AttributeError:
            if name.startswith("__") or name in Object.__dict__:
                try:
                    return object.__getattribute__(self, name)
                except AttributeError:
                    pass
            raise

    def __setattr__(self, name, value):
        Object._op(self, 2, name, value)

    def __delattr__(self, name):
        raise TypeError("deleting attributes of engine values is not supported")

    def __getitem__(self, key):
        return Object._op(self, 3, key, key=key)

    def __setitem__(self, key, value):
        Object._op(self, 4, key, value, key=key)

    def __delitem__(self, key):
        raise TypeError("deleting items of engine values is not supported")

    def __len__(self):
        return Object._op(self, 5)

    def __contains__(self, item):
        return Object._op(self, 6, item)

    def __iter__(self):
        return Object._op(self, 7)

    def __next__(self):
        return Object._op(self, 8)

    def __bool__(self):
        return Object._op(self, 9)

    def __hash__(self):
        return Object._op(self, 10)

    def _compare(self, op, other, equality):
        runtime = object.__getattribute__(self, "_runtime")
        if type(other) is Object and object.__getattribute__(other, "_runtime") is not runtime:
            if equality:
                return op == 14
            return NotImplemented
        try:
            wire.message(wire.OP, (other,), runtime._reference)
        except (TypeError, ValueError):
            if equality:
                return op == 14
            return NotImplemented
        return Object._op(self, op, other)

    __lt__ = lambda self, other: Object._compare(self, 11, other, False)
    __le__ = lambda self, other: Object._compare(self, 12, other, False)
    __eq__ = lambda self, other: Object._compare(self, 13, other, True)
    __ne__ = lambda self, other: Object._compare(self, 14, other, True)
    __gt__ = lambda self, other: Object._compare(self, 15, other, False)
    __ge__ = lambda self, other: Object._compare(self, 16, other, False)

    def __repr__(self):
        runtime = object.__getattribute__(self, "_runtime")
        if runtime.closed:
            return "<small_python.Object (closed)>"
        return Object._op(self, 17)

    def __str__(self):
        return Object._op(self, 18)

    def __dir__(self):
        return Object._op(self, 19)

    def __call__(self, *args, **kwargs):
        runtime = object.__getattribute__(self, "_runtime")
        return runtime._run(wire.CALL, self, args, kwargs)


class _Named:
    """A callable passed in under a chosen name, as define() does."""

    def __init__(self, function, name):
        self.function, self.name = function, name


class _Unraisable:
    def __init__(self, exception, obj):
        self.exc_type, self.exc_value, self.exc_traceback = type(exception), exception, exception.__traceback__
        self.err_msg = "Exception ignored in the runtime's output callback"
        self.object = obj


def _str(value):
    if not isinstance(value, str):
        raise TypeError(f"expected str, not '{type(value).__name__}'")
    return value


def _source(source):
    if "\0" in _str(source):
        raise ValueError("source code string cannot contain null bytes")
    return source


def _name(name):
    if not isinstance(name, str):
        raise TypeError(f"global names must be str, not '{type(name).__name__}'")
    return name


def _signal_name(number):
    try:
        return signal.Signals(number).name
    except ValueError:
        return f"signal {number}"
