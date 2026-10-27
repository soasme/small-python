# spec: PLS-315 26.4, 26.6
# description: dict views are live, ordered, and (for keys and items) set-like.
from harness import *

d = {"a": 1, "b": 2}
keys, values, items = d.keys(), d.values(), d.items()
d["c"] = 3
assert_eq((len(keys), list(keys), list(values), list(items)), (3, ["a", "b", "c"], [1, 2, 3], [("a", 1), ("b", 2), ("c", 3)]))
assert_eq(list(reversed(keys)), ["c", "b", "a"])
assert_eq(list(reversed(values)), [3, 2, 1])
assert_eq(list(reversed(items)), [("c", 3), ("b", 2), ("a", 1)])
assert_true("a" in keys and 2 in values and ("b", 2) in items)
assert_false(("b", 3) in items)
assert_false(("z", 1) in items)
assert_eq(keys.mapping, {"a": 1, "b": 2, "c": 3})
assert_type(keys.mapping, type(type.__dict__))
assert_raises(AttributeError, setattr, keys, "mapping", {})
assert_eq(repr({"a": 1}.keys()), "dict_keys(['a'])")
assert_eq(repr({"a": 1}.values()), "dict_values([1])")
assert_eq(repr({"a": 1}.items()), "dict_items([('a', 1)])")

# Set-like operations.
assert_eq(keys, {"a", "b", "c"})
assert_true(keys < {"a", "b", "c", "d"})
assert_true(keys >= {"a"})
assert_eq(keys & ["a", "z"], {"a"})
assert_eq(keys | ["z"], {"a", "b", "c", "z"})
assert_eq(keys - "a", {"b", "c"})
assert_eq(keys ^ {"a", "z"}, {"b", "c", "z"})
assert_type(keys & ["a"], set)
assert_true(keys.isdisjoint(["x"]))
assert_eq(items & {("a", 1)}, {("a", 1)})
assert_true(items <= {("a", 1), ("b", 2), ("c", 3), ("d", 4)})
assert_eq({"x": 1}.keys(), {"x": 1}.keys())
assert_eq({"x": 1}.items(), frozendict(x=1).items())
# A values view supports none of these; its == is identity.
assert_ne(values, values.__class__ and d.values())
assert_eq(values, values)
assert_raises(TypeError, lambda: values & {1})
assert_raises(TypeError, lambda: values < values)
fd = frozendict(k=1)
assert_eq(list(fd.keys()), ["k"])
assert_eq(fd.keys().mapping, {"k": 1})

# mappingproxy.
MappingProxy = type(type.__dict__)
assert_eq(MappingProxy.__name__, "mappingproxy")
assert_eq(MappingProxy.__module__, "builtins")
backing = {"a": 1}
proxy = MappingProxy(backing)
backing["b"] = 2
assert_eq((proxy["b"], "a" in proxy, len(proxy), list(proxy), list(reversed(proxy))), (2, True, 2, ["a", "b"], ["b", "a"]))
assert_eq((proxy.get("z", 0), list(proxy.keys()), list(proxy.values()), list(proxy.items())),
          (0, ["a", "b"], [1, 2], [("a", 1), ("b", 2)]))
assert_eq(proxy.copy(), backing)
assert_true(proxy.copy() is not backing)
assert_eq(proxy | {"c": 3}, {"a": 1, "b": 2, "c": 3})
assert_type(proxy | {"c": 3}, dict)
assert_eq(proxy, backing)
assert_eq(repr(MappingProxy({"a": 1})), "mappingproxy({'a': 1})")
assert_eq(hash(MappingProxy(frozendict(a=1))), hash(frozendict(a=1)))
assert_raises(TypeError, hash, proxy)
e = assert_raises(TypeError, exec, "p['x'] = 1", {"p": proxy})
assert_eq(str(e), "'mappingproxy' object does not support item assignment")
e = assert_raises(TypeError, exec, "del p['a']", {"p": proxy})
assert_eq(str(e), "'mappingproxy' object does not support item deletion")
e = assert_raises(TypeError, exec, "p |= {}", {"p": proxy})
assert_eq(str(e), "'|=' is not supported by mappingproxy; use '|' instead")
e = assert_raises(TypeError, MappingProxy, [1])
assert_eq(str(e), "mappingproxy() argument must be a mapping, not list")
with assert_raises(TypeError):
    class Sub(MappingProxy):
        pass
