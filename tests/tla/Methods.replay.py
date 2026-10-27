# Replays Methods.tla: each case gets the spec's method or function and
# compares what is read or returned, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCE = '''
def plain(*args):
    "plain doc"
    return args
plain.tag = "T"
class C:
    def f(self, *args):
        "f doc"
        return args
    f.tag = "T"
    @classmethod
    def cm(cls, *args):
        return args
    @staticmethod
    def sm(*args):
        return args
c = C()
c.attr = plain
the_list = []
'''
ACCESS = {"c.f": "c.f", "C.f": "C.f", "c.cm": "c.cm", "C.cm": "C.cm", "c.sm": "c.sm", "c.attr": "c.attr",
          "[].append": "the_list.append", "len": "len", "[].__len__": "the_list.__len__"}


def outcome(p):
    import builtins
    namespace = {"__name__": "m"}
    exec(SOURCE, namespace)
    m = eval(ACCESS[p["access"]], namespace)
    names = {id(namespace["c"]): "c", id(namespace["C"]): "C", id(namespace["the_list"]): "the list", id(builtins): "builtins"}
    op = p["op"]
    try:
        if op == "type":
            return type(m).__name__
        if op == "set":
            m.new = 1
            return "ok"
        if op == "call":
            access = p["access"]
            return repr(m([1]) if access == "len" else m() if access == "[].__len__" else m(1))
        value = getattr(m, "tag" if op == "tag" else op)
    except AttributeError:
        return "AttributeError"
    if op == "__self__":
        return names.get(id(value), repr(value))
    if op == "__func__":
        return value.__qualname__
    if op == "__doc__" and p["access"] in ("[].append", "len", "[].__len__"):
        return "a str or None" if value is None or type(value) is str else repr(value)
    return repr(value)


check_programs(outcome)
