# spec: PLS-315 7.4.3, 13.3.4
# description: The keywords a call gathers that bind no parameter go to a
# new **kwargs dict in call order, each stored under its name by key
# equality with the names stored before it: a str subclass's name of equal
# hash is compared by its __eq__ (the reflected one of a stored str's
# first), a true result replacing the stored value under the first name, a
# false one storing both, and an exception propagating from the call. Such
# a name is compared with the parameter names first. A name whose class
# has a Python __hash__ keeps the hash its dict stored. Inside functions as
# at module level.
from harness import *

log = []

class Odd(str):
    __hash__ = str.__hash__
    def __init__(self, text):
        self.answers = []
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((str(self), str(other)))
        answer = self.answers.pop(0) if self.answers else False
        if answer == "raise": raise LookupError(str(self))
        return answer

class Hashed(Odd):
    def __hash__(self):
        log.append(("hash", str(self)))
        return str.__hash__(self)

def f(a=0, **kw):
    return sorted((type(k).__name__, str(k), v) for k, v in kw.items())

def name(cls, text, *answers):
    n = cls(text)
    n.answers = list(answers)
    return n

def run(first, second):
    del log[:]
    try:
        r = f(**first, **second)
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    return r, log[:]

def results():
    return [
        # The merge's comparison is false, the store's true: one name, the later value.
        run({"x": 0}, {name(Odd, "x", False, True): 1}),
        # Both false: both names.
        run({"x": 0}, {name(Odd, "x", False, False): 1}),
        # The store's comparison raises.
        run({"x": 0}, {name(Odd, "x", False, "raise"): 1}),
        # Truth of a non-bool result.
        run({"x": 0}, {name(Odd, "x", False, 1): 1}),
        # A name bound to a parameter is not stored.
        run({"a": 5}, {name(Odd, "z", False): 1}),
    ]

expected = [
    ([("str", "x", 1)], [("x", "x"), ("x", "x")]),
    ([("Odd", "x", 1), ("str", "x", 0)], [("x", "x"), ("x", "x"), ("x", "a"), ("x", "x")]),
    ("LookupError: x", [("x", "x"), ("x", "x")]),
    ([("str", "x", 1)], [("x", "x"), ("x", "x")]),
    ([("Odd", "z", 1)], [("z", "a")]),
]

def main():
    return results()

# A Python __hash__ ran when its dict was made; the merge and the store compare.
assert_eq(run({"y": 0}, {name(Hashed, "y", False, True): 1}), ([("str", "y", 1)], [("y", "y"), ("y", "y")]))

assert_eq(results(), expected)
assert_eq(main(), expected)

# A native __eq__ raising there propagates too, from the parameter name's
# comparison or the stored name's.
native_answers = {"a": False}
class NativeEqName(str):
    def __hash__(self): return hash("a")
    __eq__ = native_answers.__getitem__
native_kw = {"a": 1}
native_kw[NativeEqName("b")] = 2
del native_answers["a"]
def native_only(**kw): return len(kw)
def native_param(x=0, **kw): return len(kw)
native_errors = []
for native_call in (lambda: native_only(**native_kw), lambda: native_param(**native_kw), lambda: native_param(1, **native_kw), lambda: native_only(z=0, **native_kw)):
    try: native_call()
    except KeyError as e: native_errors.append(e.args)
assert_eq(native_errors, [("a",), ("x",), ("x",), ("a",)])
