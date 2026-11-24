# spec: PLS-315 22.2
# description: bool's own bitwise methods require a bool, decline a
# non-int and give a bool for two bools; int's own methods give an int.
from harness import assert_eq, assert_raises
for name in ('__and__', '__rand__', '__or__', '__ror__', '__xor__', '__rxor__', '__invert__'):
    method = vars(bool)[name]
    assert_eq((method.__objclass__, method is getattr(int, name)), (bool, False))
    assert_raises(TypeError, method, 1, *(() if name == '__invert__' else (True,)),
                  message="descriptor '%s' requires a 'bool' object but received a 'int'" % name)
assert_eq([bool.__and__(True, True), bool.__or__(False, True), bool.__xor__(True, True), bool.__rand__(True, 3),
           bool.__ror__(False, 2), bool.__and__(True, 1.0), bool.__invert__(True)],
          [True, True, False, 1, 2, NotImplemented, -2])
assert_eq([type(r) for r in (bool.__and__(True, True), bool.__and__(True, 3))], [bool, int])
assert_eq([int.__and__(True, True), int.__or__(False, True), int.__xor__(True, False), int.__rand__(True, True)], [1, 1, 1, 1])
assert_eq({type(int.__and__(True, True)), type(int.__or__(True, False))}, {int})
assert_eq((True & True, True | 0, 3 & True, False ^ False), (True, 1, 1, False))
