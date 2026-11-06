"""What virtual threads do where CPython's preempted threads differ
(docs/threads.md section 2); tests/std.py runs it under spy only. Each check
asserts; the last line counts them.
"""
import _thread
import sys

checks = 0


def check(condition, what):
    global checks
    assert condition, what
    checks += 1


def raised(function, *args):
    try:
        function(*args)
    except RuntimeError as caught:
        return str(caught)


NO_RUN = 'cannot block: no other thread can run until this one ends'

# A started thread runs only once the starting one blocks, and threads start
# in the order they were started.
order = []
handles = [_thread.start_joinable_thread(lambda k=k: order.append(k)) for k in range(3)]
check(order == [] and _thread._count() == 3, "nothing runs before a block")
handles[1].join()
check(order == [0, 1] and _thread._count() == 1, "a join runs threads in order up to its own")
handles[2].join()
check(order == [0, 1, 2] and _thread._count() == 0, "every thread ran once")

# A thread that never blocks keeps running: no preemption.
seen = []
spinner = _thread.start_joinable_thread(lambda: seen.append("ran"))
for _ in range(100000):
    pass
check(seen == [], "a busy thread is never switched away from")
spinner.join()

# Each thread has its own ident while it runs, and the main thread's is back
# after it.
idents = []
def note():
    idents.append((_thread.get_ident(), _thread.get_native_id()))
_thread.start_joinable_thread(note).join()
_thread.start_joinable_thread(note).join()
main = _thread.get_ident()
check(main == _thread._get_main_thread_ident() and len({main, idents[0][0], idents[1][0]}) == 3,
      "distinct idents")
check(all(a == b for a, b in idents), "a native id is the thread's ident")

# Threads stack: each that waits runs the next on top of it, and they resume
# in reverse as each one's condition holds.
arrived, left = [], []
gate = _thread.allocate_lock()
gate.acquire()
def meet(k):
    arrived.append(k)
    if len(arrived) == 4:
        gate.release()
    with gate:
        left.append(k)
workers = [_thread.start_joinable_thread(lambda k=k: meet(k)) for k in range(4)]
for worker in workers:
    worker.join()
check(arrived == [0, 1, 2, 3] and left == [3, 2, 1, 0], "nested waits resume last first")

# A wait that no thread can end raises instead of hanging; a timed wait
# times out at once.
held = _thread.allocate_lock()
held.acquire()
check(raised(held.acquire) == NO_RUN, "a blocking acquire with nothing to run raises")
check(held.acquire(True, 60) is False, "a timed acquire returns at once")
rheld = _thread.RLock()
def hold_rlock():
    rheld.acquire()
_thread.start_joinable_thread(hold_rlock).join()
check(raised(rheld.acquire) == NO_RUN, "an RLock another thread holds raises too")

# A thread under another resumes only when that one ends: the one above
# cannot wait for it, so its wait raises in that thread, which the hook
# reports, and the one below goes on.
reports = []
sys.unraisablehook = lambda unraisable: reports.append(str(unraisable.exc_value))
ping, pong = _thread.allocate_lock(), _thread.allocate_lock()
ping.acquire()
pong.acquire()
def bounce():
    ping.acquire()
    pong.release()
    ping.acquire()
_thread.start_joinable_thread(bounce)
ping.release()
check(pong.acquire(True, 60) is True, "the thread above ran until it blocked")
check(reports == [NO_RUN], "its wait for the thread below raised")

# Joining a thread that waits below this one raises in the joiner; the
# joined thread, with nothing left to run, raises in turn and ends.
inner = []
def outer():
    _thread.start_joinable_thread(lambda: inner.append(raised(first.join)))
    blocker.acquire()
blocker = _thread.allocate_lock()
blocker.acquire()
first = _thread.start_joinable_thread(outer)
check(raised(first.join) is None and inner == [NO_RUN], "a join of a buried thread raises")
check(reports == [NO_RUN, NO_RUN], "the joined thread's own wait raised")
sys.unraisablehook = sys.__unraisablehook__

print("virtual threads:", checks, "checks")
