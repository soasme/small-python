# Replays YieldFromIterator.tla: each case delegates with yield from to an
# iterator with the spec's methods, takes one step, and compares the
# result, the methods called, and whether the delegator finished.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def iterator(kind, called):
    calls = []

    def __next__(self):
        calls.append(1)
        if len(calls) == 1:
            return 1
        called.append("next")
        raise StopIteration(8)
    if kind == "builtin":
        return iter([1])
    if kind == "map":
        def function(x):
            for _ in ():
                pass
            return __next__(None)
        return map(function, [0, 1])
    body = {"__iter__": lambda self: self, "__next__": __next__}
    if kind == "defined":
        def send(self, value):
            called.append("send")
            return 7

        def throw(self, *args):
            called.append("throw")
            return 7

        def close(self):
            called.append("close")
        body.update(send=send, throw=throw, close=close)
    elif kind == "raises":
        def method(name):
            def call(self, *args):
                called.append(name)
                raise ValueError
            return call
        body.update(send=method("send"), throw=method("throw"), close=method("close"))
    elif kind == "broken":
        def __getattr__(self, name):
            1 / 0
        body["__getattr__"] = __getattr__
    return type("It", (), body)()


def outcome(p):
    called = []
    it = iterator(p["kind"], called)

    closed = []

    def g():
        try:
            if p["first"]:
                yield "a"
            return (yield from it)
        finally:
            closed.append(1)
    gen = g()

    def nested():
        return (yield from gen)
    top = nested() if p["step"] == "nested" else gen
    next(top)
    if p["first"]:
        next(top)
    try:
        if p["step"] == "close":
            result = repr(gen.close())
        elif p["step"] in ("throw", "nested"):
            result = repr(top.throw(KeyError()))
        elif p["step"] == "send":
            result = repr(gen.send(1))
        elif p["step"] == "loop":
            def outer():
                yield ("ret", (yield from gen))
            result = repr(list(outer()))
        elif p["step"] == "consume":
            result = repr(list(gen))
        elif p["step"] == "drop":
            del gen, top
            return {"result": "dropped", "called": "".join(called), "finished": bool(closed)}
        else:
            result = repr(next(gen))
    except StopIteration as error:
        result = "StopIteration %r" % error.value
    except (ValueError, KeyError, ZeroDivisionError, AttributeError) as error:
        result = type(error).__name__
    return {"result": result, "called": "".join(called), "finished": gen.gi_frame is None}


check_programs(outcome)
