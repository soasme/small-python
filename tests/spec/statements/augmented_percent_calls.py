# spec: PLS-315 14.3, 23.6
# description: an augmented %= of a str, bytes or bytearray target by a
# list, tuple or dict reaching an item with a Python __repr__ or __str__,
# which may loop, converts the items in order as % does, the target bound
# to the new value; a name, subscription or attribute target, an error
# stopping the formatting and leaving the target unchanged. Inside
# functions and generators as at module level.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __repr__(self):
        for _ in (): pass
        log.append("r%d" % self.v)
        return "K%d" % self.v
    def __str__(self):
        for _ in (): pass
        log.append("s%d" % self.v)
        return "k%d" % self.v

class Bad:
    def __repr__(self):
        for _ in (): pass
        return 1

class Box: pass

def calls():
    text = "<%s>"
    text %= [K(1)]
    held = ["%s|%r"]
    held[0] %= ([K(2)], {1: K(3)})
    box = Box(); box.t = "%a"
    box.t %= ([K(4)],)
    data = before = bytearray(b"%r")
    data %= [K(5)]
    return text, held[0], box.t, data, data is not before, before

assert_eq(calls(), ("<[K1]>", "[K2]|{1: K3}", "[K4]", bytearray(b"[K5]"), True, bytearray(b"%r")))
assert_eq(log, ["r1", "r2", "r3", "r4", "r5"])
log.clear()

text = "%s"
text %= ([K(6)],)
assert_eq(text, "[K6]")

def errors():
    t = "%s %s"
    try: t %= ([K(7)], [Bad()])
    except TypeError as e: return t, str(e)

assert_eq(errors(), ("%s %s", "Bad.__repr__() must return a str, not int"))

def gen():
    t = "%r"
    t %= [K(8)]
    yield t

assert_eq(list(gen()), ["[K8]"])
assert_eq(log, ["r6", "r7", "r8"])
