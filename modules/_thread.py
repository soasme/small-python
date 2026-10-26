"""This module provides primitive operations to write multi-threaded programs.
The 'threading' module provides a more convenient interface.

Small Python's standard layer (spy-std.c) provides this module, following CPython 3.15's _thread
module. The engine runs one thread, so get_ident() is constant and starting a
thread raises RuntimeError. Locks keep CPython's states, arguments, and errors;
a blocking acquire that no other thread could ever satisfy raises RuntimeError
instead of hanging.
"""

error = RuntimeError
TIMEOUT_MAX = 9223372036.0
_NAME_MAXLEN = 15
_MAIN_IDENT = 1


def _timeout(blocking, timeout):
    # The checks of CPython's lock_acquire_parse_args.
    if not isinstance(timeout, (int, float)):
        if not hasattr(type(timeout), '__float__') and not hasattr(type(timeout), '__index__'):
            raise TypeError(f'must be real number, not {type(timeout).__name__}')
        timeout = float(timeout)
    if not blocking and timeout != -1:
        raise ValueError("can't specify a timeout for a non-blocking call")
    if timeout < 0 and timeout != -1:
        raise ValueError('timeout value must be a non-negative number')
    if timeout > TIMEOUT_MAX:
        raise OverflowError('timeout value is too large')
    return timeout


def _wait(blocking, timeout):
    # Only another thread could release the lock, and none exists.
    if blocking and timeout == -1:
        raise RuntimeError('deadlock: the lock is held and no other thread can release it')
    return False


class lock:
    """A lock object is a synchronization primitive.  To create a lock,
call threading.Lock().  Methods are:

acquire() -- lock the lock, possibly blocking until it can be obtained
release() -- unlock of the lock
locked() -- test whether the lock is currently locked

A lock is not owned by the thread that locked it; another thread may
unlock it.  A thread attempting to lock a lock that it has already locked
will block until another thread unlocks it.  Deadlocks may ensue."""

    def __new__(cls, *args, **kwargs):
        if args:
            raise TypeError('lock() takes no positional arguments')
        if kwargs:
            raise TypeError('lock() takes no keyword arguments')
        self = object.__new__(cls)
        self._locked = False
        return self

    def acquire(self, blocking=True, timeout=-1):
        """Lock the lock."""
        timeout = _timeout(blocking, timeout)
        if not self._locked:
            self._locked = True
            return True
        return _wait(blocking, timeout)

    acquire_lock = acquire

    def __enter__(self):
        return self.acquire()

    def release(self):
        """Release the lock."""
        if not self._locked:
            raise RuntimeError('release unlocked lock')
        self._locked = False

    release_lock = release

    def __exit__(self, *args):
        self.release()

    def locked(self):
        """Test whether the lock is currently locked."""
        return self._locked

    locked_lock = locked

    def _at_fork_reinit(self):
        self._locked = False

    def __repr__(self):
        state = 'locked' if self._locked else 'unlocked'
        return f'<{state} _thread.lock object at {hex(id(self))}>'


LockType = lock


class RLock:
    def __new__(cls, *args, **kwargs):
        if args:
            raise TypeError('RLock() takes no positional arguments')
        self = object.__new__(cls)
        self._owner = 0
        self._count = 0
        return self

    def acquire(self, blocking=True, timeout=-1):
        """Lock the lock."""
        timeout = _timeout(blocking, timeout)
        if self._count and self._owner != _MAIN_IDENT:
            return _wait(blocking, timeout)
        self._owner = _MAIN_IDENT
        self._count += 1
        return True

    def __enter__(self):
        return self.acquire()

    def release(self):
        """Release the lock."""
        if not self._count or self._owner != _MAIN_IDENT:
            raise RuntimeError('cannot release un-acquired lock')
        self._count -= 1
        if not self._count:
            self._owner = 0

    def __exit__(self, *args):
        self.release()

    def locked(self):
        """locked()

Return a boolean indicating whether this object is locked right now."""
        return self._count > 0

    def _is_owned(self):
        return self._count > 0 and self._owner == _MAIN_IDENT

    def _recursion_count(self):
        return self._count if self._owner == _MAIN_IDENT else 0

    def _release_save(self):
        if not self._count:
            raise RuntimeError('cannot release un-acquired lock')
        state = (self._count, self._owner)
        self._count = 0
        self._owner = 0
        return state

    def _acquire_restore(self, state, /):
        self._count, self._owner = state

    def _at_fork_reinit(self):
        self._owner = 0
        self._count = 0

    def __repr__(self):
        state = 'locked' if self._count else 'unlocked'
        return (f'<{state} _thread.RLock object owner={self._owner} '
                f'count={self._count} at {hex(id(self))}>')


def allocate_lock():
    """Create a new lock object. See help(type(threading.Lock())) for
information about locks."""
    return lock()


allocate = allocate_lock


def get_ident():
    """Return a non-zero integer that uniquely identifies the current thread
amongst other threads that exist simultaneously."""
    return _MAIN_IDENT


def get_native_id():
    """Return a non-negative integer identifying the thread as reported
by the OS (kernel)."""
    return _MAIN_IDENT


def _get_main_thread_ident():
    return _MAIN_IDENT


def _is_main_interpreter():
    return True


def daemon_threads_allowed():
    """Return True if daemon threads are allowed in the current interpreter,
and False otherwise."""
    return True


def _count():
    """Return the number of currently running Python threads, excluding
the main thread."""
    return 0


def stack_size(size=0, /):
    """Return the thread stack size used when creating new threads."""
    if size:
        raise ValueError('size not valid: %d bytes' % size)
    return 0


def start_new_thread(function, args, kwargs=None, /):
    """Start a new thread and return its identifier."""
    raise RuntimeError("can't start new thread")


start_new = start_new_thread


def start_joinable_thread(function, handle=None, daemon=True):
    """Start a thread running the given function."""
    raise RuntimeError("can't start new thread")


def exit():
    """This is synonymous to ``raise SystemExit''."""
    raise SystemExit


exit_thread = exit


def interrupt_main(signum=2, /):
    """Simulate the arrival of the given signal in the main thread."""
    raise KeyboardInterrupt


class _local:
    """Thread-local data"""


class _ThreadHandle:
    # The main thread's handle; no other thread can exist.
    def __init__(self):
        self.ident = _MAIN_IDENT

    def is_done(self):
        return False

    def join(self, timeout=None):
        raise RuntimeError('Cannot join current thread')

    def _set_done(self):
        pass


def _make_thread_handle(ident, /):
    handle = _ThreadHandle()
    handle.ident = ident
    return handle


def _shutdown():
    pass


_thread_name = 'MainThread'


def set_name(name):
    """Set the name of the current thread."""
    global _thread_name
    _thread_name = name


def _get_name():
    return _thread_name


for _cls in (lock, RLock, _local, _ThreadHandle):
    _cls.__module__ = '_thread'
del _cls
