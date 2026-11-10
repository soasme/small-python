# Replays DelegateThrowArguments.tla: each case throws into a generator
# suspended in a yield from of the spec's delegate, and compares the
# throw()'s result and whether the generator is still suspended.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Throws:
    def __iter__(self): return self
    def __next__(self): return 1
    def throw(self, *args): return "thrown"
    def close(self): pass


class Bare:
    def __iter__(self): return self
    def __next__(self): return 1


def outcome(p):
    def gen():
        yield 1
    it = gen() if p["delegate"] == "generator" else Throws() if p["delegate"] == "throws" else Bare()

    def handling():
        try:
            yield from it
        except Exception as e:
            yield "caught " + type(e).__name__

    def plain():
        yield from it
    g = handling() if p["handles"] else plain()
    next(g)
    args = {"instance": (KeyError("k"),), "invalid": (1,), "exit": (GeneratorExit, 1, 2)}[p["args"]]
    try:
        result = repr(g.throw(*args))
    except Exception as e:
        result = type(e).__name__
    return {"result": result, "suspended": g.gi_frame is not None}


check_programs(outcome)
