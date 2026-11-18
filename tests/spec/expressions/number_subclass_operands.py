# spec: PLS-315 22, 7.6.2, 7.2.4
# description: A number's own operator method takes an instance of a
# subclass of a number its type accepts (Table 22-1) and answers before
# the instance's reflected method, which it never calls: a float or
# complex with an int subclass, a complex with a float subclass, a bool
# with an int subclass, for binary operators, augmented assignments,
# divmod(), pow(), sum() and comparisons; a complex orders nothing and
# has no %, a float no bitwise operator, so those reach the reflected
# method. The reflected method of a subclass of the number's own type
# still comes first, and an int's methods take no float subclass. A
# complex with a plain instance reaches its reflected method too. Inside
# functions as at module level.
from harness import *

log = []

class I(int):
    def __radd__(self, o):
        for _ in range(2): pass
        log.append(("radd", o))
        return "I"
    def __rsub__(self, o):
        log.append(("rsub", o))
        return NotImplemented
    def __rand__(self, o):
        for _ in range(2): pass
        log.append(("rand", o))
        return NotImplemented
    def __rmod__(self, o):
        log.append(("rmod", o))
        return NotImplemented
    def __rdivmod__(self, o):
        log.append(("rdivmod", o))
        return NotImplemented
    def __rpow__(self, o, m=None):
        for _ in range(2): pass
        log.append(("rpow", o))
        return NotImplemented
    def __gt__(self, o):
        for _ in range(2): pass
        log.append(("gt", o))
        return NotImplemented
    def __eq__(self, o):
        log.append(("eq", o))
        return NotImplemented
    __hash__ = int.__hash__

class F(float):
    def __radd__(self, o):
        for _ in range(2): pass
        log.append(("Fradd", o))
        return "F"
    def __rfloordiv__(self, o):
        log.append(("Frfloordiv", o))
        return NotImplemented

class Plain:
    def __radd__(self, o):
        for _ in range(2): pass
        log.append(("Pradd", o))
        return "P"
    def __gt__(self, o):
        log.append(("Pgt", o))
        return True

def error(f):
    try:
        return f()
    except TypeError as e:
        return str(e)

def operations():
    del log[:]
    i, f = I(2), F(2.0)
    out = [1.5 + i, True + i, 1j + i, 1j + f, 1.5 - i, True & i, divmod(1.5, i), 2.0 ** i, pow(2.0, i), 1j ** i,
           1.5 < i, 1.5 == i, 1j == i, 1j != f, sum([1.5, i]), sum([1j, i, f])]
    n = 1.5
    n += i
    out.append(n)
    out += [error(lambda: 1.5 & i), error(lambda: 1j % i), error(lambda: 1j // f), error(lambda: 1j < i)]
    out += [1 + i, 2 - i, 1 + f, sum([1, f]), 1j + Plain(), sum([1j, Plain()]), 1j < Plain()]
    out.append(list(log))
    return out

expected = [3.5, 3, (2 + 1j), (2 + 1j), -0.5, 0, (0.0, 1.5), 4.0, 4.0, (-1 + 0j),
            True, False, False, True, 3.5, (4 + 1j), 3.5,
            "unsupported operand type(s) for &: 'float' and 'I'",
            "unsupported operand type(s) for %: 'complex' and 'I'",
            "unsupported operand type(s) for //: 'complex' and 'F'",
            "'<' not supported between instances of 'complex' and 'I'",
            "I", 0, "F", "F", "P", "P", True,
            [("rand", 1.5), ("rmod", 1j), ("Frfloordiv", 1j), ("gt", 1j),
             ("radd", 1), ("rsub", 2), ("Fradd", 1), ("Fradd", 1), ("Pradd", 1j), ("Pradd", 1j), ("Pgt", 1j)]]

def main():
    return operations()

assert_eq(main(), expected)
assert_eq(operations(), expected)
