# spec: PLS-315 7.7.7
# description: list() and bytes() of an instance ask its LengthHint
# through __len__ and __length_hint__ descriptors whose Python __get__
# runs first and may loop: a TypeError reading or calling __len__ gives
# way to __length_hint__, any other error propagates, as does every error
# reading __length_hint__; a sequence iterator's hint reads its instance's
# __len__ descriptor, a spent reversed one not at all.
from harness import *

log = []
class D:
    def __init__(s, f, mode=None): s.f = f; s.mode = mode
    def __get__(s, obj, owner):
        for _ in (): pass
        log.append(("get", s.f.__name__))
        if s.mode == "attr": raise AttributeError("gone")
        if s.mode == "type": raise TypeError("typed")
        if s.mode == "key": raise KeyError("k")
        return s.f.__get__(obj, owner)
def mk(mode, hint_mode=None, hint=True):
    def __len__(self): log.append("len"); return 2
    def __length_hint__(self): log.append("hint"); return 7
    def __iter__(self): return iter((1, 2))
    body = {"__len__": D(__len__, mode), "__iter__": __iter__}
    if hint: body["__length_hint__"] = D(__length_hint__, hint_mode)
    return type("X", (), body)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def results():
    out = []
    for args in [(None,), ("attr",), ("type",), ("key",), ("type", "attr"), ("type", "type"), ("type", None, False)]:
        X = mk(*args)
        out.append((args, run(lambda: list(X())), run(lambda: bytes(X()))))
    class G:
        __len__ = D(lambda self: 3)
        def __getitem__(s, i):
            if i >= 2: raise IndexError
            return i
    out.append((run(lambda: list(iter(G()))), run(lambda: list(reversed(G())))))
    return out

expected = [
    ((None,), ([1, 2], [('get', '__len__'), 'len']), (b'\x01\x02', [('get', '__len__'), 'len'])),
    (('attr',), (('AttributeError', 'gone'), [('get', '__len__')]), (('AttributeError', 'gone'), [('get', '__len__')])),
    (('type',), ([1, 2], [('get', '__len__'), ('get', '__length_hint__'), 'hint']), (b'\x01\x02', [('get', '__len__'), ('get', '__length_hint__'), 'hint'])),
    (('key',), (('KeyError', "'k'"), [('get', '__len__')]), (('KeyError', "'k'"), [('get', '__len__')])),
    (('type', 'attr'), (('AttributeError', 'gone'), [('get', '__len__'), ('get', '__length_hint__')]), (('AttributeError', 'gone'), [('get', '__len__'), ('get', '__length_hint__')])),
    (('type', 'type'), (('TypeError', 'typed'), [('get', '__len__'), ('get', '__length_hint__')]), (('TypeError', 'typed'), [('get', '__len__'), ('get', '__length_hint__')])),
    (('type', None, False), ([1, 2], [('get', '__len__')]), (b'\x01\x02', [('get', '__len__')])),
    (([0, 1], [('get', '<lambda>')]), ([], [('get', '<lambda>'), ('get', '<lambda>')])),
]
assert_eq(results(), expected)

def main():
    for _ in (): pass
    return results()

assert_eq(main(), expected)
