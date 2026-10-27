# spec: PLS-315 13.17
# description: Expressions evaluate left to right; an assignment's right side before its targets.
from harness import *

log = []
def e(n, value=None):
    log.append(n)
    return n if value is None else value

def order(thunk):
    log.clear()
    thunk()
    return list(log)

assert_eq(order(lambda: (e(1), e(2), e(3), e(4))), [1, 2, 3, 4])
assert_eq(order(lambda: [e(1), e(2), e(3), e(4)]), [1, 2, 3, 4])
assert_eq(order(lambda: {e(1): e(2), e(3): e(4)}), [1, 2, 3, 4])
assert_eq(order(lambda: {e(1), e(2)}), [1, 2])
assert_eq(order(lambda: e(1) + e(2) * (e(3) - e(4))), [1, 2, 3, 4])
assert_eq(order(lambda: e(1, lambda *a, **k: None)(e(2), e(3), *e(4, []), **e(5, {}))), [1, 2, 3, 4, 5])
assert_eq(order(lambda: e(1, [0])[e(2, 0)]), [1, 2])
assert_eq(order(lambda: e(1) < e(2) < e(3)), [1, 2, 3])
assert_eq(order(lambda: e(1, 0) or e(2)), [1, 2])
assert_eq(order(lambda: e(1) if e(2) else e(3)), [2, 1])
assert_eq(order(lambda: f"{e(1)}{e(2)}"), [1, 2])

class Target:
    def __setattr__(self, name, value):
        log.append(("set", name))
t = Target()
log.clear()
t.a, t.b = e(1), e(2)
assert_eq(log, [1, 2, ("set", "a"), ("set", "b")])

# Targets: subscript container and key are evaluated left to right, after the value.
class Box:
    def __setitem__(self, key, value):
        log.append(("setitem", key, value))
box = Box()
log.clear()
e(2, box)[e(3, "k")] = e(1, "v")
assert_eq(log, [1, 2, 3, ("setitem", "k", "v")])

# Augmented assignment evaluates the target's parts once, before the value.
class Aug:
    def __getitem__(self, key):
        log.append(("get", key))
        return 0
    def __setitem__(self, key, value):
        log.append(("set", key, value))
log.clear()
e(1, Aug())[e(2, "k")] += e(3, 5)
assert_eq(log, [1, 2, ("get", "k"), 3, ("set", "k", 5)])

# Chained assignment assigns targets left to right.
log.clear()
t.a = t.b = e(1)
assert_eq(log, [1, ("set", "a"), ("set", "b")])

# Positional and * arguments evaluate before keyword and ** arguments (13.3.4).
log.clear()
(lambda *a, **k: None)(e(1), k=e(3), *[e(2)], **{"z": e(4)})
assert_eq(log, [1, 2, 3, 4])
