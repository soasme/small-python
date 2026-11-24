# spec: PLS-315 19.3.28
# description: open() with its file, and mode, given positionally, the
# first a program calls included, opens a file in a directory the host
# mounted: what is written is read back, a missing file raises
# FileNotFoundError, and a bad mode ValueError. Inside functions and
# generators as at module level. Its arguments are checked as a built-in's
# with keyword parameters (19.3), before any file is looked at.
from harness import *

def write(path, text):
    f = open(path, "w")
    f.write(text)
    f.close()

def read(path):
    f = open(path)
    text = f.read()
    f.close()
    return text

write("spec_open_calls.txt", "one")
assert_eq(read("spec_open_calls.txt"), "one")

def gen():
    write("spec_open_calls.txt", "two")
    yield read("spec_open_calls.txt")

assert_eq(next(gen()), "two")
e = assert_raises(FileNotFoundError, read, "spec-open-calls-missing.txt")
assert_raises(ValueError, open, "spec_open_calls.txt", "q")
f = open("spec_open_calls.txt", "r")
assert_eq(f.read(), "two")
f.close()

def message(f):
    try: f()
    except TypeError as e: return str(e)
assert_eq([message(lambda: open(*["f"] * 9, mode="r")), message(lambda: open(*["f"] * 9)),
           message(lambda: open("f", "r", -1, None, None, None, True, None, opener=None)),
           message(lambda: open("f", "r", -1, None, None, None, True, encoding="x")),
           message(lambda: open(file="f", bogus=1, mode="r")), message(lambda: open(mode="r")), message(lambda: open())],
          ["open() takes at most 8 arguments (10 given)", "open() takes at most 8 arguments (9 given)",
           "open() takes at most 8 arguments (9 given)", "argument for open() given by name ('encoding') and position (4)",
           "open() got an unexpected keyword argument 'bogus'", "open() missing required argument 'file' (pos 1)",
           "open() missing required argument 'file' (pos 1)"])
# In a function, with no arguments or more than eight.
def arity():
    out, a = [], 1
    for call in (lambda: open(), lambda: open(a, a, a, a, a, a, a, a, a)):
        try: call()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(arity(), ["open() missing required argument 'file' (pos 1)", "open() takes at most 8 arguments (9 given)"])

# The classes of an opened file bind their arguments as built-ins with
# keyword parameters too.
f = open("spec_open_calls.txt")
TextIO, Reader, Raw = type(f), type(f.buffer), type(f.buffer.raw)
f.close()
assert_eq([message(lambda: Raw()), message(lambda: Raw("f", "r", True, None, 5)), message(lambda: Raw("f", x=1)),
           message(lambda: Reader(1, 2, 3)), message(lambda: Reader(raw=1, x=1)), message(lambda: TextIO()),
           message(lambda: TextIO(buffer=1, encoding=2, foo=3))],
          ["FileIO() missing required argument 'file' (pos 1)", "FileIO() takes at most 4 arguments (5 given)",
           "FileIO() got an unexpected keyword argument 'x'", "BufferedReader() takes at most 2 arguments (3 given)",
           "BufferedReader() got an unexpected keyword argument 'x'", "TextIOWrapper() missing required argument 'buffer' (pos 1)",
           "TextIOWrapper() got an unexpected keyword argument 'foo'"])
