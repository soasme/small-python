# spec: PLS-315 19.3.28
# description: open() with its file, and mode, given positionally, the
# first a program calls included, opens a file in a directory the host
# mounted: what is written is read back, a missing file raises
# FileNotFoundError, and a bad mode ValueError. Inside functions and
# generators as at module level.
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
