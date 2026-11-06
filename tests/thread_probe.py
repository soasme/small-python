"""The _thread module, as tests/std.py compares it with CPython 3.15.

Prints what does not depend on timing, addresses or the platform: the
module's names, every error and its message, lock and RLock semantics,
threads that start, finish, raise and are joined, mutual exclusion under
contention, and a switch from a thread that never waits.
"""
import _thread
import sys


def show(*values):
    print(*values, flush=True)


def error(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except BaseException as caught:
        return f"{type(caught).__name__}: {caught}"


public = sorted(name for name in dir(_thread) if not name.startswith("__"))
show("names", [name for name in public if name in (
    "LockType", "RLock", "TIMEOUT_MAX", "_ThreadHandle", "_count", "_get_main_thread_ident",
    "_is_main_interpreter", "_make_thread_handle", "_shutdown", "allocate", "allocate_lock",
    "daemon_threads_allowed", "error", "exit", "exit_thread", "get_ident", "get_native_id",
    "lock", "stack_size", "start_joinable_thread", "start_new", "start_new_thread")])
show("doc", _thread.__doc__)
show("aliases", _thread.LockType is _thread.lock, _thread.allocate is _thread.allocate_lock,
     _thread.start_new is _thread.start_new_thread, _thread.exit is _thread.exit_thread,
     _thread.error is RuntimeError, _thread.TIMEOUT_MAX)
show("classes", _thread.lock, _thread.RLock, _thread._ThreadHandle)
show("constants", _thread._is_main_interpreter(), _thread.daemon_threads_allowed(),
     _thread._get_main_thread_ident() == _thread.get_ident(), _thread._count(),
     type(_thread.get_ident()).__name__, type(_thread.get_native_id()).__name__)

# A lock.
lock = _thread.allocate_lock()
show("lock", lock.acquire(), lock.locked(), lock.acquire(False), lock.acquire(0), lock.acquire(timeout=0),
     lock.acquire(True, 0.01), lock.acquire(blocking=False))
show("repr", repr(lock).split(" object")[0])
lock.release()
show("released", lock.locked(), repr(lock).split(" object")[0], error(lock.release))
show("context", lock.__enter__(), lock.locked(), lock.__exit__(None, None, None), lock.locked())
with lock:
    show("with", lock.locked())
show("aliases", lock.acquire_lock(), lock.locked_lock(), lock.release_lock(), lock.locked())
for args, kwargs in [((False, 1), {}), ((True, -2), {}), ((True, 1e300), {}), ((True, float("nan")), {}),
                     ((True, "x"), {}), ((True, None), {}), ((True, -1, 3), {}), ((), {"wait": 1}),
                     ((True,), {"blocking": False})]:
    result = error(lock.acquire, *args, **kwargs)
    if result is True:
        lock.release()
    show("acquire", args, kwargs, result)
show("timeout max", lock.acquire(True, _thread.TIMEOUT_MAX), lock.acquire(True, 0.0), lock.locked())
lock.release()

# A reentrant lock.
rlock = _thread.RLock()
show("rlock", rlock.acquire(), rlock.acquire(), rlock._is_owned(), rlock._recursion_count(), rlock.locked())
show("rrepr", repr(rlock).split(" owner")[0], "count=2" in repr(rlock))
rlock.release()
rlock.release()
show("rreleased", rlock.locked(), rlock._is_owned(), rlock._recursion_count(), error(rlock.release))
with rlock:
    state = rlock._release_save()
    show("saved", state[0], state[1] == _thread.get_ident(), rlock.locked(), rlock._is_owned())
    rlock._acquire_restore(state)
    show("restored", rlock._recursion_count(), rlock._is_owned())
show("rlock acquire", error(rlock.acquire, False, 1), error(rlock.acquire, True, -1, 3))

# The arguments of starting a thread.
show("start", error(_thread.start_new_thread, 1, ()), error(_thread.start_new_thread, print, []),
     error(_thread.start_new_thread, print, (), []), error(_thread.start_joinable_thread, 1))
show("stack", _thread.stack_size(), error(_thread.stack_size, 100).split(":")[0], _thread.stack_size(0))

# Threads finish, and joining waits for them.
done = []
handles = [_thread.start_joinable_thread(lambda k=k: done.append(k)) for k in range(4)]
for handle in handles:
    handle.join()
show("joined", sorted(done), [handle.is_done() for handle in handles], handles[0].join(), type(handles[0].ident).__name__)
show("self", error(_thread._make_thread_handle(_thread.get_ident()).join))

# A thread started by start_new_thread signals with a lock.
finished = _thread.allocate_lock()
finished.acquire()
seen = []
def started(a, b, c=None):
    seen.append((a, b, c, _thread.get_ident() != _thread._get_main_thread_ident()))
    finished.release()
show("ident", type(_thread.start_new_thread(started, (1, 2), {"c": 3})).__name__)
finished.acquire()
show("ran", seen)

# An exception leaving a thread goes to sys.unraisablehook; SystemExit does not.
reports = []
def hook(unraisable):
    reports.append((unraisable.exc_type.__name__, str(unraisable.exc_value),
                    unraisable.err_msg.split(" <")[0], unraisable.object,
                    unraisable.exc_traceback.tb_frame.f_code.co_name))
sys.unraisablehook = hook
def fails():
    raise ValueError("from a thread")
def leaves():
    raise SystemExit(3)
for function in (fails, leaves, _thread.exit):
    _thread.start_joinable_thread(function).join()
sys.unraisablehook = sys.__unraisablehook__
show("reported", reports)

# Contention: a lock keeps a read-modify-write whole.
counter = [0]
guard = _thread.allocate_lock()
def add():
    for _ in range(2000):
        with guard:
            value = counter[0]
            counter[0] = value + 1
workers = [_thread.start_joinable_thread(add) for _ in range(4)]
for worker in workers:
    worker.join()
show("counted", counter[0])

# A thread that never waits still lets the others run.
flags = {"started": False, "stop": False}
def spin():
    flags["started"] = True
    while not flags["stop"]:
        pass
spinner = _thread.start_joinable_thread(spin)
while not flags["started"]:
    pass
flags["stop"] = True
spinner.join()
show("switched", flags)

# Waiting with a timeout, and being woken by another thread.
held = _thread.allocate_lock()
held.acquire()
show("timed out", held.acquire(True, 0.05))
def wake():
    held.release()
_thread.start_new_thread(wake, ())
show("woken", held.acquire(True, 10))

# _shutdown waits for threads that are not daemons.
late = []
gate = _thread.allocate_lock()
gate.acquire()
def last():
    gate.acquire()
    late.append(1)
_thread.start_joinable_thread(last, daemon=False)
gate.release()
_thread._shutdown()
show("shutdown", late)
