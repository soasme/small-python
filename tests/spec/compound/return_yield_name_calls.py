# spec: PLS-315 9.3.2, 22.1.1
# description: A function's or lambda's return or yield of a global name,
# in code that exec() runs with a dict subclass as globals, reads it
# through the globals' Python __getitem__, or __missing__ when absent,
# once per read, its KeyError a NameError.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class G(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(key)
        return dict.__getitem__(self, key)
class M(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(('missing', key))
        if key == 'gone': raise KeyError(key)
        return key.upper()
src = '''
def f(): return value
def g(): yield value
def h(): return absent
def k():
    yield other
f2 = lambda: value
'''
ns = G(value=5, __builtins__=__builtins__)
exec(src, ns)
emit(ns['f'](), list(ns['g']()), ns['f2'](), log); log.clear()
try: ns['h']()
except NameError as e: emit('NameError', e, log); log.clear()
ms = M(__builtins__=__builtins__)
exec(src, ms)
emit(dict.__getitem__(ms, 'f')(), list(dict.__getitem__(ms, 'k')()), log)
EXPECTED = [
    "5 [5] 5 ['f', 'value', 'g', 'value', 'f2', 'value']",
    "NameError name 'absent' is not defined ['h', 'absent']",
    "VALUE ['OTHER'] [('missing', 'value'), ('missing', 'other')]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
