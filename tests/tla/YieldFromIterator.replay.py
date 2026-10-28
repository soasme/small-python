# Replays YieldFromIterator.tla: each case delegates with yield from to an
# iterator with the spec's methods, takes one step, and compares the
# result, the methods called, and whether the delegator finished.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def iterator(kind, called):
    body = {"__iter__": lambda self: self, "__next__": lambda self: 1}
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

    def g():
        yield from it
    gen = g()
    next(gen)
    try:
        if p["step"] == "close":
            result = repr(gen.close())
        elif p["step"] == "throw":
            result = repr(gen.throw(KeyError))
        else:
            result = repr(gen.send(1))
    except (ValueError, KeyError, ZeroDivisionError, AttributeError) as error:
        result = type(error).__name__
    return {"result": result, "called": "".join(called), "finished": gen.gi_frame is None}


check_programs(outcome)
