# spec: PLS-315 7.2.4
# description: a comparison of a builtin's value (a set, list, tuple, dict,
# str or int) with an instance of a proper subclass of its type calls the
# subclass's reflected Python comparison first, which may loop; its
# NotImplemented falls back to the builtin's own comparison, and an
# exception it raises propagates. A subclass without its own method
# compares as its builtin value. Inside functions as at module level.
from harness import *

log = []

class OwnSet(set):
    def __eq__(self, o):
        for _ in (): pass
        log.append("set eq")
        return "own"
    def __gt__(self, o):
        for _ in (): pass
        log.append("set gt")
        return NotImplemented

class OwnList(list):
    def __eq__(self, o):
        for _ in (): pass
        log.append("list eq")
        return NotImplemented
    def __ge__(self, o):
        for _ in (): pass
        log.append("list ge")
        return 7

class OwnTuple(tuple):
    def __lt__(self, o):
        for _ in (): pass
        log.append("tuple lt")
        raise KeyError("lt")

class OwnDict(dict):
    def __ne__(self, o):
        for _ in (): pass
        log.append("dict ne")
        return False

class OwnStr(str):
    def __eq__(self, o):
        for _ in (): pass
        log.append("str eq")
        return o == "x"

class OwnInt(int):
    def __lt__(self, o):
        for _ in (): pass
        log.append("int lt")
        return "reflected"

class PlainSet(set): pass

def compare():
    out = [{1} == OwnSet({1}), {1} < OwnSet({1}), {2} < OwnSet({1}), [1] == OwnList([1]), [2] <= OwnList([1]),
           {1: 2} != OwnDict({1: 2}), "x" == OwnStr("y"), 5 > OwnInt(3), {1} == PlainSet({1}), (1,) <= OwnTuple((1,))]
    try: (1,) > OwnTuple((0,))
    except KeyError as e: out.append(e.args)
    return out

expected = ["own", False, False, True, 7, False, True, "reflected", True, True, ("lt",)]
expected_log = ["set eq", "set gt", "set gt", "list eq", "list ge", "dict ne", "str eq", "int lt", "tuple lt"]
assert_eq(compare(), expected)
assert_eq(log, expected_log)
log.clear()
assert_eq([{1} == OwnSet({1}), [1] == OwnList([1]), 5 > OwnInt(3)], ["own", True, "reflected"])
assert_eq(log, ["set eq", "list eq", "int lt"])
