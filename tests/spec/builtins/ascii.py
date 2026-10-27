# spec: PLS-315 19.3.5
# description: ascii() escapes non-ASCII characters of repr() and keeps the type __repr__ returns.
from harness import *
assert ascii("hello world") == "'hello world'"
assert ascii("안녕 세상") == "'\\uc548\\ub155 \\uc138\\uc0c1'"
assert ascii("안녕 Python") == "'\\uc548\\ub155 Python'"
assert ascii(5) == "5"
assert ascii(chr(0x10001)) == "'\\U00010001'"
assert ascii(chr(0x9999)) == "'\\u9999'"
assert ascii(chr(0x0A)) == "'\\n'"


class MyStr(str):
    pass


class Foo:
    def __repr__(self):
        return MyStr("hello")


class Bar:
    def __repr__(self):
        return MyStr("héllo")


assert type(ascii(Foo())) is MyStr
assert ascii(Foo()) == MyStr("hello")
assert type(ascii(Bar())) is str
assert ascii(Bar()) == "h\\xe9llo"
