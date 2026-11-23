# spec: PLS-315 15.6.4, 15.6.5
# description: A mapping pattern evaluates every key, then reads the
# subject's get, then checks each key against the keys before it and
# looks it up, a missing key ending the lookups, before any sub-pattern
# matches; a class pattern reads every attribute before any sub-pattern
# matches, a missing one ending the reads; their errors propagate.
from harness import *

log = []


class Keys:
    @property
    def a(self):
        log.append("key a")
        return "a"

    @property
    def b(self):
        log.append("key b")
        return "b"

    one = 1
    real_one = 1.0
    items = []


K = Keys()


class Logged:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        log.append("sub " + self.name)
        return other == 1


class S:
    a = Logged("a")
    b = Logged("b")


class M(dict):
    def __getattribute__(self, name):
        if name == "get":
            log.append("read get")
        return dict.__getattribute__(self, name)

    def get(self, key, default=None):
        log.append("get " + key)
        return dict.get(self, key, default)


def mapping(subject):
    match subject:
        case {K.a: S.a, K.b: S.b}:
            return "hit"
    return "miss"


# Every key, then get, then every lookup, then the sub-patterns.
assert_same(mapping(M(a=1, b=1)), "hit")
assert_same(log, ["key a", "key b", "read get", "get a", "get b", "sub a", "sub b"])
del log[:]
assert_same(mapping(M(a=2, b=1)), "miss")
assert_same(log, ["key a", "key b", "read get", "get a", "get b", "sub a"])
del log[:]
# A missing key ends the lookups; no sub-pattern runs.
assert_same(mapping(M(b=1, c=0)), "miss")
assert_same(log, ["key a", "key b", "read get", "get a"])
del log[:]
# Too short a subject fails before any key is evaluated.
assert_same(mapping(M(a=1)), "miss")
assert_same(log, [])
# An exact dict is looked up directly.
assert_same(mapping({"a": 1, "b": 1}), "hit")
assert_same(log, ["key a", "key b", "sub a", "sub b"])
del log[:]


def duplicate(subject):
    match subject:
        case {K.one: _, K.real_one: _}:
            return "hit"
    return "miss"


# Equal keys raise when the second is checked, after the first is found.
assert_raises(ValueError, duplicate, {1: 2, 3: 4}, message="mapping pattern checks duplicate key (1.0)")
assert_same(duplicate({2: 2, 3: 4}), "miss")


def unhashable(subject):
    match subject:
        case {K.items: _}:
            return "hit"
    return "miss"


assert_raises(TypeError, unhashable, {1: 2}, message="cannot use 'list' as a set element (unhashable type: 'list')")


class Liar(dict):
    def get(self, key, default=None):
        return "lie"


def rest(subject):
    match subject:
        case {"y": value, **others}:
            return value, others
    return "miss"


# **rest copies the subject and deletes the keys looked up.
assert_same(rest({"x": 1, "y": 2}), (2, {"x": 1}))
assert_raises(KeyError, rest, Liar(x=1), message="'y'")


class Raising(dict):
    def get(self, key, default=None):
        raise LookupError("no get")


assert_raises(LookupError, rest, Raising(y=1), message="no get")


class P:
    __match_args__ = ("a", "b")

    def __init__(self, **values):
        self.values = values

    def read(self, name):
        log.append("attr " + name)
        if name not in self.values:
            raise AttributeError(name)
        if self.values[name] is None:
            raise ValueError("boom")
        return self.values[name]

    a = property(lambda self: self.read("a"))
    b = property(lambda self: self.read("b"))


def instance(subject):
    match subject:
        case P(S.a, S.b):
            return "hit"
    return "miss"


assert_same(instance(P(a=1, b=1)), "hit")
assert_same(log, ["attr a", "attr b", "sub a", "sub b"])
del log[:]
assert_same(instance(P(a=2, b=1)), "miss")
assert_same(log, ["attr a", "attr b", "sub a"])
del log[:]
# A missing attribute ends the reads; another error propagates.
assert_same(instance(P(b=1)), "miss")
assert_same(log, ["attr a"])
del log[:]
assert_raises(ValueError, instance, P(a=None, b=1), message="boom")
assert_same(log, ["attr a"])
del log[:]


class Strange:
    __match_args__ = (1,)


def strange(subject):
    match subject:
        case Strange(_):
            return "hit"
    return "miss"


assert_raises(TypeError, strange, Strange(), message="__match_args__ elements must be strings (got int)")


def not_a_class(subject):
    match subject:
        case K.one():
            return "hit"
    return "miss"


assert_raises(TypeError, not_a_class, 1, message="class pattern must refer to a class")


class Meta(type):
    @property
    def __match_args__(cls):
        log.append("match args")
        if cls.kind == "list":
            return ["a"]
        if cls.kind == "none":
            raise AttributeError("none")
        return ("a", "b")


class Q(metaclass=Meta):
    kind = "tuple"
    a = 1
    b = property(lambda self: 2)


def meta(subject):
    match subject:
        case Q(1, b):
            return b
    return "miss"


# __match_args__ is read from the class, its metaclass's property running.
assert_same(meta(Q()), 2)
assert_same(log, ["match args"])
del log[:]
Q.kind = "list"
assert_raises(TypeError, meta, Q(), message="Q.__match_args__ must be a tuple (got list)")
Q.kind = "none"
assert_raises(TypeError, meta, Q(), message="Q() accepts 0 positional sub-patterns (2 given)")
assert_same(meta(1), "miss")
