# spec: PLS-315 23.4, 7.5.5, 7.5.6
# description: str.format of a list, tuple, dict or set field with a
# nested spec takes the container's repr, calling its items' Python
# __repr__, which may loop, in order: by !s, !r or !a before the nested
# spec, which then formats the text, or with no conversion when the nested
# spec is empty; a non-empty spec of a container raises TypeError. An
# item's error propagates. A container whose repr is being built shows as
# [...], converted with a spec or without one too. Inside functions as at
# module level.
from harness import *

log = []

class R:
    def __init__(self, t): self.t = t
    def __hash__(self): return 1
    def __repr__(self):
        for _ in (): pass
        log.append(self.t)
        return self.t + "é"

class Bad:
    def __repr__(self):
        for _ in (): pass
        raise LookupError("bad")

def fields():
    out = ['{!r:>{}}|{:{}}|{k!r:^{w}}'.format([R("a")], 7, (R("b"),), '', k={R("c")}, w=7)]
    out.append('{!a:{}{}}|{!s:{w}}'.format([R("d")], '<', 9, (R("e"),), w=5))
    out.append('{0:{1}}{0!r:{2}}'.format({1: R("f")}, '', 9))
    return out

expected = ['   [aé]|(bé,)| {cé}  ', '[d\\xe9]  |(eé,)', '{1: fé}{1: fé}  ']
assert_eq(fields(), expected)
assert_eq(log, ["a", "b", "c", "d", "e", "f", "f"])
log.clear()

assert_eq('{!r:>{}}|{:{}}|{k!r:^{w}}'.format([R("a")], 7, (R("b"),), '', k={R("c")}, w=7), expected[0])
assert_eq(log, ["a", "b", "c"])
log.clear()

def errors():
    out = []
    try: '{:{}}'.format([1], 'x')
    except TypeError as e: out.append(str(e))
    try: '{!r:{}}'.format([Bad()], 3)
    except LookupError as e: out.append(e.args)
    try: '{:{}}'.format((Bad(),), '')
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), ["unsupported format string passed to list.__format__", ("bad",), ("bad",)])

class In:
    def __repr__(self):
        for _ in (): pass
        return '{!r:>{}}|{:{}}|{!s:{}}'.format(outer, 7, outer, '', outer, '^9')

outer = [In()]

def recursive():
    return repr(outer), '{!r:{}}'.format(outer, '')

assert_eq(recursive(), ('[  [...]|[...]|  [...]  ]', '[  [...]|[...]|  [...]  ]'))

class Plain:
    def __repr__(self):
        return "<{0!r}|{0!r:>8}|{0!a}|{0!s:{1}}>".format(plain, "*^7")

plain = [Plain()]
assert_eq(repr(plain), "[<[...]|   [...]|[...]|*[...]*>]")
