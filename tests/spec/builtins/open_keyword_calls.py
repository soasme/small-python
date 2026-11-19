# spec: PLS-315 19.3.28
# description: open() given its file, mode or encoding by keyword, the
# first a program calls included, opens a file in a directory the host
# mounted as a positional call does: what is written is read back, a
# missing file raises FileNotFoundError, a bad mode ValueError, an
# unknown keyword TypeError. Inside functions and generators as at
# module level.
from harness import *

f = open(file="spec_open_keyword_calls.txt", mode="w")
f.write("one")
f.close()

def read(path, **options):
    f = open(path, **options)
    text = f.read()
    f.close()
    return text

assert_eq(read("spec_open_keyword_calls.txt", mode="r"), "one")
assert_eq(read("spec_open_keyword_calls.txt", encoding="utf-8"), "one")

def gen():
    f = open("spec_open_keyword_calls.txt", mode="a")
    f.write("two")
    f.close()
    f = open(file="spec_open_keyword_calls.txt")
    yield f.read()
    f.close()

assert_eq(next(gen()), "onetwo")
assert_raises(FileNotFoundError, read, "spec-open-keyword-missing.txt", mode="r")
assert_raises(ValueError, open, "spec_open_keyword_calls.txt", mode="q")
e = assert_raises(TypeError, open, "spec_open_keyword_calls.txt", colour="red")
assert_eq(str(e), "open() got an unexpected keyword argument 'colour'")
