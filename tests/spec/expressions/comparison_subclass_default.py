# spec: PLS-315 7.2.4, 13.10
# description: A comparison whose right operand's class is a strict
# subclass of the left's calls the right operand's reflected method first
# even when it is object's, which declines, and then the left operand's
# own Python method, which may loop; when that declines too, == and !=
# fall back to identity and an ordering raises TypeError, and an error
# from the method propagates, inside functions as at module level.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Base:
    def __init__(self, v): self.v = v
    def __lt__(self, other): spin(); log.append("lt"); return self.v < other.v
    def __ge__(self, other): spin(); log.append("ge"); return NotImplemented
    def __eq__(self, other):
        spin(); log.append("eq")
        if self.v == 9: raise KeyError("eq")
        return self.v == other.v
    def __ne__(self, other): spin(); log.append("ne"); return NotImplemented
class Sub(Base):
    pass

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def ordering():
    try:
        return Base(1) >= Sub(2)
    except TypeError as e:
        return str(e)

def main():
    a, b = Base(1), Sub(2)
    check(lambda: (a < b, b < a), (True, False), ["lt", "lt"])
    check(lambda: (a == Sub(1), a == b), (True, False), ["eq", "eq"])
    check(lambda: a != Sub(1), True, ["ne", "ne"])
    check(ordering, "'>=' not supported between instances of 'Base' and 'Sub'", ["ge"])
    def gen():
        yield a < b
    check(lambda: list(gen()), [True], ["lt"])
main()

assert_raises(KeyError, lambda: Base(1) == Sub(9), message="'eq'")
log.clear()
assert_eq(Base(1) < Sub(2), True)
assert_eq(log, ["lt"])
