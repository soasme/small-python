# spec: PLS-315 15.6.3, 15.6.5, 14.2
# description: How a sequence pattern reads its subject (length, index, or unpacking), and class patterns checking instances through __instancecheck__.
from harness import *

log = []
class Logged(list):
    def __len__(self):
        log.append("len")
        return list.__len__(self)
    def __getitem__(self, i):
        log.append(i)
        return list.__getitem__(self, i)
    def __iter__(self):
        log.append("iter")
        return list.__iter__(self)

def reads(subject, pattern):
    """The result of matching subject against one sequence pattern, and the reads made."""
    log.clear()
    namespace = {"subject": subject}
    run("match subject:\n    case " + pattern + ":\n        result = True\n    case _:\n        result = False\n", namespace)
    namespace.pop("subject"); namespace.pop("__builtins__", None)
    return namespace, list(log)

s = Logged([1, 2, 3, 4])
# Only wildcards: the length alone, or nothing for a lone *_.
assert_eq(reads(s, "[_, _, _, _]"), ({"result": True}, ["len"]))
assert_eq(reads(s, "[*_]"), ({"result": True}, []))
assert_eq(reads(s, "[_, *_]"), ({"result": True}, ["len"]))
# A *_ star: items by index, those after the star from a fresh length.
assert_eq(reads(s, "[a, *_, b]"), ({"a": 1, "b": 4, "result": True}, ["len", 0, "len", 3]))
assert_eq(reads(s, "[_, x, *_]"), ({"x": 2, "result": True}, ["len", 1]))
assert_eq(reads(s, "[*_, 9]"), ({"result": False}, ["len", "len", 3]))
# Otherwise the subject is unpacked by iteration before any item is matched.
assert_eq(reads(s, "[a, b, c, d]"), ({"a": 1, "b": 2, "c": 3, "d": 4, "result": True}, ["len", "iter"]))
assert_eq(reads(s, "[a, *rest]"), ({"a": 1, "rest": [2, 3, 4], "result": True}, ["len", "iter"]))
assert_eq(reads(s, "[*rest]"), ({"rest": [1, 2, 3, 4], "result": True}, ["iter"]))
assert_eq(reads(s, "[a, 9, c, d]"), ({"result": False}, ["len", "iter"]))
assert_eq(reads(s, "[a, b]"), ({"result": False}, ["len"]))

# Unpacking raises as a target list does when the length misled.
class Liar(list):
    def __len__(self):
        return 2
e = assert_raises(ValueError, run, "match Liar([1, 2, 3]):\n    case [a, b]:\n        pass\n", {"Liar": Liar})
assert_eq(str(e), "too many values to unpack (expected 2)")
namespace = {"Liar": Liar}
run("match Liar([1, 2, 3]):\n    case [a, *_]:\n        pass\n", namespace)
assert_eq(namespace["a"], 1)

# memoryview is a sequence for matching; str, bytes and bytearray are not.
for subject, expected in ((memoryview(b"ab"), (97, 98)), (memoryview(b"ab").cast("b"), (97, 98)),
                          (range(2), (0, 1)), ("ab", None), (b"ab", None), (bytearray(b"ab"), None)):
    match subject:
        case [x, y]:
            result = x, y
        case _:
            result = None
    assert_eq(result, expected, type(subject).__name__)

# Class patterns test the subject with isinstance(), so __instancecheck__ runs.
checked = []
class Meta(type):
    def __instancecheck__(cls, instance):
        checked.append(instance)
        return instance == "yes"
class C(metaclass=Meta):
    __match_args__ = ("upper",)
match "yes":
    case C(upper=u):
        result = u()
assert_eq((result, checked), ("YES", ["yes"]))
match "no":
    case C():
        result = "matched"
    case _:
        result = "not"
assert_eq(result, "not")
class Refuse(type):
    def __instancecheck__(cls, instance):
        raise TypeError("refused")
class R(metaclass=Refuse):
    pass
e = assert_raises(TypeError, run, "match 1:\n    case R():\n        pass\n", {"R": R})
assert_eq(str(e), "refused")

# Small integers are shared (Annex D), as matched items show.
x = 7
match x,:
    case y,:
        assert_is(y, x)
assert_true(int("7") is 7 and -5 is int("-5") and int("256") is 256)
