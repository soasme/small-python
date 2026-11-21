# spec: PLS-315 19.3.4, 27.5.1
# description: An anext() awaitable's __next__, send and throw called
# through its type, given it first, act as its bound methods: the async
# generator's body runs once to its yield, whose value ends the step as
# StopIteration, and a throw before it starts raises without running it;
# so do an asend's and an athrow's through theirs.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
async def agen():
    for _ in (): pass
    log.append('run')
    yield 5
def step(f, *a):
    try: return ('value', f(*a))
    except StopIteration as e: return ('stop', e.value)
    except BaseException as e: return (type(e).__name__, e.args)
aw = anext(agen(), 1); emit(step(aw.__next__))
aw = anext(agen(), 1); emit(step(type(aw).__next__, aw))
aw = anext(agen(), 1); emit(step(type(aw).send, aw, None))
aw = anext(agen(), 1); emit(step(type(aw).throw, aw, KeyError('k')))
g = agen(); a1 = g.asend(None); emit(step(type(a1).__next__, a1))
g = agen(); a1 = g.athrow(ValueError); emit(step(type(a1).__next__, a1))
g = agen(); a1 = g.asend(None); emit(step(type(a1).send, a1, None))
emit(log)
EXPECTED = [
    "('stop', 5)",
    "('stop', 5)",
    "('stop', 5)",
    "('KeyError', ('k',))",
    "('stop', 5)",
    "('ValueError', ())",
    "('stop', 5)",
    "['run', 'run', 'run', 'run', 'run']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
