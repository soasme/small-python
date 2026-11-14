# spec: PLS-315 7.5.1, 7.5.2, 13.12, 20.3
# description: truth testing by bool(), not, if, and, or, filter(), any()
# and all() of an instance of a builtin subclass calls its class's Python
# __bool__, or with none its __len__, unless its builtin is a number,
# whose own truth comes first; that of a class calls its metaclass's; a
# bad result is an error from every test, and a not that raises gives no
# value to the call around it; inside functions as at module level.
from harness import *

log = []

class Listed(list):
    def __bool__(self):
        for i in range(2): pass
        log.append("bool"); return False
class Sized(list):
    def __len__(self): log.append("len"); return 0
class Counted(int):
    def __len__(self): log.append("ilen"); return 0
class Real(float):
    def __bool__(self): log.append("fbool"); return True
class Meta(type):
    def __bool__(cls):
        for i in range(2): pass
        log.append("mbool"); return False
class C(metaclass=Meta): pass
class MetaLen(type):
    def __len__(cls): log.append("mlen"); return 0
class D(metaclass=MetaLen): pass
class Plain(type): pass
class E(metaclass=Plain): pass
class Bad(str):
    def __bool__(self): return 1
class BadMeta(type):
    def __len__(cls): return -1
class B(metaclass=BadMeta): pass

def name(e): return type(e).__name__ + ": " + str(e)

def tests(v):
    r = []
    try: r.append(bool(v))
    except Exception as e: r.append(name(e))
    try: r.append(not v)
    except Exception as e: r.append(name(e))
    try:
        if v: r.append("if")
    except Exception as e: r.append(name(e))
    try: r.append(v and 1); r.append(v or 2)
    except Exception as e: r.append(name(e))
    out = (r, log[:])
    del log[:]
    return out

listed, sized, real, bad = Listed([1]), Sized([1]), Real(0.0), Bad("x")
bad_bool = "TypeError: Bad.__bool__() must return a bool, not int"
bad_len = "ValueError: __len__() should return >= 0"
cases = [
    (listed, ([False, True, listed, 2], ["bool"] * 5)),
    (sized, ([False, True, sized, 2], ["len"] * 5)),
    (Counted(5), ([True, False, "if", 1, 5], [])),
    (Counted(0), ([False, True, 0, 2], [])),
    (real, ([True, False, "if", 1, real], ["fbool"] * 5)),
    (C, ([False, True, C, 2], ["mbool"] * 5)),
    (D, ([False, True, D, 2], ["mlen"] * 5)),
    (E, ([True, False, "if", 1, E], [])),
    (bad, ([bad_bool] * 4, [])),
    (B, ([bad_len] * 4, [])),
]

def run():
    out = [tests(v) for v, _ in cases]
    l = Listed()
    out.append((list(filter(None, [l, C, Counted(0), D, Sized()])), any([C, D, l]), all([l, C]), log[:]))
    del log[:]
    return out

expected = [e for _, e in cases] + [([], False, False, ["bool", "mbool", "mlen", "len", "mbool", "mlen", "bool", "bool"])]
assert_eq(run(), expected)
assert_eq(tests(C), expected[5])

# A not that raises leaves the call around it uncalled.
def args(*a):
    log.append(a)
    return a

def raising():
    try: args(not bad)
    except TypeError as e: log.append(str(e))
    try: args(not B)
    except ValueError as e: log.append(str(e))
    out = log[:]
    del log[:]
    return out

assert_eq(raising(), [bad_bool[len("TypeError: "):], bad_len[len("ValueError: "):]])
