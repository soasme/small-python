# spec: PLS-315 23.4
# description: str.format_map of a dict subclass's instance finds its
# fields in it, the class's __missing__ answering a missing one and its
# Python __getitem__ asked for each when it has one, and formats each by
# its value's Python __format__ and a container's items by their Python
# __repr__, in field order. Inside functions and generators as at module
# level.
from harness import *
log = []
class Shown:
    def __init__(self, name): self.name = name
    def __format__(self, spec):
        for _ in (): pass
        log.append(("format", self.name, spec))
        return self.name + spec
    def __repr__(self):
        for _ in (): pass
        log.append(("repr", self.name))
        return "R" + self.name
class Plain(dict): pass
class Missing(dict):
    def __missing__(self, key):
        log.append(("missing", key))
        return Shown(key)
class Looked(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("getitem", key))
        return dict.__getitem__(self, key)
def run(f):
    del log[:]
    try: result = f()
    except Exception as error: result = (type(error).__name__, str(error))
    return result, list(log)
def cases():
    a, b = Shown("a"), Shown("b")
    return [run(lambda: "{x:>}|{y}|{z!r}".format_map(Plain(x=a, y=[b], z=a))),
            run(lambda: "{x}{w:2}".format_map(Missing(x=b))),
            run(lambda: "{x[0]}{x}".format_map(Plain(x=(a, b)))),
            run(lambda: "{x}{y}".format_map(Looked(x=a, y=b))),
            run(lambda: "{q}".format_map(Plain())),
            run(lambda: str.format_map("{x:{y}}", Plain(x=a, y="5")))]
def gen():
    yield cases()
expected = [('a>|[Rb]|Ra', [('format', 'a', '>'), ('repr', 'b'), ('repr', 'a')]),
            ('bw2', [('format', 'b', ''), ('missing', 'w'), ('format', 'w', '2')]),
            ('a(Ra, Rb)', [('format', 'a', ''), ('repr', 'a'), ('repr', 'b')]),
            ('ab', [('getitem', 'x'), ('format', 'a', ''), ('getitem', 'y'), ('format', 'b', '')]),
            (('KeyError', "'q'"), []),
            ('a5', [('format', 'a', '5')])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
