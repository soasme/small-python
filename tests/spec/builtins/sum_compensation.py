# spec: PLS-315 19.3.35
# description: A float total adds float items and int items, an int
# subclass's and a large int's included, as floats with compensation; a
# complex total also adds complex items and, to its real part, float
# subclass items; an int too large for a float raises OverflowError. Any
# other item is added with + and leaves its stage for good: an int total
# goes on to the float and complex stages only once, then a float total to
# the complex one, and a total that leaves them, or a bool start, is
# added with + from then on.
from harness import *

class Int(int): pass
class Float(float): pass
class Zero:
    def __radd__(self, other): return 0.0

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    return [sum([1e100, 1, -1e100]), sum([1e100, Int(1), -1e100]), sum([1e100, True, -1e100]),
            sum([0.1, Int(1), 0.2, -1.0]), sum([1e100, 2 ** 70 - 2 ** 70 + 1, -1e100]),
            sum([1e100j, 1j, -1e100j]), sum([1e100 + 0j, 1, -1e100]), sum([0j, 1e100, Float(1.0), -1e100]),
            sum([1e100, Float(1.0), -1e100]),
            error(lambda: sum([1.0, 2 ** 2000])), error(lambda: sum([0j, Int(2 ** 2000)])),
            type(sum([True, 1.5])), sum([1, 2.5, Int(3)]),
            sum([Int(1), 1e100, 1.0, -1e100]), sum([1e100, Float(1.0), 1.0, -1e100]), sum([1, Zero(), 1e100, 1.0, -1e100]),
            sum([1e100, 1j, 1.0, -1e100]), sum([0j, 1e100, Zero(), 1e100, 1.0, -1e100]), sum([1, 1e100, 1.0, -1e100]),
            sum([1.5, 1j, Float(2.0), 1e100, 1.0, -1e100]), sum([1e100, 1.0, -1e100], True),
            sum([2 ** 62, 2 ** 62, -1]), sum([-2 ** 63, -1])]

expected = [1.0, 1.0, 1.0, 0.30000000000000004, 1.0, 1j, (1 + 0j), (1 + 0j), 0.0,
            ("OverflowError", "int too large to convert to float"),
            ("OverflowError", "int too large to convert to float"), float, 6.5,
            0.0, 0.0, 1.0, (1 + 1j), 0.0, 1.0, (4.5 + 1j), 0.0,
            2 ** 63 - 1, -2 ** 63 - 1]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
