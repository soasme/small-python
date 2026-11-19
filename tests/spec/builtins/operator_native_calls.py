# spec: PLS-315 26.1.2, 23.1.8, 23.6
# description: a dict's |= of a mapping instance merges it by its Python
# keys() and __getitem__, of an iterable instance by its pairs from its
# Python __iter__, in order, binding the same dict, an error from keys()
# propagating and a value with neither raising TypeError; a str
# subclass's % of a tuple or dict converts each value by its Python
# __str__ or __repr__ in order and gives a str. Inside functions and
# generators as at module level.
from harness import *
log = []
class Mapping:
    def keys(self):
        for _ in (): pass
        log.append("keys")
        return ["a", "b"]
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("getitem", key))
        return key * 2
class Pairs:
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return iter([("p", 1)])
class Failing:
    def keys(self): raise ValueError("keys")
class Text(str): pass
class Shown:
    def __str__(self):
        for _ in (): pass
        log.append("str")
        return "s"
    def __repr__(self):
        for _ in (): pass
        log.append("repr")
        return "R"
def run(f):
    del log[:]
    try: result = f()
    except Exception as error: result = (type(error).__name__, str(error))
    return result, list(log)
def ior(source):
    d = {"z": 0}
    alias = d
    d |= source
    return d, alias is d
def cases():
    return [run(lambda: ior(Mapping())), run(lambda: ior(Pairs())), run(lambda: ior(Failing())), run(lambda: ior(object())),
            run(lambda: Text("%s-%r") % (Shown(), Shown())), run(lambda: type(Text("%s") % (Shown(),)).__name__),
            run(lambda: Text("%(k)s|%(k)r") % {"k": Shown()})]
def gen():
    yield cases()
expected = [(({'z': 0, 'a': 'aa', 'b': 'bb'}, True), ['keys', ('getitem', 'a'), ('getitem', 'b')]),
            (({'z': 0, 'p': 1}, True), ['iter']),
            (('ValueError', 'keys'), []),
            (('TypeError', "'object' object is not iterable"), []),
            ('s-R', ['str', 'repr']),
            ('str', ['str']),
            ('s|R', ['str', 'repr'])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
