# spec: PLS-315 7.4.3, 13.16.1, 27.2.1
# description: A call of a generator function, a coroutine function or an
# asynchronous generator function binds a keyword whose name is an
# instance of a str subclass as any function's call does: the first
# positional-or-keyword or keyword-only parameter, in order, that its
# Python __eq__ finds equal, else **kwargs, else an unexpected keyword;
# an exception of __eq__ propagates from the call, one of __hash__ from
# the dictionary display before it. The call
# then makes its generator, running none of its body until it is resumed.
from harness import *

log = []

class Name(str):
    def __eq__(self, other):
        for _ in (): pass
        log.append((str(self), other))
        if str(self) == "bad": raise LookupError(other)
        return str.__eq__(self, other) or str(self) == other.upper()
    def __hash__(self):
        for _ in (): pass
        if str(self) == "unhashable": raise KeyError("hash")
        return str.__hash__(self)

def gen(a, b=2, **rest):
    log.append("body")
    yield (a, b, sorted(rest))

def plain(a, b=2):
    log.append("body")
    yield (a, b)

async def coro(a, b=2):
    log.append("body")
    return (a, b)

async def agen(a, *, k=0):
    log.append("body")
    yield (a, k)

def run_coro(c):
    try: c.send(None)
    except StopIteration as e: return e.value

def run_agen(g):
    try: g.__anext__().send(None)
    except StopIteration as e: return e.value

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    g = gen(1, **{Name("B"): 3})
    log.append("made")
    out = [next(g), next(gen(**{Name("a"): 4, Name("z"): 5})), next(plain(1, **{Name("b"): 6})),
           attempt(lambda: plain(1, **{Name("q"): 7})), attempt(lambda: plain(1, **{Name("a"): 8})),
           attempt(lambda: plain(1, **{Name("bad"): 9})), attempt(lambda: gen(1, **{Name("unhashable"): 9})),
           run_coro(coro(1, **{Name("b"): 10})), run_agen(agen(1, **{Name("K"): 11}))]
    return out, list(log)

expected = ([(1, 3, []), (4, 2, ["z"]), (1, 6),
             ("TypeError", "plain() got an unexpected keyword argument 'q'"),
             ("TypeError", "plain() got multiple values for argument 'a'"),
             ("LookupError", "a"), ("KeyError", "'hash'"), (1, 10), (1, 11)],
            [("B", "a"), ("B", "b"), "made", "body", ("a", "a"), ("z", "a"), ("z", "b"), "body",
             ("b", "a"), ("b", "b"), "body", ("q", "a"), ("q", "b"), ("a", "a"), ("bad", "a"),
             ("b", "a"), ("b", "b"), "body", ("K", "a"), ("K", "k"), "body"])

assert_eq(results(), expected)
assert_eq(results(), expected)
