# spec: PLS-315 16.6.2, 17.2
# description: a module's __annotate__ and __annotations__ replace each other; __annotate__ cannot be deleted.
from harness import *
import annotated

assert_eq(annotated.__annotations__, {"x": int})
annotated.__annotations__ = {"y": str}
assert_eq((annotated.__annotate__, annotated.__annotations__), (None, {"y": str}))
annotated.__annotate__ = lambda format: {"z": 1}
assert_eq(annotated.__annotations__, {"z": 1})
del annotated.__annotations__
assert_eq(str(assert_raises(AttributeError, delattr, annotated, "__annotations__")), "__annotations__")
assert_eq(annotated.__annotations__, {})
assert_eq(str(assert_raises(TypeError, delattr, annotated, "__annotate__")), "cannot delete __annotate__ attribute")
assert_eq(str(assert_raises(TypeError, setattr, annotated, "__annotate__", 1)), "__annotate__ must be callable or None")
assert_eq(str(assert_raises(AttributeError, delattr, annotated, "__dict__")), "readonly attribute")
# __annotate__ must return a dict (a subclass will do); a class's
# non-callable __annotate__ means no annotations.
class Annotations(dict): pass
def subclassed(): pass
subclassed.__annotate__ = lambda format: Annotations(a=int)
assert_eq(type(subclassed.__annotations__), Annotations)
def bad(): pass
bad.__annotate__ = lambda format: 1
assert_eq(str(assert_raises(TypeError, getattr, bad, "__annotations__")), "__annotate__() must return a dict, not int")
class Plain:
    __annotate__ = 5
assert_eq(Plain.__annotations__, {})
M = type(__import__("builtins"))
named = M("it's")
named.__file__ = 5
assert_eq(repr(named), "<module \"it's\" from 5>")
