# spec: PLS-315 13.3.4, 26.1.3
# description: A call's duplicate keyword names its callee by reading
# __qualname__ and __module__ through a Python __getattribute__ or
# __getattr__, which may loop, or by str() of a callee without
# __qualname__; an error naming it makes the name "function". A function
# holding a Python keys() is a mapping to **, a dict display, dict() and
# dict.update().
from harness import *

log = []
class Named:
    def __getattribute__(self, name):
        for _ in (): pass
        log.append(name)
        if name == "__qualname__": return "Qual"
        if name == "__module__": return "mod"
        return object.__getattribute__(self, name)
    def __call__(self, **k): return k
class Asked:
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name)
        if name == "__qualname__": return "Q"
        raise AttributeError(name)
    def __call__(self, **k): return k
class Unnamed:
    def __getattribute__(self, name):
        if name == "__qualname__": raise AttributeError(name)
        return object.__getattribute__(self, name)
    def __str__(self):
        for _ in (): pass
        log.append("str"); return "unnamed"
    def __call__(self, **k): return k
class Represented(Unnamed):
    __str__ = object.__str__
    def __repr__(self):
        for _ in (): pass
        log.append("repr"); return "represented"
class BadStr(Unnamed):
    def __str__(self): log.append("str"); return 1
class Failing:
    def __getattribute__(self, name):
        if name == "__module__": raise ValueError(name)
        if name == "__qualname__": return "F"
        return object.__getattribute__(self, name)
    def __call__(self, **k): return k
def run(f):
    del log[:]
    try: f()
    except TypeError as e: return str(e), list(log)
for callee, name, read in [(Named(), "mod.Qual()", ["__qualname__", "__module__"]), (Asked(), "__main__.Q()", ["__qualname__"]),
                           (Unnamed(), "unnamed", ["str"]), (Represented(), "represented", ["repr"]), (BadStr(), "function", ["str"]),
                           (Failing(), "function", [])]:
    message = name + " got multiple values for keyword argument 'a'"
    assert_eq(run(lambda: callee(**{"a": 1}, **{"a": 2})), (message, read))
    assert_eq(run(lambda: callee(**{"a": 1}, a=2)), (message, read))
    assert_eq(run(lambda: callee(a=1, **{"b": 0, "a": 2})), (message, read))

def holder(): pass
def keys():
    for _ in (): pass
    log.append("keys"); return ["a"]
holder.keys = keys
def g(**k): return k
not_subscriptable = "'function' object is not subscriptable"
for f in (lambda: g(**holder), lambda: {**holder}, lambda: dict(holder), lambda: {}.update(holder), lambda: g(b=1, **holder)):
    assert_eq(run(f), (not_subscriptable, ["keys"]))

# A callable instance, which has no __qualname__, is named by its str():
# object's repr, or a native __repr__'s text.
class UnnamedCallable:
    def __call__(self, **kw): return kw
class NativeShownCallable(UnnamedCallable):
    __repr__ = "shown".__str__
unnamed_messages = []
for unnamed in (UnnamedCallable(), NativeShownCallable()):
    try: unnamed(**{"a": 1}, **{"a": 2})
    except TypeError as e: unnamed_messages.append(str(e))
object_shown, rest = unnamed_messages[0].split(" object at ")
assert_eq([object_shown, rest.split("> ")[1], unnamed_messages[1]],
          ["<" + __name__ + ".UnnamedCallable", "got multiple values for keyword argument 'a'", "shown got multiple values for keyword argument 'a'"])
