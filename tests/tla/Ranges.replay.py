# Replays Ranges.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class I:
    def __init__(self, v): self.v = v
    def __index__(self): return self.v

SOURCES = {
    "one_arg": "result = (range(3), range(3).start, range(3).stop, range(3).step)",
    "index_args": "result = list(range(I(1), I(7), I(3)))",
    "float_arg": "result = range(1.0)",
    "str_arg": "result = range(0, '3')",
    "no_args": "result = range()",
    "four_args": "result = range(1, 2, 3, 4)",
    "keyword": "result = range(stop=3)",
    "step_zero": "result = range(0, 3, 0)",
    "huge_len": "from harness import host\nresult = len(range(host.maxsize() * 4))",
    "huge_ok": "from harness import host\nm = host.maxsize()\nr = range(-m, m * 4, m)\nresult = (r[-1], m * 3 - 1 in r, r.index(m * 2))",
    "attrs_kept": "result = (range(2, 1, 3).start, range(2, 1, 3).stop, range(2, 1, 3).step, range(0) == range(2, 1, 3))",
    "equal_sequences": "result = (range(0, 3, 2) == range(0, 4, 2), range(0, 3, 2) != range(0, 4, 2), range(1) == range(1, 2, 5))",
    "equal_list": "result = range(3) == [0, 1, 2]",
    "hash_equal": "result = hash(range(0, 3, 2)) == hash(range(0, 4, 2)) and hash(range(0)) == hash(range(5, 1))",
    "ordering": "result = range(1) < range(2)",
    "concat": "result = range(2) + range(2)",
    "repeat": "result = range(2) * 2",
    "contains_float": "result = (2.0 in range(3), 2.5 in range(3))",
    "contains_bool": "result = True in range(2)",
    "contains_other": "result = 'a' in range(3)",
    "index_missing": "result = range(0, 20, 2).index(11)",
    "count": "result = (range(5).count(3), range(5).count(3.0), range(5).count('x'))",
    "doc_example": "r = range(0, 20, 2)\nresult = (r, 11 in r, 10 in r, r.index(10), r[5], r[:5], r[-1])",
    "slice_step": "result = (range(10)[::3], range(10)[8:1:-2], range(10)[100:])",
    "index_bad_type": "result = range(3)['a']",
    "index_too_big": "result = range(3)[2 ** 100]",
    "immutable": "r = range(3)\nr[0] = 1",
    "attr_readonly": "r = range(3)\nr.start = 1",
    "bool": "result = (bool(range(0)), bool(range(1)))",
    "reversed_type": "result = (type(reversed(range(3))).__name__, list(reversed(range(1, 10, 4))))",
    "subclass": "class R(range): pass",
    "iter_type": "result = type(iter(range(3))).__name__",
    "repr_step": "result = (repr(range(1, 2, 1)), repr(range(1, 2, 3)))",
    "negative_index_out": "result = range(3)[-4]",
    "len_bool_index": "result = (range(True), len(range(-5)))"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    try:
        r = range(p["start"], p["stop"], p["step"])
    except ValueError as error:
        return "ValueError: %s" % error

    def at(i):
        try:
            return r[i]
        except IndexError:
            return "IndexError"
    return repr((list(r), len(r), at(0), at(-1), r[::-1], r[1:], 2 in r, r.index(2) if 2 in r else "missing"))


def outcome(p):
    if "case" not in p:
        return generated(p)
    namespace = dict(TYPES)
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


check_programs(outcome)
