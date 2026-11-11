# spec: PLS-315 27.2.4, 9.7
# description: A frame that outlives its generator does not keep the
# generator: once the generator's last reference goes, by reference count or
# by a collection of the cycle holding it, it is closed and its weak
# references are dead, while the frame lives on without naming it.
from harness import *

log = []

def suspended():
    try:
        yield 1
    finally:
        log.append("closed")

def results():
    del log[:]
    out = []
    g = suspended(); next(g)
    frame = g.gi_frame
    ref = host.weak_reference(g)
    del g
    out += [ref() is None, frame.f_generator, frame.f_code.co_name]
    holder = []
    g = suspended(); next(g)
    holder.append(holder); holder.append(g)
    cycle_frame = g.gi_frame
    cycle_ref = host.weak_reference(g)
    del g, holder
    host.collect()
    out += [cycle_ref() is None, cycle_frame.f_generator, list(log)]
    return out

expected = [True, None, "suspended", True, None, ["closed", "closed"]]

assert_eq(results(), expected)
assert_eq(results(), expected)
