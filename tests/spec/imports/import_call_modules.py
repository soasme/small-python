# spec: PLS-315 17.4.2, 17.4.3, 17.4.4
# description: __import__ called by name, positionally, by keyword, from a
# comprehension, a generator or map(), and an import statement's
# __import__ for its second module or a from-import's submodule, run each
# module body, which may loop, once, packages first, then the fromlist's
# submodules and those of __all__ for "*"; an absent submodule of the
# fromlist is skipped, a failed body's error passes out and its module is
# imported again, and the result is the top-level package or the module.
# A module of no statements, a package's too, is imported running nothing.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
from log_mod import log
def name(r):
    return [name(x) for x in r] if isinstance(r, list) else getattr(r, '__name__', r)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return name(r), log[:]
emit(run(lambda: __import__('im_plain')))
emit(run(lambda: __import__('im_plain')))
emit(run(lambda: __import__('ipk.inner.deep')))
emit(run(lambda: __import__('ipk.inner.deep', None, None, ['value']).value))
emit(run(lambda: __import__('ipk', fromlist=['s2', 'nope'])))
emit(run(lambda: __import__('ipk', None, None, ['*'])))
emit(run(lambda: __import__('ipk', None, None, ['s3']).s3.rel))
emit(run(lambda: __import__('im_bad')))
emit(run(lambda: __import__('im_bad')))
emit(run(lambda: __import__('ipk', None, None, [1])))
emit(run(lambda: __import__('')))
emit(run(lambda: __import__('nosuch_mod')))
emit(run(lambda: __import__('ipk.nosuch')))
emit(run(lambda: [__import__(n) for n in ('im_plain', 'ipk')]))
def g(): yield __import__('ipk.s1', None, None, ('s1',))
emit(run(lambda: list(g())))
def stmts():
    from ipk import s4
    import im_two, ipk.s5
    from ipk import inner as I, s6
    return s4.__name__, im_two.__name__, I.__name__, s6.__name__
emit(run(stmts))
emit(run(lambda: list(map(__import__, ['ipk.s7', 'im_plain']))))
EXPECTED = [
    "('im_plain', ['plain'])",
    "('im_plain', [])",
    "('ipk', ['ipk', 'inner', 'deep'])",
    '(7, [])',
    "('ipk', ['s2'])",
    "('ipk', ['s1'])",
    "('ipk.s1', ['s3'])",
    '((\'KeyError\', "\'bad body\'"), [\'bad\'])',
    '((\'KeyError\', "\'bad body\'"), [\'bad\'])',
    '((\'TypeError\', "Item in ``from list\'\' must be str, not int"), [])',
    "(('ValueError', 'Empty module name'), [])",
    '((\'ModuleNotFoundError\', "No module named \'nosuch_mod\'"), [])',
    '((\'ModuleNotFoundError\', "No module named \'ipk.nosuch\'"), [])',
    "(['im_plain', 'ipk'], [])",
    "(['ipk.s1'], [])",
    "(('ipk.s4', 'im_two', 'ipk.inner', 'ipk.s6'), ['s4', 'im_two', 's5', 's6'])",
    "(['ipk', 'im_plain'], ['s7'])",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)

# A module of no statements, a package's too, is imported running nothing.
def empty_modules():
    for _ in (): pass
    return [__import__(name).__name__ for name in ("im_empty", "iepkg", "im_comment")], __import__("im_empty").__doc__
assert_eq(empty_modules(), (["im_empty", "iepkg", "im_comment"], None))
