# spec: PLS-315 19.3.10, 7.5.1, 7.5.3
# description: compile() converts its arguments once each in parameter
# order, the filename's __fspath__, the mode's type, flags' __index__,
# dont_inherit's __bool__ or __len__, then optimize's __index__, before
# checking the source's type and the mode's and numbers' values; an
# error stops the conversions after it; keywords and calls inside
# functions convert alike.
from harness import assert_eq

log = []

class Path:
    def __init__(self, value="p.py"): self.value = value
    def __fspath__(self):
        for _ in (): pass
        log.append("fspath")
        return self.value

class Index:
    def __init__(self, value, name): self.value = value; self.name = name
    def __index__(self):
        for _ in (): pass
        log.append(self.name)
        return self.value

class Bool:
    def __bool__(self):
        for _ in (): pass
        log.append("bool")
        return True

class Length:
    def __len__(self):
        for _ in (): pass
        log.append("len")
        return 0

def run(f):
    del log[:]
    try: result = f()
    except Exception as e: result = (type(e).__name__, str(e))
    if type(result).__name__ == "code": result = ("code", result.co_filename)
    return result, log[:]

ALL = ["fspath", "flags", "bool", "opt"]
cases = [
    (lambda: compile("1", Path(), "exec", Index(0, "flags"), Bool(), Index(1, "opt")), (("code", "p.py"), ALL)),
    (lambda: compile("1", Path(), "bad", Index(0, "flags"), Bool(), Index(1, "opt")),
     (("ValueError", "compile() mode must be 'exec', 'eval' or 'single'"), ALL)),
    (lambda: compile(1, Path(), "exec", Index(0, "flags"), Bool(), Index(1, "opt")),
     (("TypeError", "compile() arg 1 must be a string, bytes or AST object"), ALL)),
    (lambda: compile("1", Path(), "exec", Index(0, "flags"), Bool(), Index(9, "opt")),
     (("ValueError", "compile(): invalid optimize value"), ALL)),
    (lambda: compile("1", Path(), "exec", Index(1 << 40, "flags"), Bool()),
     (("OverflowError", "Python int too large to convert to C int"), ["fspath", "flags"])),
    (lambda: compile("1", Path(), "exec", dont_inherit=Bool(), flags=Index(0, "flags")), (("code", "p.py"), ["fspath", "flags", "bool"])),
    (lambda: compile("1", Path(), "exec", 0, Length()), (("code", "p.py"), ["fspath", "len"])),
    (lambda: compile("1", Path(), 5, Index(0, "flags")), (("TypeError", "compile() argument 'mode' must be str, not int"), ["fspath"])),
    (lambda: compile("1", Path(5), "exec", Index(0, "flags")),
     (("TypeError", "expected Path.__fspath__() to return str or bytes, not int"), ["fspath"])),
    (lambda: compile("1", Path("a\0b"), "exec", Index(0, "flags")), (("ValueError", "embedded null character"), ["fspath"])),
    (lambda: compile("1", Path(b"b.py"), "exec"), (("code", "b.py"), ["fspath"])),
    (lambda: compile("1", "s.py", "exec", Index("x", "flags")),
     (("TypeError", "Index.__index__() must return an int, not str"), ["flags"])),
    (lambda: compile("1", 7, "exec", Index(0, "flags")), (("TypeError", "expected str, bytes or os.PathLike object, not int"), [])),
]
for i, (f, expected) in enumerate(cases):
    assert_eq(run(f), expected, str(i))

def inside():
    return [run(f) for f, _ in cases]
assert_eq(inside(), [e for _, e in cases])
