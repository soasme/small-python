# spec: PLS-315 24.2, 24.3, 23.6
# description: bytearray.__mod__ called by name, bound to the format or
# passed as a callable, formats as bytearray % does: each %a, %r, %s or %c
# calls the argument's Python __repr__, __bytes__ or __index__, which may
# loop or raise, once and in order, and returns a bytearray; the format
# stays exported meanwhile, so a method resizing it raises BufferError.
from harness import assert_eq, assert_raises
log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass
class R:
    def __repr__(self): spin(); log.append('repr'); return 'R'
class B:
    def __bytes__(self): spin(); log.append('bytes'); return b'BY'
    def __index__(self): spin(); log.append('index'); return 65
class Bad:
    def __repr__(self): spin(); raise KeyError('b')
def run(f, *args):
    del log[:]
    r = f(*args)
    return type(r).__name__, bytes(r), log[:]
assert_eq(run(bytearray.__mod__, bytearray(b'%a|%r'), (R(), R())), ('bytearray', b'R|R', ['repr', 'repr']))
assert_eq(run(bytearray(b'%s %c').__mod__, (B(), B())), ('bytearray', b'BY A', ['bytes', 'index']))
assert_eq(run(lambda: bytearray(b'<%a>').__mod__(R())), ('bytearray', b'<R>', ['repr']))
assert_raises(KeyError, bytearray(b'%a').__mod__, Bad())
fmt = bytearray(b'%a end')
class Clears:
    def __repr__(self): spin(); fmt.clear(); return 'E'
assert_raises(BufferError, fmt.__mod__, Clears())
assert_eq(fmt, bytearray(b'%a end'))
fmt.clear()
def g(): yield run(bytearray(b'%a!').__mod__, R())
assert_eq(list(g()), [('bytearray', b'R!', ['repr'])])
