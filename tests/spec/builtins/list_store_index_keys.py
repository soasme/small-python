# spec: PLS-315 25.1, 14.2
# description: a list item assignment takes its index from a bool or an
# object's __index__, Python or native, counts a negative index from the
# end, in a list subclass too, and a magnitude past an index-sized
# integer is an IndexError.
from harness import *
class PyIndex:
    def __index__(self): return 1
class NativeIndex:
    __index__ = (1).__index__
class Sub(list): pass
def stores():
    l = [0, 0, 0]
    l[True] = "t"; l[PyIndex()] = "i"; l[NativeIndex()] = "n"
    s = Sub([0, 0]); s[True] = "st"; s[-1] = "neg"
    pair = [0, 0]; pair[False], pair[True] = "x", "y"
    try: l[2**70] = 1
    except IndexError as e: error = str(e)
    return l, s, pair, error
assert_eq(stores(), ([0, "n", 0], [0, "neg"], ["x", "y"], "cannot fit 'int' into an index-sized integer"))
