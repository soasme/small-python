# spec: PLS-315 25.1.2, 19.3.32, 19.3.5, 19.3.16, 23.6
# description: the repr of a list's, tuple's, dict's, set's, frozenset's or
# frozendict's subclass instance that defines no __repr__ calls its items'
# __repr__ in order, a set's, frozenset's or frozendict's naming its type;
# so do str(), ascii(), format(), an f-string field, str.format and % of
# one defining no __str__ or __format__ either, and a staticmethod
# __repr__ of an item is called with no arguments. An instance holding
# itself shows [...]; an item's error propagates. Inside functions and
# generators as at module level.
from harness import *
log = []
class I:
    def __init__(self, t): self.t = t
    def __repr__(self):
        for _ in (): pass
        log.append(self.t)
        return self.t
class Static:
    __repr__ = staticmethod(lambda: (log.append("static"), "st")[1])
class Bad:
    def __repr__(self):
        for _ in (): pass
        log.append("bad")
        raise KeyError("bad")
class L(list): pass
class T(tuple): pass
class D(dict): pass
class S(set): pass
class F(frozenset): pass
class FD(frozendict): pass
class Own(list):
    def __str__(self): return "own"
def run(f):
    del log[:]
    try: result = f()
    except KeyError as error: result = ("KeyError", str(error))
    return result, list(log)
def shows(v):
    return [repr(v), str(v), ascii(v), format(v), f"{v}", f"{v!r:>3}", "{} {!a}".format(v, v), "%s %r" % (v, v)]
def cases():
    a, s = I("a"), Static()
    looped = L([a]); looped.append(looped)
    held = D({1: a}); held[2] = held
    return [run(lambda: shows(L([a, 1]))), run(lambda: shows(T((a,)))), run(lambda: shows(D({1: a}))),
            run(lambda: shows(S([a]))), run(lambda: shows(F([a]))), run(lambda: shows(FD({2: a}))),
            run(lambda: shows([L([s]), (S([s]),)])), run(lambda: [repr(looped), str(held)]),
            run(lambda: [repr(Own([a])), str(Own([a])), f"{Own([a])}"]), run(lambda: repr(L([a, Bad(), I("never")]))),
            run(lambda: ascii([I("é")])), run(lambda: "%a" % (T((I("ü"),)),))]
def gen():
    yield cases()
expected = [(['[a, 1]', '[a, 1]', '[a, 1]', '[a, 1]', '[a, 1]', '[a, 1]', '[a, 1] [a, 1]', '[a, 1] [a, 1]'], ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a']),
            (['(a,)', '(a,)', '(a,)', '(a,)', '(a,)', '(a,)', '(a,) (a,)', '(a,) (a,)'], ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a']),
            (['{1: a}', '{1: a}', '{1: a}', '{1: a}', '{1: a}', '{1: a}', '{1: a} {1: a}', '{1: a} {1: a}'], ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a']),
            (['S({a})', 'S({a})', 'S({a})', 'S({a})', 'S({a})', 'S({a})', 'S({a}) S({a})', 'S({a}) S({a})'], ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a']),
            (['F({a})', 'F({a})', 'F({a})', 'F({a})', 'F({a})', 'F({a})', 'F({a}) F({a})', 'F({a}) F({a})'], ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a']),
            (['FD({2: a})', 'FD({2: a})', 'FD({2: a})', 'FD({2: a})', 'FD({2: a})', 'FD({2: a})', 'FD({2: a}) FD({2: a})', 'FD({2: a}) FD({2: a})'], ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a']),
            (['[[st], (S({st}),)]', '[[st], (S({st}),)]', '[[st], (S({st}),)]', '[[st], (S({st}),)]', '[[st], (S({st}),)]', '[[st], (S({st}),)]', '[[st], (S({st}),)] [[st], (S({st}),)]', '[[st], (S({st}),)] [[st], (S({st}),)]'], ['static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static', 'static']),
            (['[a, [...]]', '{1: a, 2: {...}}'], ['a', 'a']),
            (['[a]', 'own', 'own'], ['a']),
            (('KeyError', "'bad'"), ['a', 'bad']),
            ('[\\xe9]', ['é']),
            ('(\\xfc,)', ['ü'])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
