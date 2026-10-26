"""Weak reference support for Python.

This module is an implementation of PEP 205. Small Python builds it into the
engine; it follows CPython 3.15's weakref, _weakref and _weakrefset modules.
The engine keeps the weak table and exposes private primitives to this
module: _weak_bind(target, reference, callback), _weak_get(reference),
_weak_callback(reference), _weak_hash(reference), and _weak_refs(target).
A callback runs at the next statement boundary after its referent dies.
"""

__all__ = ["ref", "proxy", "getweakrefcount", "getweakrefs",
           "WeakKeyDictionary", "ReferenceType", "ProxyType",
           "CallableProxyType", "ProxyTypes", "WeakValueDictionary",
           "WeakSet", "WeakMethod", "finalize"]

_GenericAlias = type(list[int])


def _type_name(obj):
    cls = type(obj)
    module = cls.__module__
    if module in ('builtins', '__main__'):
        return cls.__qualname__
    return f'{module}.{cls.__qualname__}'


class ReferenceType:
    __slots__ = ()

    def __new__(cls, ob, callback=None, /):
        if callback is None and cls is ReferenceType:
            for wr in _weak_refs(ob):
                if type(wr) is ReferenceType and _weak_callback(wr) is None:
                    return wr
        self = object.__new__(cls)
        _weak_bind(ob, self, callback)
        return self

    def __init__(self, ob, callback=None, /):
        pass

    def __call__(self, /):
        return _weak_get(self)

    @property
    def __callback__(self):
        return _weak_callback(self)

    def __hash__(self):
        return _weak_hash(self)

    def __eq__(self, other):
        if not isinstance(other, ReferenceType):
            return NotImplemented
        a, b = _weak_get(self), _weak_get(other)
        if a is None or b is None:
            return self is other
        return a == b

    def __ne__(self, other):
        if not isinstance(other, ReferenceType):
            return NotImplemented
        a, b = _weak_get(self), _weak_get(other)
        if a is None or b is None:
            return self is not other
        return a != b

    def __repr__(self):
        obj = _weak_get(self)
        if obj is None:
            return f'<weakref at {id(self):#x}; dead>'
        try:
            name = obj.__name__
        except Exception:
            name = None
        if isinstance(name, str):
            return f"<weakref at {id(self):#x}; to '{_type_name(obj)}' at {id(obj):#x} ({name})>"
        return f"<weakref at {id(self):#x}; to '{_type_name(obj)}' at {id(obj):#x}>"

    __class_getitem__ = classmethod(_GenericAlias)


ref = ReferenceType


def _unwrap(proxy):
    obj = _weak_get(proxy)
    if obj is None:
        raise ReferenceError('weakly-referenced object no longer exists')
    return obj


def _arg(value):
    return _unwrap(value) if type(value) in ProxyTypes else value


class ProxyType:
    __slots__ = ()
    __hash__ = None

    def __getattribute__(self, name):
        return getattr(_unwrap(self), name)

    def __setattr__(self, name, value):
        setattr(_unwrap(self), name, value)

    def __delattr__(self, name):
        delattr(_unwrap(self), name)

    def __repr__(self):
        obj = _weak_get(self)
        if obj is None:
            return f'<weakproxy at {id(self):#x}; dead>'
        return f"<weakproxy at {id(self):#x}; to '{_type_name(obj)}' at {id(obj):#x}>"

    def __str__(self):
        return str(_unwrap(self))

    def __bytes__(self):
        return bytes(_unwrap(self))

    def __bool__(self):
        return bool(_unwrap(self))

    def __len__(self):
        return len(_unwrap(self))

    def __contains__(self, value):
        return value in _unwrap(self)

    def __getitem__(self, key):
        return _unwrap(self)[key]

    def __setitem__(self, key, value):
        _unwrap(self)[key] = value

    def __delitem__(self, key):
        del _unwrap(self)[key]

    def __iter__(self):
        return iter(_unwrap(self))

    def __next__(self):
        obj = _unwrap(self)
        if not hasattr(type(obj), '__next__'):
            raise TypeError(f"Weakref proxy referenced a non-iterator '{type(obj).__name__}' object")
        return next(obj)

    def __reversed__(self):
        return reversed(_unwrap(self))

    def __index__(self):
        return _unwrap(self).__index__()

    def __int__(self):
        return int(_unwrap(self))

    def __float__(self):
        return float(_unwrap(self))

    def __neg__(self):
        return -_unwrap(self)

    def __pos__(self):
        return +_unwrap(self)

    def __abs__(self):
        return abs(_unwrap(self))

    def __invert__(self):
        return ~_unwrap(self)

    def __lt__(self, other):
        return _unwrap(self) < _arg(other)

    def __le__(self, other):
        return _unwrap(self) <= _arg(other)

    def __eq__(self, other):
        return _unwrap(self) == _arg(other)

    def __ne__(self, other):
        return _unwrap(self) != _arg(other)

    def __gt__(self, other):
        return _unwrap(self) > _arg(other)

    def __ge__(self, other):
        return _unwrap(self) >= _arg(other)


def _binary(op):
    def forward(self, other):
        return op(_arg(self), _arg(other))

    def reflected(self, other):
        return op(_arg(other), _arg(self))
    return forward, reflected


for _name, _op in (
        ('add', lambda a, b: a + b), ('sub', lambda a, b: a - b),
        ('mul', lambda a, b: a * b), ('matmul', lambda a, b: a @ b),
        ('truediv', lambda a, b: a / b), ('floordiv', lambda a, b: a // b),
        ('mod', lambda a, b: a % b), ('divmod', divmod),
        ('pow', lambda a, b: a ** b), ('lshift', lambda a, b: a << b),
        ('rshift', lambda a, b: a >> b), ('and', lambda a, b: a & b),
        ('xor', lambda a, b: a ^ b), ('or', lambda a, b: a | b)):
    _forward, _reflected = _binary(_op)
    setattr(ProxyType, f'__{_name}__', _forward)
    setattr(ProxyType, f'__r{_name}__', _reflected)

for _name, _op in (
        ('iadd', lambda a, b: a.__iadd__(b) if hasattr(type(a), '__iadd__') else a + b),
        ('isub', lambda a, b: a.__isub__(b) if hasattr(type(a), '__isub__') else a - b),
        ('imul', lambda a, b: a.__imul__(b) if hasattr(type(a), '__imul__') else a * b),
        ('imatmul', lambda a, b: a.__imatmul__(b) if hasattr(type(a), '__imatmul__') else a @ b),
        ('itruediv', lambda a, b: a.__itruediv__(b) if hasattr(type(a), '__itruediv__') else a / b),
        ('ifloordiv', lambda a, b: a.__ifloordiv__(b) if hasattr(type(a), '__ifloordiv__') else a // b),
        ('imod', lambda a, b: a.__imod__(b) if hasattr(type(a), '__imod__') else a % b),
        ('ipow', lambda a, b: a.__ipow__(b) if hasattr(type(a), '__ipow__') else a ** b),
        ('ilshift', lambda a, b: a.__ilshift__(b) if hasattr(type(a), '__ilshift__') else a << b),
        ('irshift', lambda a, b: a.__irshift__(b) if hasattr(type(a), '__irshift__') else a >> b),
        ('iand', lambda a, b: a.__iand__(b) if hasattr(type(a), '__iand__') else a & b),
        ('ixor', lambda a, b: a.__ixor__(b) if hasattr(type(a), '__ixor__') else a ^ b),
        ('ior', lambda a, b: a.__ior__(b) if hasattr(type(a), '__ior__') else a | b)):
    setattr(ProxyType, f'__{_name}__', _binary(_op)[0])
del _name, _op, _forward, _reflected


class CallableProxyType(ProxyType):
    __slots__ = ()

    def __call__(self, /, *args, **kwargs):
        return _unwrap(self)(*args, **kwargs)


ProxyTypes = (ProxyType, CallableProxyType)


def proxy(object, callback=None, /):
    """Create a proxy object that weakly references 'object'.

    'callback', if given, is called with a reference to the
    proxy when 'object' is about to be finalized."""
    cls = CallableProxyType if callable(object) else ProxyType
    if callback is None:
        for wr in _weak_refs(object):
            if type(wr) is cls and _weak_callback(wr) is None:
                return wr
    self = ProxyType.__new__(cls)
    _weak_bind(object, self, callback)
    return self


def getweakrefcount(object, /):
    """Return the number of weak references to 'object'."""
    return len(_weak_refs(object))


def getweakrefs(object, /):
    """Return a list of all weak reference objects pointing to 'object'."""
    return _weak_refs(object)


def _remove_dead_weakref(dct, key, /):
    """Atomically remove key from dict if it points to a dead weakref."""
    try:
        wr = dct[key]
    except KeyError:
        return
    if wr() is None:
        del dct[key]


def _is_mapping(other):
    return hasattr(type(other), 'keys') and hasattr(type(other), '__getitem__')


# Small Python closures retain their whole defining environment, so the callbacks
# below come from small factories that capture only what CPython's do.
def _weakset_remover(selfref):
    def _remove(item):
        self = selfref()
        if self is not None:
            self.data.discard(item)
    return _remove


def _value_remover(selfref):
    def remove(wr):
        self = selfref()
        if self is not None:
            _remove_dead_weakref(self.data, wr.key)
    return remove


def _key_remover(selfref):
    def remove(k):
        self = selfref()
        if self is not None:
            try:
                del self.data[k]
            except KeyError:
                pass
    return remove


def _method_callback(self_wr, callback):
    def _cb(arg):
        self = self_wr[0]()
        if self._alive:
            self._alive = False
            if callback is not None:
                callback(self)
    return _cb


class _MutableMapping:
    # The collections.abc.MutableMapping mixins these classes rely on.
    __reversed__ = None

    def clear(self):
        try:
            while True:
                self.popitem()
        except KeyError:
            pass

    def __eq__(self, other):
        if not _is_mapping(other):
            return NotImplemented
        return dict(self.items()) == dict(other.items())

    __class_getitem__ = classmethod(_GenericAlias)


class WeakSet:
    def __init__(self, data=None):
        self.data = set()
        self._remove = _weakset_remover(ref(self))
        if data is not None:
            self.update(data)

    def __iter__(self):
        for itemref in self.data.copy():
            item = itemref()
            if item is not None:
                yield item

    def __len__(self):
        return len(self.data)

    def __contains__(self, item):
        try:
            wr = ref(item)
        except TypeError:
            return False
        return wr in self.data

    def __reduce__(self):
        return self.__class__, (list(self),), self.__getstate__()

    def add(self, item):
        self.data.add(ref(item, self._remove))

    def clear(self):
        self.data.clear()

    def copy(self):
        return self.__class__(self)

    def pop(self):
        while True:
            try:
                itemref = self.data.pop()
            except KeyError:
                raise KeyError('pop from empty WeakSet') from None
            item = itemref()
            if item is not None:
                return item

    def remove(self, item):
        self.data.remove(ref(item))

    def discard(self, item):
        self.data.discard(ref(item))

    def update(self, other):
        for element in other:
            self.add(element)

    def __ior__(self, other):
        self.update(other)
        return self

    def difference(self, other):
        newset = self.copy()
        newset.difference_update(other)
        return newset
    __sub__ = difference

    def difference_update(self, other):
        self.__isub__(other)

    def __isub__(self, other):
        if self is other:
            self.data.clear()
        else:
            self.data.difference_update(ref(item) for item in other)
        return self

    def intersection(self, other):
        return self.__class__(item for item in other if item in self)
    __and__ = intersection

    def intersection_update(self, other):
        self.__iand__(other)

    def __iand__(self, other):
        self.data.intersection_update(ref(item) for item in other)
        return self

    def issubset(self, other):
        return self.data.issubset(ref(item) for item in other)
    __le__ = issubset

    def __lt__(self, other):
        return self.data < set(map(ref, other))

    def issuperset(self, other):
        return self.data.issuperset(ref(item) for item in other)
    __ge__ = issuperset

    def __gt__(self, other):
        return self.data > set(map(ref, other))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.data == set(map(ref, other))

    def symmetric_difference(self, other):
        newset = self.copy()
        newset.symmetric_difference_update(other)
        return newset
    __xor__ = symmetric_difference

    def symmetric_difference_update(self, other):
        self.__ixor__(other)

    def __ixor__(self, other):
        if self is other:
            self.data.clear()
        else:
            self.data.symmetric_difference_update(ref(item, self._remove) for item in other)
        return self

    def union(self, other):
        return self.__class__(e for s in (self, other) for e in s)
    __or__ = union

    def isdisjoint(self, other):
        return len(self.intersection(other)) == 0

    def __repr__(self):
        return repr(self.data)

    __class_getitem__ = classmethod(_GenericAlias)


class WeakMethod(ref):
    """
    A custom `weakref.ref` subclass which simulates a weak reference to
    a bound method, working around the lifetime problem of bound methods.
    """

    __slots__ = "_func_ref", "_meth_type", "_alive", "__weakref__"

    def __new__(cls, meth, callback=None):
        try:
            obj = meth.__self__
            func = meth.__func__
        except AttributeError:
            raise TypeError("argument should be a bound method, not {}"
                            .format(type(meth))) from None
        self_wr = []
        _cb = _method_callback(self_wr, callback)
        self = ref.__new__(cls, obj, _cb)
        self._func_ref = ref(func, _cb)
        self._meth_type = type(meth)
        self._alive = True
        self_wr.append(ref(self))
        return self

    def __call__(self):
        obj = super().__call__()
        func = self._func_ref()
        if obj is None or func is None:
            return None
        return self._meth_type(func, obj)

    def __eq__(self, other):
        if isinstance(other, WeakMethod):
            if not self._alive or not other._alive:
                return self is other
            return ref.__eq__(self, other) and self._func_ref == other._func_ref
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, WeakMethod):
            if not self._alive or not other._alive:
                return self is not other
            return ref.__ne__(self, other) or self._func_ref != other._func_ref
        return NotImplemented

    __hash__ = ref.__hash__


class WeakValueDictionary(_MutableMapping):
    """Mapping class that references values weakly.

    Entries in the dictionary will be discarded when no strong
    reference to the value exists anymore
    """

    def __init__(self, other=(), /, **kw):
        self._remove = _value_remover(ref(self))
        self.data = {}
        self.update(other, **kw)

    def __getitem__(self, key):
        o = self.data[key]()
        if o is None:
            raise KeyError(key)
        else:
            return o

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def __contains__(self, key):
        try:
            o = self.data[key]()
        except KeyError:
            return False
        return o is not None

    def __repr__(self):
        return "<%s at %#x>" % (self.__class__.__name__, id(self))

    def __setitem__(self, key, value):
        self.data[key] = KeyedRef(value, self._remove, key)

    def copy(self):
        new = WeakValueDictionary()
        for key, wr in self.data.copy().items():
            o = wr()
            if o is not None:
                new[key] = o
        return new

    __copy__ = copy

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = self.__class__()
        for key, wr in self.data.copy().items():
            o = wr()
            if o is not None:
                new[deepcopy(key, memo)] = o
        return new

    def get(self, key, default=None):
        try:
            wr = self.data[key]
        except KeyError:
            return default
        else:
            o = wr()
            if o is None:
                return default
            else:
                return o

    def items(self):
        for k, wr in self.data.copy().items():
            v = wr()
            if v is not None:
                yield k, v

    def keys(self):
        for k, wr in self.data.copy().items():
            if wr() is not None:
                yield k

    __iter__ = keys

    def itervaluerefs(self):
        """Return an iterator that yields the weak references to the values."""
        yield from self.data.copy().values()

    def values(self):
        for wr in self.data.copy().values():
            obj = wr()
            if obj is not None:
                yield obj

    def popitem(self):
        while True:
            key, wr = self.data.popitem()
            o = wr()
            if o is not None:
                return key, o

    def pop(self, key, *args):
        try:
            o = self.data.pop(key)()
        except KeyError:
            o = None
        if o is None:
            if args:
                return args[0]
            else:
                raise KeyError(key)
        else:
            return o

    def setdefault(self, key, default=None):
        try:
            o = self.data[key]()
        except KeyError:
            o = None
        if o is None:
            self.data[key] = KeyedRef(default, self._remove, key)
            return default
        else:
            return o

    def update(self, other=None, /, **kwargs):
        d = self.data
        if other is not None:
            if not hasattr(other, "items"):
                other = dict(other)
            for key, o in other.items():
                d[key] = KeyedRef(o, self._remove, key)
        for key, o in kwargs.items():
            d[key] = KeyedRef(o, self._remove, key)

    def valuerefs(self):
        """Return a list of weak references to the values."""
        return list(self.data.copy().values())

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        if _is_mapping(other):
            c = self.copy()
            c.update(other)
            return c
        return NotImplemented

    def __ror__(self, other):
        if _is_mapping(other):
            c = self.__class__()
            c.update(other)
            c.update(self)
            return c
        return NotImplemented


class KeyedRef(ref):
    """Specialized reference that includes a key corresponding to the value."""

    __slots__ = "key",

    def __new__(type, ob, callback, key):
        self = ref.__new__(type, ob, callback)
        self.key = key
        return self

    def __init__(self, ob, callback, key):
        super().__init__(ob, callback)


class WeakKeyDictionary(_MutableMapping):
    """ Mapping class that references keys weakly."""

    def __init__(self, dict=None):
        self.data = {}
        self._remove = _key_remover(ref(self))
        if dict is not None:
            self.update(dict)

    def __delitem__(self, key):
        del self.data[ref(key)]

    def __getitem__(self, key):
        return self.data[ref(key)]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return "<%s at %#x>" % (self.__class__.__name__, id(self))

    def __setitem__(self, key, value):
        self.data[ref(key, self._remove)] = value

    def copy(self):
        new = WeakKeyDictionary()
        for key, value in self.data.copy().items():
            o = key()
            if o is not None:
                new[o] = value
        return new

    __copy__ = copy

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = self.__class__()
        for key, value in self.data.copy().items():
            o = key()
            if o is not None:
                new[o] = deepcopy(value, memo)
        return new

    def get(self, key, default=None):
        return self.data.get(ref(key), default)

    def __contains__(self, key):
        try:
            wr = ref(key)
        except TypeError:
            return False
        return wr in self.data

    def items(self):
        for wr, value in self.data.copy().items():
            key = wr()
            if key is not None:
                yield key, value

    def keys(self):
        for wr in self.data.copy():
            obj = wr()
            if obj is not None:
                yield obj

    __iter__ = keys

    def values(self):
        for wr, value in self.data.copy().items():
            if wr() is not None:
                yield value

    def keyrefs(self):
        """Return a list of weak references to the keys."""
        return list(self.data)

    def popitem(self):
        while True:
            key, value = self.data.popitem()
            o = key()
            if o is not None:
                return o, value

    def pop(self, key, *args):
        return self.data.pop(ref(key), *args)

    def setdefault(self, key, default=None):
        return self.data.setdefault(ref(key, self._remove), default)

    def update(self, dict=None, /, **kwargs):
        if kwargs:
            msg = ("Keyword arguments are not supported: "
                   "cannot create weak reference to 'str' object")
            raise TypeError(msg)
        d = self.data
        if dict is not None:
            if not hasattr(dict, "items"):
                dict = type({})(dict)
            for key, value in dict.items():
                d[ref(key, self._remove)] = value

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        if _is_mapping(other):
            c = self.copy()
            c.update(other)
            return c
        return NotImplemented

    def __ror__(self, other):
        if _is_mapping(other):
            c = self.__class__()
            c.update(other)
            c.update(self)
            return c
        return NotImplemented


class finalize:
    """Class for finalization of weakrefable objects

    finalize(obj, func, *args, **kwargs) returns a callable finalizer
    object which will be called when obj is garbage collected. The
    first time the finalizer is called it evaluates func(*arg, **kwargs)
    and returns the result. After this the finalizer is dead, and
    calling it just returns None.

    Small Python has no interpreter-exit hook, so the atexit flag is kept
    but finalizers do not run at exit.
    """

    __slots__ = ()
    _registry = {}
    _shutdown = False
    _index = 0
    _dirty = False

    class _Info:
        __slots__ = ("weakref", "func", "args", "kwargs", "atexit", "index")

    def __init__(self, obj, func, /, *args, **kwargs):
        info = self._Info()
        info.weakref = ref(obj, self)
        info.func = func
        info.args = args
        info.kwargs = kwargs or None
        info.atexit = True
        info.index = finalize._index
        finalize._index += 1
        self._registry[self] = info
        finalize._dirty = True

    def __call__(self, _=None):
        """If alive then mark as dead and return func(*args, **kwargs);
        otherwise return None"""
        info = self._registry.pop(self, None)
        if info and not self._shutdown:
            return info.func(*info.args, **(info.kwargs or {}))

    def detach(self):
        """If alive then mark as dead and return (obj, func, args, kwargs);
        otherwise return None"""
        info = self._registry.get(self)
        obj = info and info.weakref()
        if obj is not None and self._registry.pop(self, None):
            return (obj, info.func, info.args, info.kwargs or {})

    def peek(self):
        """If alive then return (obj, func, args, kwargs);
        otherwise return None"""
        info = self._registry.get(self)
        obj = info and info.weakref()
        if obj is not None:
            return (obj, info.func, info.args, info.kwargs or {})

    @property
    def alive(self):
        """Whether finalizer is alive"""
        return self in self._registry

    @property
    def atexit(self):
        """Whether finalizer should be called at exit"""
        info = self._registry.get(self)
        return bool(info) and info.atexit

    @atexit.setter
    def atexit(self, value):
        info = self._registry.get(self)
        if info:
            info.atexit = bool(value)

    def __repr__(self):
        info = self._registry.get(self)
        obj = info and info.weakref()
        if obj is None:
            return '<%s object at %#x; dead>' % (type(self).__name__, id(self))
        else:
            return '<%s object at %#x; for %r at %#x>' % \
                (type(self).__name__, id(self), type(obj).__name__, id(obj))
