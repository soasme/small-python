# spec: PLS-315 9.7, 27.2.4
# description: An asynchronous generator in a cycle with its own frame,
# suspended in a handler, whose close a collection's finalizer runs but
# whose finally ignores the GeneratorExit by yielding, stays suspended;
# later collections reclaim it, its frame, its locals and the exception it
# handles, and the values allocated after them stay intact.
from harness import assert_eq, host
host.disable_automatic_collection()
log = []
refs = {}
class E(Exception): pass
class Local: pass
async def agen(box):
    local = Local()
    refs["local"] = host.weak_reference(local)
    try:
        raise E
    except E as e:
        refs["e"] = host.weak_reference(e)
        try:
            yield 1
        finally:
            log.append("finally")
            yield 2
def make():
    box = []
    a = agen(box); box.append(a); box.append(a.ag_frame)
    try: a.asend(None).send(None)
    except StopIteration as stop: assert_eq(stop.value, 1)
make()
for _ in range(3): host.collect()
assert_eq((log, refs["e"]() is None, refs["local"]() is None), (["finally"], True, True))
def closure(i):
    def get(): return i
    return get
kept = [closure(i) for i in range(500)]
for _ in range(2): host.collect()
assert_eq(sum(f() for f in kept), 124750)
