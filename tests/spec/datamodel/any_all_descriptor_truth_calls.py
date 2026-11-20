# spec: PLS-315 7.5.6, 7.3.2, 19.3.1
# description: any() and all() take each item's truth as a test does,
# through descriptors too: a __bool__ read raising AttributeError is
# absent, its __len__'s result's truth then taken unchecked, or true
# when that read raises AttributeError too; a __bool__ read's result
# must return a bool; a __len__ descriptor's result is checked as a
# length; any other error of a read propagates. A list's items and a
# generator's agree, each read once.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def getter(n):
    def get(self):
        log.append(("get", n)); return lambda: n
    return property(get)
def length(n):
    def __len__(self):
        for _ in (): pass
        log.append(("len", n)); return n
    return __len__
cases = [{"__bool__": property(booh), "__len__": length(0)}, {"__bool__": property(booh), "__len__": length(-1)},
         {"__bool__": property(booh), "__len__": property(booh)}, {"__bool__": property(booh), "__len__": getter(0)},
         {"__bool__": property(booh), "__len__": property(boom)}, {"__bool__": property(booh)},
         {"__bool__": getter(True)}, {"__bool__": getter(1)}, {"__len__": getter(3)}, {"__len__": property(booh)},
         {"__bool__": property(booh), "__len__": len}]
def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__
def run():
    for _ in (): pass
    del log[:]
    out = []
    for d in cases:
        k = type("K", (), d)
        out.append((attempt(lambda: any([0, k()])), attempt(lambda: all([1, k()])), attempt(lambda: any(x for x in [k()]))))
    return out, list(log)

expected = ([(False, False, False), (True, True, True), (True, True, True), (False, False, False), ('KeyError', 'KeyError', 'KeyError'), (True, True, True), (True, True, True), ('TypeError', 'TypeError', 'TypeError'), (True, True, True), ('AttributeError', 'AttributeError', 'AttributeError'), ('TypeError', 'TypeError', 'TypeError')], [('len', 0), ('len', 0), ('len', 0), ('len', -1), ('len', -1), ('len', -1), ('get', 0), ('get', 0), ('get', 0), ('get', True), ('get', True), ('get', True), ('get', 1), ('get', 1), ('get', 1), ('get', 3), ('get', 3), ('get', 3)])

assert_eq(run(), expected)
assert_eq(run(), expected)
