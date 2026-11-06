"""This module provides primitive operations to write multi-threaded programs.
The 'threading' module provides a more convenient interface."""
# Virtual threads (docs/threads.md): every thread runs on the host's system
# thread, and switches only where it would block. A thread that blocks runs
# the threads not yet started, each on top of it, until what it waits for
# holds. A thread below another resumes only when the one above it ends, so
# a wait that no thread can end raises instead of hanging.

error = RuntimeError
TIMEOUT_MAX = 9223372036.0
try:
    from _spy import _setting
except ImportError:
    _setting = None

_main = 1
_current = _main
_last = _main
_queue = []
_live = 0
_stack_size = 0


def _report(error, message):
    # As the engine reports an unraisable error: sys, loaded for its hook.
    if _setting is None:
        return
    if _setting('unraisablehook') is None:
        try:
            import sys
        except ImportError:
            pass
    hook = _setting('unraisablehook')
    if hook is not None:
        # The traceback starts in the thread's function, not in run.
        if error.__traceback__ is not None:
            error.__traceback__ = error.__traceback__.tb_next
        hook(type(error), error, error.__traceback__, message, None)


def _start(run):
    global _last, _live
    _last += 1
    _queue.append((_last, run))
    _live += 1
    return _last


def _wait(ready, timed):
    # Block until ready() holds, running the threads not yet started on top
    # of this one. With none left, a timed wait times out and a wait for
    # ever raises.
    global _current, _live
    while not ready():
        if not _queue:
            if timed:
                return False
            raise RuntimeError('cannot block: no other thread can run until this one ends')
        waiting = _current
        _current, run = _queue.pop(0)
        try:
            run()
        finally:
            _current = waiting
            _live -= 1
    return True


def _timeout(args, kwargs):
    # acquire's arguments, as milliseconds to wait: negative for ever.
    given = len(args) + len(kwargs)
    if given > 2:
        raise TypeError(f"acquire() takes at most 2 arguments ({given} given)")
    values = dict(zip(("blocking", "timeout"), args))
    for name in kwargs:
        if name not in ("blocking", "timeout"):
            raise TypeError(f"acquire() got an unexpected keyword argument '{name}'")
        if name in values:
            raise TypeError(f"argument for acquire() given by name ('{name}') and position ({len(values)})")
        values[name] = kwargs[name]
    blocking = bool(values.get("blocking", True))
    timeout = values.get("timeout", -1)
    kind = type(timeout)
    if not (hasattr(kind, "__float__") or hasattr(kind, "__index__")):
        raise TypeError(f"must be real number, not {kind.__name__}")
    timeout = float(timeout)
    if timeout != timeout:
        raise ValueError("Invalid value NaN (not a number)")
    if not blocking:
        if timeout != -1:
            raise ValueError("can't specify a timeout for a non-blocking call")
        return 0.0
    if timeout == -1:
        return -1.0
    if timeout < 0:
        raise ValueError("timeout value must be a non-negative number")
    if timeout > TIMEOUT_MAX:
        raise OverflowError("timestamp out of range for C PyTime_t")
    return timeout * 1000.0


class lock:
    """A lock object is a synchronization primitive."""
    def __init__(self):
        self._locked = False
    def _free(self):
        return not self._locked
    def _take(self, ms):
        if self._locked and (not ms or not _wait(self._free, ms > 0)):
            return False
        self._locked = True
        return True
    def acquire(self, *args, **kwargs):
        """Lock the lock."""
        return self._take(_timeout(args, kwargs) if args or kwargs else -1.0)
    def release(self):
        """Release the lock."""
        if not self._locked:
            raise RuntimeError('release unlocked lock')
        self._locked = False
    def locked(self):
        """Test whether the lock is currently locked."""
        return self._locked
    def acquire_lock(self, *args, **kwargs):
        """An obsolete synonym of acquire()."""
        return self._take(_timeout(args, kwargs) if args or kwargs else -1.0)
    def release_lock(self):
        """An obsolete synonym of release()."""
        self.release()
    def locked_lock(self):
        """An obsolete synonym of locked()."""
        return self._locked
    def __enter__(self):
        return self._take(-1.0)
    def __exit__(self, *args):
        self.release()
    def _at_fork_reinit(self):
        self._locked = False
    def __repr__(self):
        state = 'locked' if self._locked else 'unlocked'
        return f'<{state} _thread.lock object at {id(self):#x}>'
LockType = lock


def allocate_lock():
    """Create a new lock object. See help(type(threading.Lock())) for
information about locks."""
    return lock()
def allocate():
    """An obsolete synonym of allocate_lock()."""
    return lock()


class RLock:
    """A reentrant lock: the thread holding it may acquire it again."""
    def __init__(self, *args, **kwargs):
        self._block = lock()
        self._owner = 0
        self._count = 0
    def acquire(self, *args, **kwargs):
        """Lock the lock."""
        ms = _timeout(args, kwargs) if args or kwargs else -1.0
        if self._count and self._owner == _current:
            self._count += 1
            return True
        if not self._block._take(ms):
            return False
        self._owner = _current
        self._count = 1
        return True
    __enter__ = acquire
    def release(self):
        """Release the lock."""
        if not self._count or self._owner != _current:
            raise RuntimeError('cannot release un-acquired lock')
        self._count -= 1
        if not self._count:
            self._owner = 0
            self._block.release()
    def __exit__(self, *args):
        self.release()
    def locked(self):
        """Test whether the lock is currently locked."""
        return self._block.locked()
    def _is_owned(self):
        return bool(self._count) and self._owner == _current
    def _recursion_count(self):
        return self._count if self._is_owned() else 0
    def _release_save(self):
        if not self._count:
            raise RuntimeError('cannot release un-acquired lock')
        state = (self._count, self._owner)
        self._count = 0
        self._owner = 0
        self._block.release()
        return state
    def _acquire_restore(self, state):
        self._block.acquire()
        self._count, self._owner = state
    def _at_fork_reinit(self):
        self.__init__()
    def __repr__(self):
        state = 'locked' if self._block.locked() else 'unlocked'
        return f'<{state} _thread.RLock object owner={self._owner} count={self._count} at {id(self):#x}>'


def get_ident():
    """Return a non-zero integer that uniquely identifies the current thread
amongst other threads that exist simultaneously."""
    return _current


def get_native_id():
    """Return a non-negative integer identifying the thread as reported
by the OS (kernel)."""
    return _current


def _count():
    """Return the number of currently running Python threads, excluding
the main thread."""
    return _live


def _get_main_thread_ident():
    return _main


def _is_main_interpreter():
    return True


def daemon_threads_allowed():
    """Return True if daemon threads are allowed in the current interpreter."""
    return True


def stack_size(size=None, /):
    """Return the thread stack size used when creating new threads."""
    global _stack_size
    old = _stack_size
    if size is not None:
        size = size.__index__()
        if size and size < 32768:
            raise ValueError('size must be at least 32768 bytes')
        if size < 0:
            raise ValueError('size must be 0 or a positive value')
        _stack_size = size
    return old


def exit():
    """This is synonymous to ``raise SystemExit''."""
    raise SystemExit
def exit_thread():
    """An obsolete synonym of exit()."""
    raise SystemExit


def start_new_thread(function, args, kwargs=None, /):
    """Start a new thread and return its identifier."""
    if not callable(function):
        raise TypeError('first arg must be callable')
    if not isinstance(args, tuple):
        raise TypeError('2nd arg must be a tuple')
    if kwargs is not None and not isinstance(kwargs, dict):
        raise TypeError('optional 3rd arg must be a dictionary')
    def run():
        try:
            function(*args, **(kwargs or {}))
        except SystemExit:
            pass
        except BaseException as error:
            _report(error, f'Exception ignored in thread started by {function!r}')
    return _start(run)
def start_new(function, args, kwargs=None, /):
    """An obsolete synonym of start_new_thread()."""
    return start_new_thread(function, args, kwargs)


_handles = {}


class _ThreadHandle:
    def __init__(self):
        self.ident = None
        self._done = False
        self._daemon = True
    def is_done(self):
        return self._done
    def _set_done(self):
        self._done = True
    def join(self, timeout=None):
        if self.ident == _current and not self._done:
            raise RuntimeError('Cannot join current thread')
        _wait(self.is_done, timeout is not None and timeout >= 0)
    def __repr__(self):
        return f'<_thread._ThreadHandle object: ident={self.ident}>'


def start_joinable_thread(function, handle=None, daemon=True):
    """*For internal use only*: start a new thread."""
    if not callable(function):
        raise TypeError('thread function must be callable')
    if handle is None:
        handle = _ThreadHandle()
    handle._daemon = daemon
    def run():
        try:
            function()
        except SystemExit:
            pass
        except BaseException as error:
            _report(error, f'Exception ignored in thread started by {function!r}')
        finally:
            _handles.pop(id(handle), None)
            handle._set_done()
    _handles[id(handle)] = handle
    handle.ident = _start(run)
    return handle


def _make_thread_handle(ident):
    handle = _ThreadHandle()
    handle.ident = ident
    return handle


def _shutdown():
    """Wait for all non-daemon threads."""
    for handle in list(_handles.values()):
        if not handle._daemon and handle.ident != _current:
            handle.join()
