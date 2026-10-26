'''This module implements specialized container datatypes providing
alternatives to Python's general purpose built-in containers, dict,
list, set, and tuple.

* namedtuple   factory function for creating tuple subclasses with named fields
* deque        list-like container with fast appends and pops on either end
* ChainMap     dict-like class for creating a single view of multiple mappings
* Counter      dict subclass for counting hashable objects
* OrderedDict  dict subclass that remembers the order entries were added
* defaultdict  dict subclass that calls a factory function to supply missing values
* UserDict     wrapper around dictionary objects for easier dict subclassing
* UserList     wrapper around list objects for easier list subclassing
* UserString   wrapper around string objects for easier string subclassing

slim.py builds this module into the engine. namedtuple, Counter, ChainMap,
UserDict, UserList, and UserString are CPython 3.15's pure-Python code;
deque, defaultdict, and OrderedDict follow its C implementations. There is
no collections.abc: private mixins supply the methods these classes inherit
from it.
'''

__all__ = [
    'ChainMap',
    'Counter',
    'OrderedDict',
    'UserDict',
    'UserList',
    'UserString',
    'defaultdict',
    'deque',
    'namedtuple',
]

_GenericAlias = type(list[int])
_mappingproxy = type({}.keys().mapping)


class _sys:
    maxsize = 9223372036854775807
    intern = staticmethod(lambda string: string)
    _getframemodulename = _caller_module


_KEYWORDS = frozenset([
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
    'while', 'with', 'yield'])


def _iskeyword(name):
    return name in _KEYWORDS


def _itemgetter(index):
    return lambda item: item[index]


def _eq(a, b):
    return a == b


def _repeat(element, times):
    for _ in range(times):
        yield element


def _starmap(function, iterable):
    for args in iterable:
        yield function(*args)


class _chain:
    @staticmethod
    def from_iterable(iterables):
        for iterable in iterables:
            yield from iterable


def _nlargest(n, iterable, key):
    return sorted(iterable, key=key, reverse=True)[:max(n, 0)]


def _copy(x):
    copier = getattr(type(x), '__copy__', None)
    if copier is not None:
        return copier(x)
    raise TypeError(f"un(shallow)copyable object of type {type(x)}")


def _recursive_repr(fillvalue='...'):
    'Decorator to make a repr function return fillvalue for a recursive call'

    def decorating_function(user_function):
        repr_running = set()

        def wrapper(self):
            key = id(self)
            if key in repr_running:
                return fillvalue
            repr_running.add(key)
            try:
                result = user_function(self)
            finally:
                repr_running.discard(key)
            return result

        wrapper.__module__ = getattr(user_function, '__module__')
        wrapper.__doc__ = getattr(user_function, '__doc__')
        wrapper.__name__ = getattr(user_function, '__name__')
        wrapper.__qualname__ = getattr(user_function, '__qualname__')
        return wrapper

    return decorating_function


def _is_mapping(other):
    return isinstance(other, (dict, _Mapping, _mappingproxy))


class _KeysView:
    __slots__ = '_mapping',

    def __init__(self, mapping):
        self._mapping = mapping

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0.__class__.__name__}({0._mapping!r})'.format(self)

    def __contains__(self, key):
        return key in self._mapping

    def __iter__(self):
        yield from self._mapping


class _ItemsView(_KeysView):
    __slots__ = ()

    def __contains__(self, item):
        key, value = item
        try:
            v = self._mapping[key]
        except KeyError:
            return False
        else:
            return v is value or v == value

    def __iter__(self):
        for key in self._mapping:
            yield (key, self._mapping[key])


class _ValuesView(_KeysView):
    __slots__ = ()

    def __contains__(self, value):
        for key in self._mapping:
            v = self._mapping[key]
            if v is value or v == value:
                return True
        return False

    def __iter__(self):
        for key in self._mapping:
            yield self._mapping[key]


_KeysView.__name__ = _KeysView.__qualname__ = 'KeysView'
_ItemsView.__name__ = _ItemsView.__qualname__ = 'ItemsView'
_ValuesView.__name__ = _ValuesView.__qualname__ = 'ValuesView'


class _Mapping:
    # The collections.abc.Mapping mixin methods.
    __slots__ = ()
    __reversed__ = None

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def keys(self):
        return _KeysView(self)

    def items(self):
        return _ItemsView(self)

    def values(self):
        return _ValuesView(self)

    def __eq__(self, other):
        if not _is_mapping(other):
            return NotImplemented
        return dict(self.items()) == dict(other.items())

    __class_getitem__ = classmethod(_GenericAlias)


class _MutableMapping(_Mapping):
    # The collections.abc.MutableMapping mixin methods.
    __slots__ = ()
    __marker = object()

    def pop(self, key, default=__marker):
        try:
            value = self[key]
        except KeyError:
            if default is self.__marker:
                raise
            return default
        else:
            del self[key]
            return value

    def popitem(self):
        try:
            key = next(iter(self))
        except StopIteration:
            raise KeyError from None
        value = self[key]
        del self[key]
        return key, value

    def clear(self):
        try:
            while True:
                self.popitem()
        except KeyError:
            pass

    def update(self, other=(), /, **kwds):
        if _is_mapping(other):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, "keys"):
            for key in other.keys():
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        for key, value in kwds.items():
            self[key] = value

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default


class _Sequence:
    # The collections.abc.Sequence mixin methods.
    __slots__ = ()

    def __iter__(self):
        i = 0
        try:
            while True:
                v = self[i]
                yield v
                i += 1
        except IndexError:
            return

    def __contains__(self, value):
        for v in self:
            if v is value or v == value:
                return True
        return False

    def __reversed__(self):
        for i in reversed(range(len(self))):
            yield self[i]

    def index(self, value, start=0, stop=None):
        if start is not None and start < 0:
            start = max(len(self) + start, 0)
        if stop is not None and stop < 0:
            stop += len(self)
        i = start
        while stop is None or i < stop:
            try:
                v = self[i]
            except IndexError:
                break
            if v is value or v == value:
                return i
            i += 1
        raise ValueError

    def count(self, value):
        return sum(1 for v in self if v is value or v == value)

    __class_getitem__ = classmethod(_GenericAlias)


class _MutableSequence(_Sequence):
    # The collections.abc.MutableSequence mixin methods.
    __slots__ = ()

    def append(self, value):
        self.insert(len(self), value)

    def clear(self):
        try:
            while True:
                self.pop()
        except IndexError:
            pass

    def reverse(self):
        n = len(self)
        for i in range(n//2):
            self[i], self[n-i-1] = self[n-i-1], self[i]

    def extend(self, values):
        if values is self:
            values = list(values)
        for v in values:
            self.append(v)

    def pop(self, index=-1):
        v = self[index]
        del self[index]
        return v

    def remove(self, value):
        del self[self.index(value)]

    def __iadd__(self, values):
        self.extend(values)
        return self


################################################################################
### deque
################################################################################

class deque:
    '''A list-like sequence optimized for data accesses near its endpoints.'''

    # Items live in self._items[self._head:]; free space at the front makes
    # appendleft and popleft amortized constant time. Every mutation bumps
    # self._state so that iterators detect it, as CPython's deque does.

    def __new__(cls, /, *args, **kwargs):
        self = object.__new__(cls)
        object.__setattr__(self, '_items', [])
        object.__setattr__(self, '_head', 0)
        object.__setattr__(self, '_maxlen', None)
        object.__setattr__(self, '_state', 0)
        return self

    def __init__(self, iterable=(), maxlen=None):
        if maxlen is not None:
            if not isinstance(maxlen, int):
                raise TypeError('an integer is required')
            if maxlen < 0:
                raise ValueError('maxlen must be non-negative')
        object.__setattr__(self, '_maxlen', maxlen)
        if len(self):
            self.clear()
        if iterable is not None:
            self.extend(iterable)

    @property
    def maxlen(self):
        '''maximum size of a deque or None if unbounded'''
        return self._maxlen

    def __setattr__(self, name, value):
        if name == 'maxlen':
            raise AttributeError("attribute 'maxlen' of 'collections.deque' objects is not writable")
        object.__setattr__(self, name, value)

    def _mutated(self):
        object.__setattr__(self, '_state', self._state + 1)

    def _compact(self):
        if self._head > 16 and self._head * 2 > len(self._items):
            del self._items[:self._head]
            object.__setattr__(self, '_head', 0)

    def __len__(self):
        return len(self._items) - self._head

    def __bool__(self):
        return len(self._items) > self._head

    def append(self, x, /):
        '''Add an element to the right side of the deque.'''
        self._items.append(x)
        self._mutated()
        if self._maxlen is not None and len(self) > self._maxlen:
            self.popleft()

    def appendleft(self, x, /):
        '''Add an element to the left side of the deque.'''
        if not self._head:
            spare = max(8, len(self))
            object.__setattr__(self, '_items', [None] * spare + self._items)
            object.__setattr__(self, '_head', spare)
        head = self._head - 1
        self._items[head] = x
        object.__setattr__(self, '_head', head)
        self._mutated()
        if self._maxlen is not None and len(self) > self._maxlen:
            self.pop()

    def pop(self, /):
        '''Remove and return the rightmost element.'''
        if not self:
            raise IndexError('pop from an empty deque')
        self._mutated()
        return self._items.pop()

    def popleft(self, /):
        '''Remove and return the leftmost element.'''
        if not self:
            raise IndexError('pop from an empty deque')
        head = self._head
        x = self._items[head]
        self._items[head] = None
        object.__setattr__(self, '_head', head + 1)
        self._mutated()
        self._compact()
        return x

    def extend(self, iterable, /):
        '''Extend the right side of the deque with elements from the iterable.'''
        if iterable is self:
            iterable = list(iterable)
        for x in iterable:
            self.append(x)

    def extendleft(self, iterable, /):
        '''Extend the left side of the deque with elements from the iterable.'''
        if iterable is self:
            iterable = list(iterable)
        for x in iterable:
            self.appendleft(x)

    def clear(self, /):
        '''Remove all elements from the deque.'''
        object.__setattr__(self, '_items', [])
        object.__setattr__(self, '_head', 0)
        self._mutated()

    def copy(self, /):
        '''Return a shallow copy of a deque.'''
        if type(self) is deque:
            return deque(self, self._maxlen)
        if self._maxlen is None:
            return type(self)(self)
        return type(self)(self, self._maxlen)

    __copy__ = copy

    def count(self, value, /):
        '''Return number of occurrences of value.'''
        state = self._state
        n = 0
        for i in range(self._head, len(self._items)):
            item = self._items[i]
            if item is value or item == value:
                n += 1
            if state != self._state:
                raise RuntimeError('deque mutated during iteration')
        return n

    def index(self, value, start=0, stop=_sys.maxsize, /):
        '''Return first index of value.

        Raises ValueError if the value is not present.'''
        n = len(self)
        start, stop = slice(start, stop).indices(n)[:2]
        state = self._state
        for i in range(start, stop):
            item = self._items[self._head + i]
            if item is value or item == value:
                return i
            if state != self._state:
                raise RuntimeError('deque mutated during iteration')
        raise ValueError('deque.index(x): x not in deque')

    def insert(self, index, value, /):
        '''Insert value before index.'''
        if self._maxlen is not None and len(self) >= self._maxlen:
            raise IndexError('deque already at its maximum size')
        n = len(self)
        index = index.__index__()
        if index < 0:
            index = max(n + index, 0)
        index = min(index, n)
        self._items.insert(self._head + index, value)
        self._mutated()

    def remove(self, value, /):
        '''Remove first occurrence of value.'''
        state = self._state
        for i in range(self._head, len(self._items)):
            item = self._items[i]
            equal = item is value or item == value
            if state != self._state:
                raise IndexError('deque mutated during remove().')
            if equal:
                del self._items[i]
                self._mutated()
                return
        raise ValueError('deque.remove(x): x not in deque')

    def reverse(self, /):
        '''Reverse *IN PLACE*.'''
        items = self._items[self._head:]
        items.reverse()
        object.__setattr__(self, '_items', items)
        object.__setattr__(self, '_head', 0)
        self._mutated()

    def rotate(self, n=1, /):
        '''Rotate the deque n steps to the right (default n=1).  If n is negative, rotates left.'''
        size = len(self)
        if size <= 1:
            return
        n = n.__index__() % size
        if n:
            items = self._items[self._head:]
            object.__setattr__(self, '_items', items[-n:] + items[:-n])
            object.__setattr__(self, '_head', 0)
            self._mutated()

    def _index(self, index):
        if not hasattr(type(index), '__index__'):
            raise TypeError(f"sequence index must be integer, not '{type(index).__name__}'")
        index = index.__index__()
        n = len(self)
        if index < 0:
            index += n
        if not 0 <= index < n:
            raise IndexError('deque index out of range')
        return self._head + index

    def __getitem__(self, index, /):
        return self._items[self._index(index)]

    def __setitem__(self, index, value, /):
        self._items[self._index(index)] = value

    def __delitem__(self, index, /):
        del self._items[self._index(index)]
        self._mutated()

    def __contains__(self, value, /):
        state = self._state
        for i in range(self._head, len(self._items)):
            item = self._items[i]
            equal = item is value or item == value
            if state != self._state:
                raise RuntimeError('deque mutated during iteration')
            if equal:
                return True
        return False

    def __iter__(self):
        return _deque_iterator(self, False)

    def __reversed__(self):
        '''Return a reverse iterator over the deque.'''
        return _deque_iterator(self, True)

    @_recursive_repr('[...]')
    def _repr_items(self):
        return repr(list(self))

    def __repr__(self):
        items = self._repr_items()
        if self._maxlen is not None:
            return f'{type(self).__name__}({items}, maxlen={self._maxlen})'
        return f'{type(self).__name__}({items})'

    __hash__ = None

    def _compare(self, other, op):
        if not isinstance(other, deque):
            return NotImplemented
        return op(list(self), list(other))

    def __eq__(self, other):
        return self._compare(other, lambda a, b: a == b)

    def __ne__(self, other):
        return self._compare(other, lambda a, b: a != b)

    def __lt__(self, other):
        return self._compare(other, lambda a, b: a < b)

    def __le__(self, other):
        return self._compare(other, lambda a, b: a <= b)

    def __gt__(self, other):
        return self._compare(other, lambda a, b: a > b)

    def __ge__(self, other):
        return self._compare(other, lambda a, b: a >= b)

    def __add__(self, other, /):
        if not isinstance(other, deque):
            raise TypeError(f'can only concatenate deque (not "{type(other).__name__}") to deque')
        new = self.copy()
        new.extend(other)
        return new

    def __iadd__(self, other, /):
        self.extend(other)
        return self

    def __mul__(self, n, /):
        new = self.copy()
        new *= n
        return new

    __rmul__ = __mul__

    def __imul__(self, n, /):
        n = n.__index__()
        if n <= 0:
            self.clear()
        elif n > 1:
            items = list(self)
            for _ in range(n - 1):
                self.extend(items)
        return self

    def __reduce__(self):
        state = getattr(self, '__getstate__', None)
        state = state() if state is not None else None
        if isinstance(state, dict):
            state = {k: v for k, v in state.items() if k not in ('_items', '_head', '_maxlen', '_state')} or None
        if self._maxlen is None:
            return type(self), (), state, iter(self)
        return type(self), ((), self._maxlen), state, iter(self)

    __class_getitem__ = classmethod(_GenericAlias)


class _deque_iterator:
    __slots__ = ('_deque', '_index', '_state', '_reverse')

    def __init__(self, d, reverse):
        self._deque = d
        self._state = d._state
        self._reverse = reverse
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        d = self._deque
        if d is None:
            raise StopIteration
        if self._state != d._state:
            self._deque = None
            raise RuntimeError('deque mutated during iteration')
        n = len(d)
        if self._index >= n:
            self._deque = None
            raise StopIteration
        i = n - 1 - self._index if self._reverse else self._index
        self._index += 1
        return d._items[d._head + i]

    def __length_hint__(self):
        d = self._deque
        return 0 if d is None else len(d) - self._index


################################################################################
### defaultdict
################################################################################

class defaultdict(dict):
    '''defaultdict(default_factory=None, /, [...]) --> dict with default factory

The default factory is called without arguments to produce
a new value when a key is not present, in __getitem__ only.
A defaultdict compares equal to a dict with the same items.
All remaining arguments are treated the same as if they were
passed to the dict constructor, including keyword arguments.
'''
    __slots__ = ('default_factory',)

    def __init__(self, default_factory=None, /, *args, **kwargs):
        if default_factory is not None and not callable(default_factory):
            raise TypeError('first argument must be callable or None')
        self.default_factory = default_factory
        dict.__init__(self, *args, **kwargs)

    def __missing__(self, key, /):
        '''__missing__(key) # Called by __getitem__ for missing key; pseudo-code:
  if self.default_factory is None: raise KeyError((key,))
  self[key] = value = self.default_factory()
  return value
'''
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    @_recursive_repr()
    def _repr_factory(self):
        return repr(self.default_factory)

    def __repr__(self):
        factory = 'None' if self.default_factory is None else self._repr_factory()
        return f'{type(self).__name__}({factory}, {dict.__repr__(self)})'

    def copy(self, /):
        '''D.copy() -> a shallow copy of D.'''
        return type(self)(self.default_factory, self)

    __copy__ = copy

    def __reduce__(self):
        args = () if self.default_factory is None else (self.default_factory,)
        return type(self), args, None, None, iter(self.items())

    def __or__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = self.copy()
        new.update(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = type(self)(self.default_factory, other)
        new.update(self)
        return new

    __class_getitem__ = classmethod(_GenericAlias)


################################################################################
### OrderedDict
################################################################################

class OrderedDict(dict):
    'Dictionary that remembers insertion order'
    # The inherited dict keeps insertion order; the order-aware methods
    # rearrange it as CPython's C OrderedDict does.

    def __init__(self, other=(), /, **kwds):
        '''Initialize an ordered dictionary.  The signature is the same as
        regular dictionaries.  Keyword argument order is preserved.
        '''
        self.update(other, **kwds)

    update = _MutableMapping.update

    def popitem(self, last=True):
        '''Remove and return a (key, value) pair from the dictionary.

        Pairs are returned in LIFO order if last is true or FIFO order if false.
        '''
        if not self:
            raise KeyError('dictionary is empty')
        key = next(reversed(self)) if last else next(iter(self))
        value = dict.pop(self, key)
        return key, value

    def move_to_end(self, key, last=True):
        '''Move an existing element to the end (or beginning if last is false).

        Raise KeyError if the element does not exist.
        '''
        value = dict.pop(self, key)
        if last:
            dict.__setitem__(self, key, value)
        else:
            rest = list(dict.items(self))
            dict.clear(self)
            dict.__setitem__(self, key, value)
            for k, v in rest:
                dict.__setitem__(self, k, v)

    __marker = object()

    def pop(self, key, default=__marker):
        '''od.pop(k[,d]) -> v, remove specified key and return the corresponding
        value.  If key is not found, d is returned if given, otherwise KeyError
        is raised.
        '''
        if default is self.__marker:
            return dict.pop(self, key)
        return dict.pop(self, key, default)

    def setdefault(self, key, default=None):
        '''Insert key with a value of default if key is not in the dictionary.

        Return the value for key if key is in the dictionary, else default.
        '''
        if key in self:
            return self[key]
        self[key] = default
        return default

    @_recursive_repr()
    def __repr__(self):
        'od.__repr__() <==> repr(od)'
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))

    def __reduce__(self):
        'Return state information for pickling'
        state = getattr(self, '__getstate__', None)
        state = state() if state is not None else None
        return self.__class__, (), state or None, None, iter(self.items())

    def copy(self):
        'od.copy() -> a shallow copy of od'
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        '''Create a new ordered dictionary with keys from iterable and values set to value.
        '''
        self = cls()
        for key in iterable:
            self[key] = value
        return self

    def __eq__(self, other):
        '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.

        '''
        if isinstance(other, OrderedDict):
            return dict.__eq__(self, other) and all(map(_eq, self, other))
        return dict.__eq__(self, other)

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = self.__class__(self)
        new.update(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = self.__class__(other)
        new.update(self)
        return new


################################################################################
### namedtuple
################################################################################

def _tuplegetter(index, doc):
    return property(_itemgetter(index), doc=doc)


def namedtuple(typename, field_names, *, rename=False, defaults=None, module=None):
    """Returns a new subclass of tuple with named fields.

    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> Point.__doc__                   # docstring for the new class
    'Point(x, y)'
    >>> p = Point(11, y=22)             # instantiate with positional args or keywords
    >>> p[0] + p[1]                     # indexable like a plain tuple
    33
    >>> x, y = p                        # unpack like a regular tuple
    >>> x, y
    (11, 22)
    >>> p.x + p.y                       # fields also accessible by name
    33
    >>> d = p._asdict()                 # convert to a dictionary
    >>> d['x']
    11
    >>> Point(**d)                      # convert from a dictionary
    Point(x=11, y=22)
    >>> p._replace(x=100)               # _replace() is like str.replace() but targets named fields
    Point(x=100, y=22)

    """

    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = _sys.intern(str(typename))

    if rename:
        seen = set()
        for index, name in enumerate(field_names):
            if (not name.isidentifier()
                or _iskeyword(name)
                or name.startswith('_')
                or name in seen):
                field_names[index] = f'_{index}'
            seen.add(name)

    for name in [typename] + field_names:
        if type(name) is not str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid '
                             f'identifiers: {name!r}')
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             f'keyword: {name!r}')

    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             f'{name!r}')
        if name in seen:
            raise ValueError(f'Encountered duplicate field name: {name!r}')
        seen.add(name)

    field_defaults = {}
    if defaults is not None:
        defaults = tuple(defaults)
        if len(defaults) > len(field_names):
            raise TypeError('Got more default values than field names')
        field_defaults = dict(reversed(list(zip(reversed(field_names),
                                                reversed(defaults)))))

    # Variables used in the methods and docstrings
    field_names = tuple(map(_sys.intern, field_names))
    num_fields = len(field_names)
    arg_list = ', '.join(field_names)
    if num_fields == 1:
        arg_list += ','
    repr_fmt = '(' + ', '.join(f'{name}=%r' for name in field_names) + ')'
    tuple_new = tuple.__new__
    _dict, _tuple, _len, _map, _zip = dict, tuple, len, map, zip

    # Create all the named tuple methods to be added to the class namespace

    namespace = {
        '_tuple_new': tuple_new,
        '__builtins__': {},
        '__name__': f'namedtuple_{typename}',
    }
    code = f'lambda _cls, {arg_list}: _tuple_new(_cls, ({arg_list}))'
    __new__ = eval(code, namespace)
    __new__.__name__ = '__new__'
    __new__.__doc__ = f'Create new instance of {typename}({arg_list})'
    if defaults is not None:
        __new__.__defaults__ = defaults

    @classmethod
    def _make(cls, iterable):
        result = tuple_new(cls, iterable)
        if _len(result) != num_fields:
            raise TypeError(f'Expected {num_fields} arguments, got {len(result)}')
        return result

    _make.__func__.__doc__ = (f'Make a new {typename} object from a sequence '
                              'or iterable')

    def _replace(self, /, **kwds):
        result = self._make(_map(kwds.pop, field_names, self))
        if kwds:
            raise TypeError(f'Got unexpected field names: {list(kwds)!r}')
        return result

    _replace.__doc__ = (f'Return a new {typename} object replacing specified '
                        'fields with new values')

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + repr_fmt % self

    def _asdict(self):
        'Return a new dict which maps field names to their values.'
        return _dict(_zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return _tuple(self)

    # Modify function metadata to help with introspection and debugging
    for method in (
        __new__,
        _make.__func__,
        _replace,
        __repr__,
        _asdict,
        __getnewargs__,
    ):
        method.__qualname__ = f'{typename}.{method.__name__}'

    # Build-up the class namespace dictionary
    # and use type() to build the result class
    class_namespace = {
        '__doc__': f'{typename}({arg_list})',
        '__slots__': (),
        '_fields': field_names,
        '_field_defaults': field_defaults,
        '__new__': __new__,
        '_make': _make,
        '__replace__': _replace,
        '_replace': _replace,
        '__repr__': __repr__,
        '_asdict': _asdict,
        '__getnewargs__': __getnewargs__,
        '__match_args__': field_names,
    }
    for index, name in enumerate(field_names):
        doc = _sys.intern(f'Alias for field number {index}')
        class_namespace[name] = _tuplegetter(index, doc)

    result = type(typename, (tuple,), class_namespace)

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython), or where the user has
    # specified a particular module.
    if module is None:
        try:
            module = _sys._getframemodulename(1) or '__main__'
        except AttributeError:
            try:
                module = _sys._getframe(1).f_globals.get('__name__', '__main__')
            except (AttributeError, ValueError):
                pass
    if module is not None:
        result.__module__ = module

    return result


########################################################################
###  Counter
########################################################################

def _count_elements(mapping, iterable):
    'Tally elements from the iterable.'
    mapping_get = mapping.get
    for elem in iterable:
        mapping[elem] = mapping_get(elem, 0) + 1

class Counter(dict):
    '''Dict subclass for counting hashable items.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    When constructed from a Mapping or Counter, the original object's
    values will be used as the initial counts.

    >>> c = Counter('abcdeabcdabcaba')  # count elements from a string

    >>> c.most_common(3)                # three most common elements
    [('a', 5), ('b', 4), ('c', 3)]
    >>> sorted(c)                       # list all unique elements
    ['a', 'b', 'c', 'd', 'e']
    >>> ''.join(sorted(c.elements()))   # list elements with repetitions
    'aaaaabbbbcccdde'
    >>> sum(c.values())                 # total of all counts
    15

    >>> c['a']                          # count of letter 'a'
    5
    >>> for elem in 'shazam':           # update counts from an iterable
    ...     c[elem] += 1                # by adding 1 to each element's count
    >>> c['a']                          # now there are seven 'a'
    7
    >>> del c['b']                      # remove all 'b'
    >>> c['b']                          # now there are zero 'b'
    0

    >>> d = Counter('simsalabim')       # make another counter
    >>> c.update(d)                     # add in the second counter
    >>> c['a']                          # now there are nine 'a'
    9

    >>> c.clear()                       # empty the counter
    >>> c
    Counter()

    Note:  If a count is set to zero or reduced to zero, it will remain
    in the counter until the entry is deleted or the counter is cleared:

    >>> c = Counter('aaabbc')
    >>> c['b'] -= 2                     # reduce the count of 'b' by two
    >>> c.most_common()                 # 'b' is still in, but its count is zero
    [('a', 3), ('c', 1), ('b', 0)]

    '''
    # References:
    #   http://en.wikipedia.org/wiki/Multiset
    #   http://www.gnu.org/software/smalltalk/manual-base/html_node/Bag.html
    #   http://www.java2s.com/Tutorial/Cpp/0380__set-multiset/Catalog0380__set-multiset.htm
    #   http://code.activestate.com/recipes/259174/
    #   Knuth, TAOCP Vol. II section 4.6.3

    def __init__(self, iterable=None, /, **kwds):
        '''Create a new, empty Counter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = Counter()                           # a new, empty counter
        >>> c = Counter('gallahad')                 # a new counter from an iterable
        >>> c = Counter({'a': 4, 'b': 2})           # a new counter from a mapping
        >>> c = Counter(a=4, b=2)                   # a new counter from keyword args

        '''
        super().__init__()
        self.update(iterable, **kwds)

    def __missing__(self, key):
        'The count of elements not in the Counter is zero.'
        # Needed so that self[missing_item] does not raise KeyError
        return 0

    def total(self):
        'Sum of the counts'
        return sum(self.values())

    def most_common(self, n=None):
        '''List the n most common elements and their counts from the most
        common to the least.  If n is None, then list all element counts.

        >>> Counter('abracadabra').most_common(3)
        [('a', 5), ('b', 2), ('r', 2)]

        '''
        # Emulate Bag.sortedByCount from Smalltalk
        if n is None:
            return sorted(self.items(), key=_itemgetter(1), reverse=True)

        return _nlargest(n, self.items(), key=_itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each as many times as its count.

        >>> c = Counter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        Knuth's example for prime factors of 1836:  2**2 * 3**3 * 17**1

        >>> import math
        >>> prime_factors = Counter({2: 2, 3: 3, 17: 1})
        >>> math.prod(prime_factors.elements())
        1836

        Note, if an element's count has been set to zero or is a negative
        number, elements() will ignore it.

        '''
        # Emulate Bag.do from Smalltalk and Multiset.begin from C++.
        return _chain.from_iterable(_starmap(_repeat, self.items()))

    # Override dict methods where necessary

    @classmethod
    def fromkeys(cls, iterable, v=None):
        # There is no equivalent method for counters because the semantics
        # would be ambiguous in cases such as Counter.fromkeys('aaabbc', v=2).
        # Initializing counters to zero values isn't necessary because zero
        # is already the default value for counter lookups.  Initializing
        # to one is easily accomplished with Counter(set(iterable)).  For
        # more exotic cases, create a dictionary first using a dictionary
        # comprehension or dict.fromkeys().
        raise NotImplementedError(
            'Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

    def update(self, iterable=None, /, **kwds):
        '''Like dict.update() but add counts instead of replacing them.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = Counter('which')
        >>> c.update('witch')           # add elements from another iterable
        >>> d = Counter('watch')
        >>> c.update(d)                 # add elements from another counter
        >>> c['h']                      # four 'h' in which, witch, and watch
        4

        '''
        # The regular dict.update() operation makes no sense here because the
        # replace behavior results in some of the original untouched counts
        # being mixed-in with all of the other counts for a mismash that
        # doesn't have a straight-forward interpretation in most counting
        # contexts.  Instead, we implement straight-addition.  Both the inputs
        # and outputs are allowed to contain zero and negative counts.

        if iterable is not None:
            if _is_mapping(iterable):
                if self:
                    self_get = self.get
                    for elem, count in iterable.items():
                        self[elem] = count + self_get(elem, 0)
                else:
                    # fast path when counter is empty
                    super().update(iterable)
            else:
                _count_elements(self, iterable)
        if kwds:
            self.update(kwds)

    def subtract(self, iterable=None, /, **kwds):
        '''Like dict.update() but subtracts counts instead of replacing them.
        Counts can be reduced below zero.  Both the inputs and outputs are
        allowed to contain zero and negative counts.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = Counter('which')
        >>> c.subtract('witch')             # subtract elements from another iterable
        >>> c.subtract(Counter('watch'))    # subtract elements from another counter
        >>> c['h']                          # 2 in which, minus 1 in witch, minus 1 in watch
        0
        >>> c['w']                          # 1 in which, minus 1 in witch, minus 1 in watch
        -1

        '''
        if iterable is not None:
            self_get = self.get
            if _is_mapping(iterable):
                for elem, count in iterable.items():
                    self[elem] = self_get(elem, 0) - count
            else:
                for elem in iterable:
                    self[elem] = self_get(elem, 0) - 1
        if kwds:
            self.subtract(kwds)

    def copy(self):
        'Return a shallow copy.'
        return self.__class__(self)

    def __reduce__(self):
        return self.__class__, (dict(self),)

    def __delitem__(self, elem):
        'Like dict.__delitem__() but does not raise KeyError for missing values.'
        if elem in self:
            super().__delitem__(elem)

    def __repr__(self):
        if not self:
            return f'{self.__class__.__name__}()'
        try:
            # dict() preserves the ordering returned by most_common()
            d = dict(self.most_common())
        except TypeError:
            # handle case where values are not orderable
            d = dict(self)
        return f'{self.__class__.__name__}({d!r})'

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       and at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative and zero counts, add-in an empty counter:
    #       c += Counter()
    #
    # Results are ordered according to when an element is first
    # encountered in the left operand and then by the order
    # encountered in the right operand.
    #
    # When the multiplicities are all zero or one, multiset operations
    # are guaranteed to be equivalent to the corresponding operations
    # for regular sets.
    #
    #     Given counter multisets such as:
    #         cp = Counter(a=1, b=0, c=1)
    #         cq = Counter(c=1, d=0, e=1)
    #
    #     The corresponding regular sets would be:
    #         sp = {'a', 'c'}
    #         sq = {'c', 'e'}
    #
    #     All of the following relations would hold:
    #         (cp == cq) == (sp == sq)
    #         (cp != cq) == (sp != sq)
    #         (cp <= cq) == (sp <= sq)
    #         (cp < cq) == (sp < sq)
    #         (cp >= cq) == (sp >= sq)
    #         (cp > cq) == (sp > sq)
    #         set(cp + cq) == sp | sq
    #         set(cp - cq) == sp - sq
    #         set(cp | cq) == sp | sq
    #         set(cp & cq) == sp & sq
    #         set(cp ^ cq) == sp ^ sq

    def __eq__(self, other):
        'True if all counts agree. Missing counts are treated as zero.'
        if not isinstance(other, Counter):
            return NotImplemented
        return all(self[e] == other[e] for c in (self, other) for e in c)

    def __ne__(self, other):
        'True if any counts disagree. Missing counts are treated as zero.'
        if not isinstance(other, Counter):
            return NotImplemented
        return not self == other

    def __le__(self, other):
        'True if all counts in self are a subset of those in other.'
        if not isinstance(other, Counter):
            return NotImplemented
        return all(self[e] <= other[e] for c in (self, other) for e in c)

    def __lt__(self, other):
        'True if all counts in self are a proper subset of those in other.'
        if not isinstance(other, Counter):
            return NotImplemented
        return self <= other and self != other

    def __ge__(self, other):
        'True if all counts in self are a superset of those in other.'
        if not isinstance(other, Counter):
            return NotImplemented
        return all(self[e] >= other[e] for c in (self, other) for e in c)

    def __gt__(self, other):
        'True if all counts in self are a proper superset of those in other.'
        if not isinstance(other, Counter):
            return NotImplemented
        return self >= other and self != other

    def __add__(self, other):
        '''Add counts from two counters.

        >>> Counter('abbb') + Counter('bcc')
        Counter({'b': 4, 'c': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            newcount = count + other[elem]
            if newcount > 0:
                result[elem] = newcount
        for elem, count in other.items():
            if elem not in self and count > 0:
                result[elem] = count
        return result

    def __sub__(self, other):
        ''' Subtract count, but keep only results with positive counts.

        >>> Counter('abbbc') - Counter('bccd')
        Counter({'b': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            newcount = count - other[elem]
            if newcount > 0:
                result[elem] = newcount
        for elem, count in other.items():
            if elem not in self and count < 0:
                result[elem] = 0 - count
        return result

    def __or__(self, other):
        '''Union is the maximum of value in either of the input counters.

        >>> Counter('abbb') | Counter('bcc')
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            other_count = other[elem]
            newcount = other_count if count < other_count else count
            if newcount > 0:
                result[elem] = newcount
        for elem, count in other.items():
            if elem not in self and count > 0:
                result[elem] = count
        return result

    def __and__(self, other):
        ''' Intersection is the minimum of corresponding counts.

        >>> Counter('abbb') & Counter('bcc')
        Counter({'b': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            other_count = other[elem]
            newcount = count if count < other_count else other_count
            if newcount > 0:
                result[elem] = newcount
        return result

    def __xor__(self, other):
        '''Symmetric difference. Absolute value of count differences.

        The symmetric difference p ^ q is equivalent to:

            (p - q) | (q - p).

        For each element, symmetric difference gives the same result as:

            max(p[elem], q[elem]) - min(p[elem], q[elem])

        >>> Counter(a=5, b=3, c=2, d=2) ^ Counter(a=1, b=3, c=5, e=1)
        Counter({'a': 4, 'c': 3, 'd': 2, 'e': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            newcount = abs(count - other[elem])
            if newcount:
                result[elem] = newcount
        for elem, count in other.items():
            if elem not in self and count:
                result[elem] = abs(count)
        return result

    def __pos__(self):
        'Adds an empty counter, effectively stripping negative and zero counts'
        result = Counter()
        for elem, count in self.items():
            if count > 0:
                result[elem] = count
        return result

    def __neg__(self):
        '''Subtracts from an empty counter.  Strips positive and zero counts,
        and flips the sign on negative counts.

        '''
        result = Counter()
        for elem, count in self.items():
            if count < 0:
                result[elem] = 0 - count
        return result

    def _keep_positive(self):
        '''Internal method to strip elements with a negative or zero count'''
        nonpositive = [elem for elem, count in self.items() if not count > 0]
        for elem in nonpositive:
            del self[elem]
        return self

    def __iadd__(self, other):
        '''Inplace add from another counter, keeping only positive counts.

        >>> c = Counter('abbb')
        >>> c += Counter('bcc')
        >>> c
        Counter({'b': 4, 'c': 2, 'a': 1})

        '''
        for elem, count in other.items():
            self[elem] += count
        return self._keep_positive()

    def __isub__(self, other):
        '''Inplace subtract counter, but keep only results with positive counts.

        >>> c = Counter('abbbc')
        >>> c -= Counter('bccd')
        >>> c
        Counter({'b': 2, 'a': 1})

        '''
        for elem, count in other.items():
            self[elem] -= count
        return self._keep_positive()

    def __ior__(self, other):
        '''Inplace union is the maximum of value from either counter.

        >>> c = Counter('abbb')
        >>> c |= Counter('bcc')
        >>> c
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        for elem, other_count in other.items():
            count = self[elem]
            if other_count > count:
                self[elem] = other_count
        return self._keep_positive()

    def __iand__(self, other):
        '''Inplace intersection is the minimum of corresponding counts.

        >>> c = Counter('abbb')
        >>> c &= Counter('bcc')
        >>> c
        Counter({'b': 1})

        '''
        for elem, count in self.items():
            other_count = other[elem]
            if other_count < count:
                self[elem] = other_count
        return self._keep_positive()

    def __ixor__(self, other):
        '''Inplace symmetric difference. Absolute value of count differences.

        >>> c = Counter(a=5, b=3, c=2, d=2)
        >>> c ^= Counter(a=1, b=3, c=5, e=1)
        >>> c
        Counter({'a': 4, 'c': 3, 'd': 2, 'e': 1})

        '''
        for elem, count in self.items():
            self[elem] = abs(count - other[elem])
        for elem, count in other.items():
            if elem not in self:
                self[elem] = abs(count)
        return self._keep_positive()


########################################################################
###  ChainMap
########################################################################

class ChainMap(_MutableMapping):
    ''' A ChainMap groups multiple dicts (or other mappings) together
    to create a single, updateable view.

    The underlying mappings are stored in a list.  That list is public and can
    be accessed or updated using the *maps* attribute.  There is no other
    state.

    Lookups search the underlying mappings successively until a key is found.
    In contrast, writes, updates, and deletions only operate on the first
    mapping.

    '''

    def __init__(self, *maps):
        '''Initialize a ChainMap by setting *maps* to the given mappings.
        If no mappings are provided, a single empty dictionary is used.

        '''
        self.maps = list(maps) or [{}]          # always at least one map

    def __missing__(self, key):
        raise KeyError(key)

    def __getitem__(self, key):
        for mapping in self.maps:
            try:
                return mapping[key]             # can't use 'key in mapping' with defaultdict
            except KeyError:
                pass
        return self.__missing__(key)            # support subclasses that define __missing__

    def get(self, key, default=None):
        return self[key] if key in self else default    # needs to make use of __contains__

    def __len__(self):
        return len(set().union(*self.maps))     # reuses stored hash values if possible

    def __iter__(self):
        d = {}
        for mapping in map(dict.fromkeys, reversed(self.maps)):
            d |= mapping                        # reuses stored hash values if possible
        return iter(d)

    def __contains__(self, key):
        for mapping in self.maps:
            if key in mapping:
                return True
        return False

    def __bool__(self):
        return any(self.maps)

    @_recursive_repr()
    def __repr__(self):
        return f'{self.__class__.__name__}({", ".join(map(repr, self.maps))})'

    @classmethod
    def fromkeys(cls, iterable, value=None, /):
        'Create a new ChainMap with keys from iterable and values set to value.'
        return cls(dict.fromkeys(iterable, value))

    def copy(self):
        'New ChainMap or subclass with a new copy of maps[0] and refs to maps[1:]'
        return self.__class__(self.maps[0].copy(), *self.maps[1:])

    __copy__ = copy

    def new_child(self, m=None, **kwargs):      # like Django's Context.push()
        '''New ChainMap with a new map followed by all previous maps.
        If no map is provided, an empty dict is used.
        Keyword arguments update the map or new empty dict.
        '''
        if m is None:
            m = kwargs
        elif kwargs:
            m.update(kwargs)
        return self.__class__(m, *self.maps)

    @property
    def parents(self):                          # like Django's Context.pop()
        'New ChainMap from maps[1:].'
        return self.__class__(*self.maps[1:])

    def __setitem__(self, key, value):
        self.maps[0][key] = value

    def __delitem__(self, key):
        try:
            del self.maps[0][key]
        except KeyError:
            raise KeyError(f'Key not found in the first mapping: {key!r}')

    def popitem(self):
        'Remove and return an item pair from maps[0]. Raise KeyError is maps[0] is empty.'
        try:
            return self.maps[0].popitem()
        except KeyError:
            raise KeyError('No keys found in the first mapping.')

    def pop(self, key, *args):
        'Remove *key* from maps[0] and return its value. Raise KeyError if *key* not in maps[0].'
        try:
            return self.maps[0].pop(key, *args)
        except KeyError:
            raise KeyError(f'Key not found in the first mapping: {key!r}')

    def clear(self):
        'Clear maps[0], leaving maps[1:] intact.'
        self.maps[0].clear()

    def __ior__(self, other):
        self.maps[0].update(other)
        return self

    def __or__(self, other):
        if not _is_mapping(other):
            return NotImplemented
        m = self.copy()
        m.maps[0].update(other)
        return m

    def __ror__(self, other):
        if not _is_mapping(other):
            return NotImplemented
        m = dict(other)
        for child in reversed(self.maps):
            m.update(child)
        return self.__class__(m)


################################################################################
### UserDict
################################################################################

class UserDict(_MutableMapping):

    # Start by filling-out the abstract methods
    def __init__(self, dict=None, /, **kwargs):
        self.data = {}
        if dict is not None:
            self.update(dict)
        if kwargs:
            self.update(kwargs)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __setitem__(self, key, item):
        self.data[key] = item

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    # Modify __contains__ and get() to work like dict
    # does when __missing__ is present.
    def __contains__(self, key):
        return key in self.data

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default


    # Now, add the methods in dicts but not in MutableMapping
    def __repr__(self):
        return repr(self.data)

    def __or__(self, other):
        if isinstance(other, UserDict):
            return self.__class__(self.data | other.data)
        if isinstance(other, dict):
            return self.__class__(self.data | other)
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, UserDict):
            return self.__class__(other.data | self.data)
        if isinstance(other, dict):
            return self.__class__(other | self.data)
        return NotImplemented

    def __ior__(self, other):
        if isinstance(other, UserDict):
            self.data |= other.data
        else:
            self.data |= other
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"].copy()
        return inst

    def copy(self):
        if self.__class__ is UserDict:
            return UserDict(self.data.copy())
        data = self.data
        try:
            self.data = {}
            c = _copy(self)
        finally:
            self.data = data
        c.update(self)
        return c


    # This method has a default implementation in MutableMapping, but dict's
    # equivalent is last-in, first-out instead of first-in, first-out.
    def popitem(self):
        """Remove and return a (key, value) pair as a 2-tuple.

        Removes pairs in the same order as the wrapped mapping's popitem()
        method. For dict objects (the default), that order is last-in,
        first-out (LIFO).
        Raises KeyError if the UserDict is empty.
        """
        return self.data.popitem()


    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d


################################################################################
### UserList
################################################################################

class UserList(_MutableSequence):
    """A more or less complete user-defined wrapper around list objects."""

    def __init__(self, initlist=None):
        self.data = []
        if initlist is not None:
            # XXX should this accept an arbitrary sequence?
            if type(initlist) == type(self.data):
                self.data[:] = initlist
            elif isinstance(initlist, UserList):
                self.data[:] = initlist.data[:]
            else:
                self.data = list(initlist)

    def __repr__(self):
        return repr(self.data)

    def __lt__(self, other):
        return self.data < self.__cast(other)

    def __le__(self, other):
        return self.data <= self.__cast(other)

    def __eq__(self, other):
        return self.data == self.__cast(other)

    def __gt__(self, other):
        return self.data > self.__cast(other)

    def __ge__(self, other):
        return self.data >= self.__cast(other)

    def __cast(self, other):
        return other.data if isinstance(other, UserList) else other

    def __contains__(self, item):
        return item in self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i])
        else:
            return self.data[i]

    def __setitem__(self, i, item):
        self.data[i] = item

    def __delitem__(self, i):
        del self.data[i]

    def __add__(self, other):
        if isinstance(other, UserList):
            return self.__class__(self.data + other.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data + other)
        return self.__class__(self.data + list(other))

    def __radd__(self, other):
        if isinstance(other, UserList):
            return self.__class__(other.data + self.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(other + self.data)
        return self.__class__(list(other) + self.data)

    def __iadd__(self, other):
        if isinstance(other, UserList):
            self.data += other.data
        elif isinstance(other, type(self.data)):
            self.data += other
        else:
            self.data += list(other)
        return self

    def __mul__(self, n):
        return self.__class__(self.data * n)

    __rmul__ = __mul__

    def __imul__(self, n):
        self.data *= n
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"][:]
        return inst

    def append(self, item):
        self.data.append(item)

    def insert(self, i, item):
        self.data.insert(i, item)

    def pop(self, i=-1):
        return self.data.pop(i)

    def remove(self, item):
        self.data.remove(item)

    def clear(self):
        self.data.clear()

    def copy(self):
        return self.__class__(self)

    def count(self, item):
        return self.data.count(item)

    def index(self, item, *args):
        return self.data.index(item, *args)

    def reverse(self):
        self.data.reverse()

    def sort(self, /, *args, **kwds):
        self.data.sort(*args, **kwds)

    def extend(self, other):
        if isinstance(other, UserList):
            self.data.extend(other.data)
        else:
            self.data.extend(other)


################################################################################
### UserString
################################################################################

class UserString(_Sequence):

    def __init__(self, seq):
        if isinstance(seq, str):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

    def __int__(self):
        return int(self.data)

    def __float__(self):
        return float(self.data)

    def __complex__(self):
        return complex(self.data)

    def __hash__(self):
        return hash(self.data)

    def __getnewargs__(self):
        return (self.data[:],)

    def __eq__(self, string):
        if isinstance(string, UserString):
            return self.data == string.data
        return self.data == string

    def __lt__(self, string):
        if isinstance(string, UserString):
            return self.data < string.data
        return self.data < string

    def __le__(self, string):
        if isinstance(string, UserString):
            return self.data <= string.data
        return self.data <= string

    def __gt__(self, string):
        if isinstance(string, UserString):
            return self.data > string.data
        return self.data > string

    def __ge__(self, string):
        if isinstance(string, UserString):
            return self.data >= string.data
        return self.data >= string

    def __contains__(self, char):
        if isinstance(char, UserString):
            char = char.data
        return char in self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.__class__(self.data[index])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, str):
            return self.__class__(self.data + other)
        return self.__class__(self.data + str(other))

    def __radd__(self, other):
        if isinstance(other, str):
            return self.__class__(other + self.data)
        return self.__class__(str(other) + self.data)

    def __mul__(self, n):
        return self.__class__(self.data * n)

    __rmul__ = __mul__

    def __mod__(self, args):
        return self.__class__(self.data % args)

    def __rmod__(self, template):
        return self.__class__(str(template) % self)

    # the following methods are defined in alphabetical order:
    def capitalize(self):
        return self.__class__(self.data.capitalize())

    def casefold(self):
        return self.__class__(self.data.casefold())

    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))

    def count(self, sub, start=0, end=_sys.maxsize):
        if isinstance(sub, UserString):
            sub = sub.data
        return self.data.count(sub, start, end)

    def removeprefix(self, prefix, /):
        if isinstance(prefix, UserString):
            prefix = prefix.data
        return self.__class__(self.data.removeprefix(prefix))

    def removesuffix(self, suffix, /):
        if isinstance(suffix, UserString):
            suffix = suffix.data
        return self.__class__(self.data.removesuffix(suffix))

    def encode(self, encoding='utf-8', errors='strict'):
        encoding = 'utf-8' if encoding is None else encoding
        errors = 'strict' if errors is None else errors
        return self.data.encode(encoding, errors)

    def endswith(self, suffix, start=0, end=_sys.maxsize):
        return self.data.endswith(suffix, start, end)

    def expandtabs(self, tabsize=8):
        return self.__class__(self.data.expandtabs(tabsize))

    def find(self, sub, start=0, end=_sys.maxsize):
        if isinstance(sub, UserString):
            sub = sub.data
        return self.data.find(sub, start, end)

    def format(self, /, *args, **kwds):
        return self.data.format(*args, **kwds)

    def format_map(self, mapping):
        return self.data.format_map(mapping)

    def index(self, sub, start=0, end=_sys.maxsize):
        if isinstance(sub, UserString):
            sub = sub.data
        return self.data.index(sub, start, end)

    def isalpha(self):
        return self.data.isalpha()

    def isalnum(self):
        return self.data.isalnum()

    def isascii(self):
        return self.data.isascii()

    def isdecimal(self):
        return self.data.isdecimal()

    def isdigit(self):
        return self.data.isdigit()

    def isidentifier(self):
        return self.data.isidentifier()

    def islower(self):
        return self.data.islower()

    def isnumeric(self):
        return self.data.isnumeric()

    def isprintable(self):
        return self.data.isprintable()

    def isspace(self):
        return self.data.isspace()

    def istitle(self):
        return self.data.istitle()

    def isupper(self):
        return self.data.isupper()

    def join(self, seq):
        return self.data.join(seq)

    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))

    def lower(self):
        return self.__class__(self.data.lower())

    def lstrip(self, chars=None):
        return self.__class__(self.data.lstrip(chars))

    maketrans = str.maketrans

    def partition(self, sep):
        return self.data.partition(sep)

    def replace(self, old, new, maxsplit=-1):
        if isinstance(old, UserString):
            old = old.data
        if isinstance(new, UserString):
            new = new.data
        return self.__class__(self.data.replace(old, new, maxsplit))

    def rfind(self, sub, start=0, end=_sys.maxsize):
        if isinstance(sub, UserString):
            sub = sub.data
        return self.data.rfind(sub, start, end)

    def rindex(self, sub, start=0, end=_sys.maxsize):
        if isinstance(sub, UserString):
            sub = sub.data
        return self.data.rindex(sub, start, end)

    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))

    def rpartition(self, sep):
        return self.data.rpartition(sep)

    def rstrip(self, chars=None):
        return self.__class__(self.data.rstrip(chars))

    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)

    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)

    def splitlines(self, keepends=False):
        return self.data.splitlines(keepends)

    def startswith(self, prefix, start=0, end=_sys.maxsize):
        return self.data.startswith(prefix, start, end)

    def strip(self, chars=None):
        return self.__class__(self.data.strip(chars))

    def swapcase(self):
        return self.__class__(self.data.swapcase())

    def title(self):
        return self.__class__(self.data.title())

    def translate(self, *args):
        return self.__class__(self.data.translate(*args))

    def upper(self):
        return self.__class__(self.data.upper())

    def zfill(self, width):
        return self.__class__(self.data.zfill(width))
