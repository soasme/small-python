# spec: PLS-315 23.4
# description: a format field's name looks up its first part in the
# positional arguments or the keywords' mapping, by its Python
# __getitem__ or a dict subclass's __missing__, then each .attribute (a
# property's getter, __getattr__ when the lookup fails) and [index] (a
# Python __getitem__) in order, before the field converts and formats its
# object; numbering counts each field once; a lookup's error propagates.
# Inside functions and generators as at module level.
from harness import *
log = []
class Shown:
    def __format__(self, spec):
        for _ in (): pass
        log.append(("format", spec))
        return "F" + spec
    def __repr__(self): return "R"
class Missing(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(("missing", key))
        return Shown()
class Looked(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("getitem", key))
        return dict.__getitem__(self, key)
class Seq:
    def __getitem__(self, i):
        for _ in (): pass
        log.append(("seq", i))
        return [Shown(), "x"][i]
class Obj:
    @property
    def p(self):
        for _ in (): pass
        log.append("property")
        return Seq()
    def __getattr__(self, name):
        for _ in (): pass
        log.append(("getattr", name))
        return name.upper()
def run(f):
    del log[:]
    try: result = f()
    except Exception as error: result = (type(error).__name__, str(error))
    return result, list(log)
def cases():
    return [run(lambda: "{a}|{b:>3}|{c!r}".format_map(Missing(a=1))),
            run(lambda: "{x}{y}".format_map(Looked(x=Shown(), y=2))),
            run(lambda: "{0[0]:q}{0[1]}".format(Seq())),
            run(lambda: "{0.p[0]:z}|{0.zz}|{1}".format(Obj(), 3)),
            run(lambda: "{.zz}-{}".format(Obj(), 5)),
            run(lambda: "{k.p[1]!r:>4}".format(k=Obj())),
            run(lambda: "{x:{y.w}}".format(x=7, y=Obj())),
            run(lambda: "{a[nokey]}".format(a=Looked())),
            run(lambda: "{a.p.q}".format(a=Obj())),
            run(lambda: "{}{0.zz}".format(Obj())),
            run(lambda: "{a}".format_map(Missing()))]
def gen():
    yield cases()
expected = [('1|F>3|R', [('missing', 'b'), ('format', '>3'), ('missing', 'c')]),
            ('F2', [('getitem', 'x'), ('format', ''), ('getitem', 'y')]),
            ('Fqx', [('seq', 0), ('format', 'q'), ('seq', 1)]),
            ('Fz|ZZ|3', ['property', ('seq', 0), ('format', 'z'), ('getattr', 'zz')]),
            ('ZZ-5', [('getattr', 'zz')]),
            (" 'x'", ['property', ('seq', 1)]),
            (('ValueError', "Unknown format code 'W' for object of type 'int'"), [('getattr', 'w')]),
            (('KeyError', "'nokey'"), [('getitem', 'nokey')]),
            (('AttributeError', "'Seq' object has no attribute 'q'"), ['property']),
            (('ValueError', 'cannot switch from automatic field numbering to manual field specification'), []),
            ('F', [('missing', 'a'), ('format', '')])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
