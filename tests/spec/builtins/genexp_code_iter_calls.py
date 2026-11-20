# spec: PLS-315 28.1
# description: a function made from a generator expression's code takes
# its iterable, whose iterator it gets at the call: a Python __iter__ or
# __aiter__ runs once, its result checked as an iterator or an async
# iterator, and its exception propagates; the generator is named after
# the function; inside comprehensions and generators too.
from harness import assert_eq
FunctionType = type(lambda: 0)
log = []
class It:
    def __init__(self, n): self.n = n
    def __iter__(self):
        for _ in (): pass
        log.append('iter')
        return iter(range(self.n))
class Bad:
    def __iter__(self): return 5
class Raise:
    def __iter__(self): raise KeyError('r')
class AIt:
    def __aiter__(self):
        for _ in (): pass
        log.append('aiter')
        return self
    async def __anext__(self):
        if getattr(self, 'done', 0): raise StopAsyncIteration
        self.done = 1
        return 7
class Plain:
    def __iter__(self): return iter([4, 5])
class APlain:
    def __init__(self): self.n = 0
    def __aiter__(self): return self
    async def __anext__(self):
        self.n += 1
        if self.n > 2: raise StopAsyncIteration
        return self.n
class ABad:
    def __aiter__(self): return 5
code = (x * 10 for x in [1]).gi_code
async def make(): return (x + 1 async for x in AIt())
def run_co(co):
    try: co.send(None)
    except StopIteration as s: return s.value
acode = run_co(make()).ag_code
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
async def collect(ag): return [x async for x in ag]
cases = [lambda: list(FunctionType(code, {})(It(3))), lambda: FunctionType(code, {})(It(3)).__qualname__, lambda: FunctionType(code, {})(Bad()),
         lambda: FunctionType(code, {})(Raise()), lambda: run_co(collect(FunctionType(acode, {})(AIt()))), lambda: FunctionType(acode, {})(ABad()),
         lambda: list(FunctionType(code, {})(Plain())), lambda: run_co(collect(FunctionType(acode, {})(APlain()))),
         lambda: FunctionType(code, {})(5), lambda: list(FunctionType(code, {})([2, 3])), lambda: [list(FunctionType(code, {})(It(2))) for _ in (0,)]]
EXPECTED = [
    ([0, 10, 20], ['iter']),
    ('<genexpr>', ['iter']),
    (('TypeError', 'Bad.__iter__() must return an iterator, not int'), []),
    (('KeyError', "'r'"), []),
    ([8], ['aiter']),
    (('TypeError', "'async for' received an object from __aiter__ that does not implement __anext__: int"), []),
    ([40, 50], []),
    ([2, 3], []),
    (('TypeError', "'int' object is not iterable"), []),
    ([20, 30], []),
    ([[0, 10]], ['iter']),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
