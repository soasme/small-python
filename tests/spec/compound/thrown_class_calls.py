# spec: PLS-315 13.16.3, 27.2.2, 27.5.2
# description: An exception class thrown into a generator at a yield from
# whose delegate has no such throw or close, or a Python one, or one its
# __getattr__ gives, and one an async generator's athrow throws at its
# yield, with a value, a tuple of arguments or a traceback, is called
# once there: its Python __new__ and __init__ run before the exception
# raises, a __new__ giving another class's instance has the class called
# again with it, and an error of the call raises in its place.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def spin():
    for _ in (): pass
class Exit(GeneratorExit):
    def __init__(self, *a):
        spin(); log.append(('Exit.init', a)); super().__init__(*a)
class Bad(Exception):
    def __init__(self, *a):
        spin(); log.append(('Bad.init', a)); super().__init__(*a)
class Fails(Exception):
    def __init__(self):
        spin(); raise KeyError('init')
class Odd(Exception):
    def __new__(cls):
        spin(); return 7
class It:
    def __iter__(self): return self
    def __next__(self): return 1
    def close(self): spin(); log.append('close')
class NoThrow:
    def __iter__(self): return self
    def __next__(self): return 1
def outer(it):
    try:
        yield from it
    except BaseException as e:
        log.append(('caught', type(e).__name__, e.args, type(e.__context__).__name__))
        yield 'handled'
def go(it, exc):
    g = outer(it); next(g)
    try:
        try:
            raise OSError('outside')
        except OSError:
            r = g.throw(exc)
    except BaseException as e:
        r = ('out', type(e).__name__, e.args, type(e.__context__).__name__)
    log.append(r)
for it, exc in [(It(), Exit), (NoThrow(), Bad), (NoThrow(), Exit), (NoThrow(), Fails), (NoThrow(), Odd), (It(), Fails)]:
    go(it, exc)
class Sub(Bad): pass
class Swap(Exception):
    def __new__(cls, *a):
        spin(); log.append(('Swap.new', a))
        return Sub(*a) if a and a[0] != 'again' else super().__new__(cls, *a)
class Failing(Exception):
    def __init__(self, *a):
        spin(); raise KeyError('init')
class Asked:
    def __iter__(self): return self
    def __next__(self): return 1
    def __getattr__(self, name):
        spin(); log.append(('ask', name))
        if name == 'close': return [].clear
        raise AttributeError(name)
for exc in (Exit, Bad, Fails):
    go(Asked(), exc)
async def agen():
    while True:
        try:
            yield 1
        except BaseException as e:
            log.append(('agen', type(e).__name__, e.args, type(e.__context__).__name__, e.__traceback__ is not None))
            yield 2
def tb():
    try: raise ValueError
    except ValueError as e: return e.__traceback__
def drive(aw):
    try:
        aw.send(None)
    except StopIteration as e:
        return ('stop', e.value)
    except BaseException as e:
        return ('raised', type(e).__name__, e.args)
for args in [(Bad,), (Bad, 'v'), (Bad, ('x', 'y')), (Bad, None, tb()), (Swap, 's'), (Swap, 'again'), (Failing,), (Failing, 'q')]:
    g = agen(); drive(g.asend(None))
    log.append(drive(g.athrow(*args)))
for x in log: emit(x)
EXPECTED = [
    'close',
    "('Exit.init', ())",
    "('caught', 'Exit', (), 'NoneType')",
    'handled',
    "('Bad.init', ())",
    "('caught', 'Bad', (), 'NoneType')",
    'handled',
    "('Exit.init', ())",
    "('caught', 'Exit', (), 'NoneType')",
    'handled',
    "('caught', 'KeyError', ('init',), 'OSError')",
    'handled',
    '(\'caught\', \'TypeError\', ("calling <class \'__main__.Odd\'> should have returned an instance of BaseException, not int",), \'OSError\')',
    'handled',
    "('caught', 'KeyError', ('init',), 'OSError')",
    'handled',
    "('ask', 'close')",
    "('Exit.init', ())",
    "('caught', 'Exit', (), 'NoneType')",
    'handled',
    "('ask', 'throw')",
    "('Bad.init', ())",
    "('caught', 'Bad', (), 'NoneType')",
    'handled',
    "('ask', 'throw')",
    "('caught', 'KeyError', ('init',), 'OSError')",
    'handled',
    "('Bad.init', ())",
    "('agen', 'Bad', (), 'NoneType', True)",
    "('stop', 2)",
    "('Bad.init', ('v',))",
    "('agen', 'Bad', ('v',), 'NoneType', True)",
    "('stop', 2)",
    "('Bad.init', ('x', 'y'))",
    "('agen', 'Bad', ('x', 'y'), 'NoneType', True)",
    "('stop', 2)",
    "('Bad.init', ())",
    "('agen', 'Bad', (), 'NoneType', True)",
    "('stop', 2)",
    "('Swap.new', ('s',))",
    "('Bad.init', ('s',))",
    "('Swap.new', (Sub('s'),))",
    "('Bad.init', (Sub('s'),))",
    "('agen', 'Sub', (Sub('s'),), 'NoneType', True)",
    "('stop', 2)",
    "('Swap.new', ('again',))",
    "('agen', 'Swap', ('again',), 'NoneType', True)",
    "('stop', 2)",
    "('agen', 'KeyError', ('init',), 'NoneType', True)",
    "('stop', 2)",
    "('agen', 'KeyError', ('init',), 'NoneType', True)",
    "('stop', 2)",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
