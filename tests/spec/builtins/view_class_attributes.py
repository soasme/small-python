# spec: PLS-315 26.4, 20.6, 20.7
# description: the dictionary view classes hold mapping as a read-only
# getset descriptor, whose __get__ gives the view's mapping proxy; the
# keys and items classes hold isdisjoint, callable with a view first, and
# __contains__, and the values class has no __contains__ (membership
# iterates, an item's Python __eq__ called). staticmethod and classmethod
# hold a writable __dict__ descriptor for the object's attributes, a
# subclass instance's own.
from harness import assert_eq

def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__ + ": " + str(e)

d = {1: 2}
views = [d.keys(), d.values(), d.items()]
results = []
for v in views:
    K = type(v)
    m = K.__dict__["mapping"]
    results.append((type(m).__name__, m.__get__(v) == d, type(m.__get__(v)).__name__,
                    attempt(lambda: m.__set__(v, {})), "isdisjoint" in K.__dict__, "__contains__" in K.__dict__))
assert_eq(results, [
    ("getset_descriptor", True, "mappingproxy", "AttributeError: attribute 'mapping' of 'dict_keys' objects is not writable", True, True),
    ("getset_descriptor", True, "mappingproxy", "AttributeError: attribute 'mapping' of 'dict_values' objects is not writable", False, False),
    ("getset_descriptor", True, "mappingproxy", "AttributeError: attribute 'mapping' of 'dict_items' objects is not writable", True, True)])
assert_eq((type(d.keys()).isdisjoint(d.keys(), [3]), type(d.items()).isdisjoint(d.items(), [(1, 2)])), (True, False))
assert_eq(attempt(lambda: type(d.values()).isdisjoint), "AttributeError: type object 'dict_values' has no attribute 'isdisjoint'")

log = []
class E:
    def __eq__(self, other):
        for _ in (): pass
        log.append("eq")
        return True
assert_eq((5 in {1: E()}.values(), log), (True, ["eq"]))

def f(): pass
for kind in (staticmethod, classmethod):
    s = kind(f)
    descriptor = kind.__dict__["__dict__"]
    s.x = 1
    descriptor.__set__(s, {"y": 2})
    assert_eq((type(descriptor).__name__, attempt(lambda: s.x), s.y, descriptor.__get__(s) is s.__dict__),
              ("getset_descriptor", "AttributeError: '" + kind.__name__ + "' object has no attribute 'x'", 2, True))

# A subclass instance's __dict__, through the same descriptor, is its own.
class CM(classmethod): pass
sub = CM(f)
classmethod.__dict__["__dict__"].__set__(sub, {"k": 3})
assert_eq((sub.k, vars(sub), classmethod.__dict__["__dict__"].__get__(sub) is sub.__dict__), (3, {"k": 3}, True))
