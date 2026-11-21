# spec: PLS-315 9.3.2
# description: A builtins dict whose key for a name is not a str but has
# its hash and a Python __eq__, which may loop, compares once for each
# evaluation of the name, as a call's callee, its argument or both, in a
# nested call, before NameError for a name it does not match, and passing
# an exception __eq__ raises.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
builtins_dict = vars(len.__self__)
class Key:
    def __init__(self, name): self.name = name
    def __hash__(self): return hash(self.name)
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", other)); return other == self.name
def swap(name):
    value = builtins_dict.pop(name)
    builtins_dict[Key(name)] = value
    return value
orig_len, orig_abs = swap("len"), swap("abs")
def f(x):
    return len(x)
emit(f([1, 2]), log); log.clear()
def g(x):
    return orig_len([abs, len])
emit(g(0), log); log.clear()
def h(x):
    return max(len(x), abs(-3))
emit(h("ab"), log); log.clear()
def missing():
    return nothere(1)
try: missing()
except NameError as e: emit("ne", e, log); log.clear()
class Boom:
    def __hash__(self): return hash("boom_name")
    def __eq__(self, other):
        for _ in (): pass
        raise KeyError("eq")
builtins_dict[Boom()] = 1
def boom():
    return emit(boom_name)
try: boom()
except KeyError as e: emit("ke", e)
def twice(x):
    return orig_abs(len(x) - len(x))
emit(twice([1]), log); log.clear()
for k in [k for k in builtins_dict if not isinstance(k, str)]: del builtins_dict[k]
builtins_dict["len"] = orig_len; builtins_dict["abs"] = orig_abs
emit(len([1]), log)
EXPECTED = [
    "2 [('eq', 'len')]",
    "2 [('eq', 'abs'), ('eq', 'len')]",
    "3 [('eq', 'len'), ('eq', 'abs')]",
    "ne name 'nothere' is not defined []",
    "ke 'eq'",
    "0 [('eq', 'len'), ('eq', 'len')]",
    '1 []',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
