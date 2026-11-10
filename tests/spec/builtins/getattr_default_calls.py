# spec: PLS-315 19.3.11, 7.3.4
# description: getattr() of an instance, a str and a default reads the
# instance's own entry or calls the Python property getter, __get__,
# __getattribute__ or __getattr__ that reading the attribute calls; their
# value is getattr()'s, an AttributeError from any of them or from the
# lookup gives the default, and another exception propagates, with plain
# and computed operands, in an expression and an assignment, inside
# functions as at module level. hasattr() calls them alike: a value, even
# a false one, gives True and an AttributeError False.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Gets:
    def __get__(self, instance, owner):
        spin()
        log.append("get")
        raise AttributeError("get")

class Plain:
    d = Gets()
    @property
    def p(self):
        spin()
        log.append("p")
        return "p"
    @property
    def bad(self):
        spin()
        log.append("bad")
        raise AttributeError("bad")
    @property
    def key(self):
        spin()
        raise KeyError("key")

class Fallback:
    def __getattr__(self, name):
        spin()
        log.append(name)
        if name == "miss": raise AttributeError(name)
        return name * 2

class Items(list):
    @property
    def p(self):
        spin()
        return len(self)

class Hooked:
    def __getattribute__(self, name):
        spin()
        if name == "miss": raise AttributeError(name)
        return name.upper()

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    plain, fallback, hooked = Plain(), Fallback(), Hooked()
    holder = [plain, fallback, Items([1, 2]), hooked]
    stored = getattr(plain, "bad", "stored")
    plain.o = "own"
    out = [getattr(plain, "p", 0), stored, getattr(plain, "nothing", 1), getattr(plain, "d", 2),
           getattr(fallback, "ab", 0), getattr(fallback, "miss", 3), getattr(holder[2], "p", 0),
           getattr(holder[0], "bad", 4), getattr(holder[1], "miss", 5), getattr(hooked, "h", 0),
           getattr(holder[3], "miss", 6), error(lambda: getattr(plain, "key", 0)),
           error(lambda: getattr(holder[0], "key", 0)), getattr(plain, "o", 7), getattr(plain, "o")]
    out.append(list(log))
    del log[:]
    out.append([hasattr(plain, "p"), hasattr(plain, "bad"), hasattr(fallback, "ab"), hasattr(holder[1], "miss"),
                hasattr(Items(), "p"), hasattr(hooked, "h"), hasattr(holder[3], "miss"), hasattr(plain, "o"),
                hasattr(plain, "nothing"), error(lambda: hasattr(plain, "key")), list(log)])
    return out

expected = ["p", "stored", 1, 2, "abab", 3, 2, 4, 5, "H", 6, ("KeyError", "'key'"), ("KeyError", "'key'"), "own", "own",
            ["bad", "p", "get", "ab", "miss", "bad", "miss"],
            [True, False, True, False, True, True, False, True, False, ("KeyError", "'key'"), ["p", "bad", "ab", "miss"]]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
