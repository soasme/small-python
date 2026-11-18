# spec: PLS-315 21.4.3
# description: split() and subgroup() of an exception group test it, then
# each of its exceptions in order, descending into a nested group that
# does not match, by a Python condition that may loop; each split group's
# matches and then its rest derive a group by its class's Python derive,
# which may loop, the derived group taking the original's notes, cause and
# context. A whole match is the group itself; a derive that returns no
# group raises TypeError; an exception from the condition or derive
# propagates. A group nested past the recursion limit splits. Called as a
# method, bound and called later, or unbound from the class; inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def name(e):
    return type(e).__name__ + (":" + e.message if isinstance(e, BaseExceptionGroup) else ":" + str(e))

def cond(e):
    spin(); log.append(name(e))
    return isinstance(e, ValueError)

class Mine(ExceptionGroup):
    def derive(self, excs):
        spin(); log.append(("derive", self.message, len(excs)))
        return Mine(self.message + "'", excs)

class Bad(ExceptionGroup):
    def derive(self, excs):
        return ValueError("no")

class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self): spin(); log.append("bool"); return self.v

def shape(e):
    if e is None: return None
    if isinstance(e, BaseExceptionGroup): return (type(e).__name__, e.message, [shape(x) for x in e.exceptions])
    return name(e)

def tree():
    inner = Mine("inner", [ValueError(1), TypeError(2)])
    outer = Mine("outer", [inner, ValueError(3), KeyError(4)])
    outer.add_note("n")
    outer.__cause__ = OSError("c")
    return outer

def run(f):
    del log[:]
    try:
        r = f()
        r = [shape(x) for x in r] if isinstance(r, tuple) else shape(r)
    except Exception as e:
        r = (type(e).__name__, str(e))
    return r, list(log)

def results():
    g = tree()
    split = g.split
    out = [run(lambda: g.split(cond)), run(lambda: g.subgroup(cond)), run(lambda: split(cond)),
           run(lambda: ExceptionGroup.split(g, cond)), run(lambda: BaseExceptionGroup.subgroup(g, cond)),
           run(lambda: g.split(lambda e: (spin(), True)[1])), run(lambda: g.split(lambda e: Truth(isinstance(e, KeyError)))),
           run(lambda: g.split(ValueError)), run(lambda: g.subgroup((KeyError, TypeError))),
           run(lambda: Bad("b", [ValueError(1), KeyError(2)]).split(ValueError)),
           run(lambda: g.split(lambda e: 1 / 0 if isinstance(e, TypeError) else False)),
           run(lambda: g.split(1))]
    m, r = g.split(cond)
    out.append((m.__notes__, r.__notes__, m.__notes__ is g.__notes__, type(m.__cause__).__name__, r.__cause__ is g.__cause__,
                g.split(lambda e: True)[0] is g))
    return out

expected = [([('Mine', "outer'", [('Mine', "inner'", ['ValueError:1']), 'ValueError:3']),
            ('Mine', "outer'", [('Mine', "inner'", ['TypeError:2']), 'KeyError:4'])],
            ['Mine:outer',
            'Mine:inner',
            'ValueError:1',
            'TypeError:2',
            ('derive', 'inner', 1),
            ('derive', 'inner', 1),
            'ValueError:3',
            'KeyError:4',
            ('derive', 'outer', 2),
            ('derive', 'outer', 2)]),
            (('Mine', "outer'", [('Mine', "inner'", ['ValueError:1']), 'ValueError:3']),
            ['Mine:outer',
            'Mine:inner',
            'ValueError:1',
            'TypeError:2',
            ('derive', 'inner', 1),
            'ValueError:3',
            'KeyError:4',
            ('derive', 'outer', 2)]),
            ([('Mine', "outer'", [('Mine', "inner'", ['ValueError:1']), 'ValueError:3']),
            ('Mine', "outer'", [('Mine', "inner'", ['TypeError:2']), 'KeyError:4'])],
            ['Mine:outer',
            'Mine:inner',
            'ValueError:1',
            'TypeError:2',
            ('derive', 'inner', 1),
            ('derive', 'inner', 1),
            'ValueError:3',
            'KeyError:4',
            ('derive', 'outer', 2),
            ('derive', 'outer', 2)]),
            ([('Mine', "outer'", [('Mine', "inner'", ['ValueError:1']), 'ValueError:3']),
            ('Mine', "outer'", [('Mine', "inner'", ['TypeError:2']), 'KeyError:4'])],
            ['Mine:outer',
            'Mine:inner',
            'ValueError:1',
            'TypeError:2',
            ('derive', 'inner', 1),
            ('derive', 'inner', 1),
            'ValueError:3',
            'KeyError:4',
            ('derive', 'outer', 2),
            ('derive', 'outer', 2)]),
            (('Mine', "outer'", [('Mine', "inner'", ['ValueError:1']), 'ValueError:3']),
            ['Mine:outer',
            'Mine:inner',
            'ValueError:1',
            'TypeError:2',
            ('derive', 'inner', 1),
            'ValueError:3',
            'KeyError:4',
            ('derive', 'outer', 2)]),
            ([('Mine', 'outer', [('Mine', 'inner', ['ValueError:1', 'TypeError:2']), 'ValueError:3', 'KeyError:4']), None], []),
            ([('Mine', "outer'", ['KeyError:4']), ('Mine', "outer'", [('Mine', "inner'", ['ValueError:1', 'TypeError:2']), 'ValueError:3'])],
            ['bool', 'bool', 'bool', 'bool', ('derive', 'inner', 2), 'bool', 'bool', ('derive', 'outer', 1), ('derive', 'outer', 2)]),
            ([('Mine', "outer'", [('Mine', "inner'", ['ValueError:1']), 'ValueError:3']),
            ('Mine', "outer'", [('Mine', "inner'", ['TypeError:2']), 'KeyError:4'])],
            [('derive', 'inner', 1), ('derive', 'inner', 1), ('derive', 'outer', 2), ('derive', 'outer', 2)]),
            (('Mine', "outer'", [('Mine', "inner'", ['TypeError:2']), 'KeyError:4']), [('derive', 'inner', 1), ('derive', 'outer', 2)]),
            (('TypeError', 'derive must return an instance of BaseExceptionGroup'), []),
            (('ZeroDivisionError', 'division by zero'), []),
            (('TypeError', 'expected an exception type, a tuple of exception types, or a callable (other than a class)'), []),
            (['n'], ['n'], False, 'OSError', True, True)]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)

# A group nested past the recursion limit splits, its levels kept on the heap.
def nested(n):
    e = TypeError(1)
    for i in range(n): e = ExceptionGroup(str(i), [e, ValueError(i)])
    return e

def depth(e):
    d = 0
    while isinstance(e, BaseExceptionGroup): e = e.exceptions[0]; d += 1
    return d

m, r = nested(2000).split(TypeError)
assert_eq((depth(m), depth(r), len(m.exceptions), len(r.exceptions)), (2000, 2000, 1, 2))
